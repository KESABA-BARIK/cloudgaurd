"""
Ablation Studies Module

Compares different pattern mining and evaluation approaches to measure the impact
of design choices (thresholds, parameters, algorithms).

Variants:
1. Current Trie (optimized): min_support=3, min_conf=0.6, final_threshold=0.5
2. Loose Trie: min_support=1, min_conf=0.1, final_threshold=0.15
3. Simple Prefix: No pattern mining, just prefix matching
"""

from services.baseline_engine import Trie, evaluate_request
from collections import defaultdict, Counter
import numpy as np


def evaluate_request_with_rules(userId, resource, action, rules):
    """Helper: evaluate if request matches any rule."""
    for rule in rules:
        if rule['userId'] == userId and rule['action'] == action:
            # Check if resource matches pattern
            pattern = rule['resourcePattern']
            # Simple pattern matching: check if resource starts with pattern stem
            if pattern.endswith('*'):
                pattern_stem = pattern[:-1]
                if resource.startswith(pattern_stem):
                    return rule['confidence']
            elif resource == pattern:
                return rule['confidence']
    return 0.0


def mine_rules_current(logs):
    """Current Trie with optimized parameters (min_support=3, min_conf=0.6, threshold=0.5)."""
    grouped = defaultdict(list)
    
    # Only use logs with 'over-granted' label for mining
    over_granted_logs = [l for l in logs if l.get('label') == 'over-granted']
    
    for log in over_granted_logs:
        grouped[(log['userId'], log['action'])].append(log)
    
    rules = []
    
    for (uid, action), log_list in grouped.items():
        if len(log_list) < 1:
            continue
        
        trie = Trie()
        for log in log_list:
            trie.insert(log['resource'])
        
        patterns = trie.extract_patterns(
            len(log_list),
            min_support=3,      # Current: need at least 3 accesses
            min_conf=0.6        # Current: 60% confidence minimum
        )
        
        # Fallback: use most common resource
        if not patterns:
            resource_counts = Counter(log['resource'] for log in log_list)
            most_common = resource_counts.most_common(1)[0][0]
            patterns = [{"pattern": most_common, "confidence": 0.5, "support": len(log_list)}]
        
        for pattern in patterns:
            if pattern['confidence'] >= 0.5:  # Current threshold
                rules.append({
                    "userId": uid,
                    "action": action,
                    "resourcePattern": pattern['pattern'],
                    "support": pattern['support'],
                    "confidence": pattern['confidence']
                })
    
    return rules


def mine_rules_loose(logs):
    """Loose Trie with minimal parameters (min_support=1, min_conf=0.1, threshold=0.15)."""
    grouped = defaultdict(list)
    
    # Only use logs with 'over-granted' label for mining
    over_granted_logs = [l for l in logs if l.get('label') == 'over-granted']
    
    for log in over_granted_logs:
        grouped[(log['userId'], log['action'])].append(log)
    
    rules = []
    
    for (uid, action), log_list in grouped.items():
        if len(log_list) < 1:
            continue
        
        trie = Trie()
        for log in log_list:
            trie.insert(log['resource'])
        
        patterns = trie.extract_patterns(
            len(log_list),
            min_support=1,      # Loose: accept single occurrence
            min_conf=0.1        # Loose: 10% confidence minimum
        )
        
        # Fallback: use most common resource
        if not patterns:
            resource_counts = Counter(log['resource'] for log in log_list)
            most_common = resource_counts.most_common(1)[0][0]
            patterns = [{"pattern": most_common, "confidence": 0.5, "support": len(log_list)}]
        
        for pattern in patterns:
            if pattern['confidence'] >= 0.15:  # Loose threshold
                rules.append({
                    "userId": uid,
                    "action": action,
                    "resourcePattern": pattern['pattern'],
                    "support": pattern['support'],
                    "confidence": pattern['confidence']
                })
    
    return rules


def mine_rules_prefix(logs):
    """Simple prefix matching without pattern mining."""
    grouped = defaultdict(list)
    
    # Only use logs with 'over-granted' label for mining
    over_granted_logs = [l for l in logs if l.get('label') == 'over-granted']
    
    for log in over_granted_logs:
        grouped[(log['userId'], log['action'])].append(log)
    
    rules = []
    
    for (uid, action), log_list in grouped.items():
        if len(log_list) < 1:
            continue
        
        # Extract prefixes (first path segment) from resources
        prefixes = defaultdict(int)
        for log in log_list:
            resource = log['resource']
            prefix = resource.split('/')[0]
            prefixes[prefix] += 1
        
        # Create rules for prefixes with > 0 support
        for prefix, count in prefixes.items():
            rules.append({
                "userId": uid,
                "action": action,
                "resourcePattern": f"{prefix}/*",
                "support": count,
                "confidence": count / len(log_list)
            })
    
    return rules


def evaluate_with_threshold(logs, rules, threshold=0.5):
    """Evaluate logs against rules using confidence threshold."""
    tp = fp = fn = tn = 0
    
    for log in logs:
        if not log.get('label'):
            continue
        
        actual_over_granted = log['label'] == 'over-granted'
        
        # Check if any rule matches with threshold
        predicted_over_granted = False
        for rule in rules:
            if rule['userId'] == log['userId'] and rule['action'] == log['action']:
                pattern = rule['resourcePattern']
                resource = log['resource']
                
                # Pattern matching
                matches = False
                if pattern.endswith('*'):
                    pattern_stem = pattern[:-1]
                    matches = resource.startswith(pattern_stem)
                else:
                    matches = resource == pattern
                
                if matches and rule['confidence'] >= threshold:
                    predicted_over_granted = True
                    break
        
        # Count metrics
        if predicted_over_granted and actual_over_granted:
            tp += 1
        elif predicted_over_granted and not actual_over_granted:
            fp += 1
        elif not predicted_over_granted and actual_over_granted:
            fn += 1
        else:
            tn += 1
    
    precision = tp / ((tp + fp) or 1)
    recall = tp / ((tp + fn) or 1)
    f1 = 2 * (precision * recall) / ((precision + recall) or 1)
    
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1_score": f1
    }


def evaluate_ablation_variant(logs, variant_name):
    """
    Evaluate a single ablation variant via 5-fold cross-validation.
    
    Args:
        logs: List of log entries with labels
        variant_name: Name of variant ("current", "loose", "prefix")
    
    Returns:
        dict with mean/std metrics across folds
    """
    fold_results = []
    n_folds = 5
    
    # Shuffle logs and split into folds
    shuffled = sorted(logs, key=lambda x: hash(str(x)))
    fold_size = len(shuffled) // n_folds
    
    for fold_idx in range(n_folds):
        # Create fold split
        test_start = fold_idx * fold_size
        test_end = test_start + fold_size if fold_idx < n_folds - 1 else len(shuffled)
        
        test = shuffled[test_start:test_end]
        train = shuffled[:test_start] + shuffled[test_end:]
        
        # Mine rules for this fold
        if variant_name == "current":
            rules = mine_rules_current(train)
            threshold = 0.5
        elif variant_name == "loose":
            rules = mine_rules_loose(train)
            threshold = 0.15
        elif variant_name == "prefix":
            rules = mine_rules_prefix(train)
            threshold = 0.0  # No threshold for prefix matching
        else:
            raise ValueError(f"Unknown variant: {variant_name}")
        
        # Evaluate on test set
        metrics = evaluate_with_threshold(test, rules, threshold=threshold)
        fold_results.append(metrics)
    
    # Compute mean and std across folds
    metrics_keys = ['tp', 'fp', 'fn', 'tn', 'precision', 'recall', 'f1_score']
    mean_metrics = {}
    std_metrics = {}
    
    for key in metrics_keys:
        values = [r[key] for r in fold_results]
        mean_metrics[key] = round(np.mean(values), 3)
        std_metrics[key] = round(np.std(values), 3)
    
    return {
        "variant": variant_name,
        "fold_results": fold_results,
        "mean": mean_metrics,
        "std": std_metrics
    }


def run_ablation_study(logs):
    """
    Run complete ablation study comparing all variants.
    
    Args:
        logs: List of log entries with labels
    
    Returns:
        dict with results for all variants and comparison summary
    """
    variants = ["current", "loose", "prefix"]
    study_results = {}
    
    for variant in variants:
        study_results[variant] = evaluate_ablation_variant(logs, variant)
    
    # Create comparison summary
    variant_names = {
        "current": "Trie (Optimized: min_support=3, min_conf=0.6)",
        "loose": "Trie (Loose: min_support=1, min_conf=0.1)",
        "prefix": "Simple Prefix Matching"
    }
    
    summary = {
        "variants_compared": [variant_names[v] for v in variants],
        "metric": "f1_score",
        "winner": variant_names[max(
            study_results.items(),
            key=lambda x: x[1]['mean']['f1_score']
        )[0]],
        "results": study_results
    }
    
    return summary

