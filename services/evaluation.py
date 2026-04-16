"""
Evaluation and ML analysis services.

Provides metrics calculation and anomaly detection using ML features.
"""

import random
import numpy as np
from sklearn.ensemble import IsolationForest
from .baseline_engine import evaluate_request, matches_pattern


def extract_features(cfg):
    """
    Extract deterministic features for ML analysis.
    
    Features capture structural characteristics of resource access patterns:
    - Resource depth (indicates how deep in hierarchy)
    - Resource length (unusual lengths may be suspicious)
    - Numeric IDs (might indicate data record access)
    - Sensitive keyword count (based on content)
    """
    resource = str(cfg.get('resource', ''))

    # Feature 1: resource depth (more slashes = deeper access)
    f1 = resource.count('/')

    # Feature 2: resource length (unusual lengths may be suspicious)
    f2 = len(resource)

    # Feature 3: exposure marker (very basic - 1 if 0.0.0.0 present)
    f3 = 1 if '0.0.0.0' in str(cfg) else 0

    # Feature 4: risk encoding
    risk_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    f4 = risk_map.get(cfg.get('risk', 'low'), 1)

    # Feature 5: has numeric IDs (might indicate data access)
    f5 = 1 if any(c.isdigit() for c in resource) else 0

    # Feature 6: contains known sensitive keywords
    sensitive_words = ['secret', 'password', 'token', 'key', 'admin', 'private']
    f6 = sum(1 for word in sensitive_words if word in resource.lower())

    return [f1, f2, f3, f4, f5, f6]


def run_isolation_forest(configs, rules=None):
    """
    Detect anomalous configurations using ML and rule deviations.
    
    Combines:
    1. Statistical anomaly detection (Isolation Forest on features)
    2. Rule deviation detection (doesn't match learned baseline)
    
    Returns configs with anomaly flags, scores, and reasoning.
    """
    if not configs:
        return []

    X = np.array([extract_features(cfg) for cfg in configs])
    
    # Need at least 2 samples to fit
    if len(X) < 2:
        return [{
            'id': cfg.get('id'),
            'name': cfg.get('name'),
            'anomaly_score': 0.0,
            'risk': cfg.get('risk'),
            'issue': cfg.get('issue'),
            'flagged': False,
            'reason': 'insufficient_data'
        } for cfg in configs]

    model = IsolationForest(contamination=0.3, random_state=42)
    model.fit(X)

    scores = model.decision_function(X)
    preds = model.predict(X)

    results = []
    for i, cfg in enumerate(configs):
        is_anomaly = preds[i] == -1
        
        # Incorporate baseline rule matching if rules provided
        rule_penalty = 0.0
        if rules and 'userId' in cfg and 'resource' in cfg and 'action' in cfg:
            matches_baseline = any(
                r['userId'] == cfg['userId'] and
                r['action'] == cfg['action'] and
                matches_pattern(cfg['resource'], r['resourcePattern'])
                for r in rules
            )
            # If doesn't match baseline AND is statistical anomaly, stronger signal
            if not matches_baseline:
                rule_penalty = 0.2
        
        flagged = (is_anomaly or rule_penalty > 0)
        
        results.append({
            'id': cfg.get('id'),
            'name': cfg.get('name'),
            'anomaly_score': float(scores[i]) + rule_penalty,
            'risk': cfg.get('risk'),
            'issue': cfg.get('issue'),
            'flagged': flagged,
            'statistical_anomaly': bool(is_anomaly),
            'baseline_deviation': bool(rule_penalty > 0)
        })

    return results


def split_data(logs, train_ratio=0.7):
    """Shuffle and split logs for train/test."""
    random.shuffle(logs)
    split = int(len(logs) * train_ratio)
    return logs[:split], logs[split:]


def cross_validate(logs, n_folds=5):
    """
    Perform N-fold cross-validation.
    
    Reduces variance on small datasets by training/testing on multiple splits.
    Returns average metrics across all folds.
    
    Args:
        logs: List of logs with labels
        n_folds: Number of folds (default 5)
        
    Returns:
        Dict with mean and std of metrics across folds
    """
    from .baseline_engine import mine_coarse_rules, refine_rules
    
    if len(logs) < n_folds:
        return {"error": f"Need at least {n_folds} logs for {n_folds}-fold cross-validation"}
    
    # Shuffle logs
    shuffled = logs.copy()
    random.shuffle(shuffled)
    
    # Split into n_folds
    fold_size = len(shuffled) // n_folds
    folds = [
        shuffled[i*fold_size:(i+1)*fold_size]
        for i in range(n_folds)
    ]
    
    # If there are remainder logs, add them to last fold
    if len(shuffled) % n_folds != 0:
        folds[-1].extend(shuffled[n_folds*fold_size:])
    
    fold_metrics = []
    
    # For each fold, use it as test and rest as train
    for test_fold_idx in range(n_folds):
        test_logs = folds[test_fold_idx]
        train_logs = []
        for i, fold in enumerate(folds):
            if i != test_fold_idx:
                train_logs.extend(fold)
        
        # Get baseline logs (allowed only)
        baseline_logs = [
            log for log in train_logs
            if log.get('label') == 'allowed' or 'label' not in log
        ]
        
        if not baseline_logs:
            continue
        
        # Train rules
        rules = refine_rules(mine_coarse_rules(baseline_logs))
        
        # Evaluate
        metrics = evaluate_baseline_fold(test_logs, rules)
        fold_metrics.append(metrics)
    
    # Compute mean and std
    if not fold_metrics:
        return {"error": "Could not perform cross-validation"}
    
    import numpy as np
    
    mean_metrics = {}
    std_metrics = {}
    
    for key in fold_metrics[0].keys():
        values = [m[key] for m in fold_metrics]
        mean_metrics[key] = round(np.mean(values), 3)
        std_metrics[key] = round(np.std(values), 3)
    
    return {
        'mean': mean_metrics,
        'std': std_metrics,
        'folds': n_folds,
        'fold_results': fold_metrics
    }


def evaluate_baseline_fold(test_logs, rules):
    """Evaluate rules on test logs (single fold)."""
    TP = FP = FN = TN = 0
    
    for log in test_logs:
        if 'label' not in log:
            continue
        
        pred = evaluate_request(log['userId'], log['resource'], log['action'], rules)
        actual = log['label']
        
        if pred == 'over-granted' and actual == 'over-granted':
            TP += 1
        elif pred == 'over-granted' and actual == 'allowed':
            FP += 1
        elif pred == 'allowed' and actual == 'over-granted':
            FN += 1
        else:
            TN += 1
    
    precision = TP / max((TP + FP), 1)
    recall = TP / max((TP + FN), 1)
    f1 = 2 * precision * recall / max((precision + recall), 1)
    
    return {
        'tp': TP,
        'fp': FP,
        'fn': FN,
        'tn': TN,
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1_score': round(f1, 3)
    }


def evaluate_metrics(logs):
    """
    Calculate evaluation metrics (precision, recall, f1) on test set.
    
    Splits logs into train/test, mines rules from train set,
    evaluates predictions against test set labels.
    
    Returns metrics dict with precision, recall, f1_score, and sizes.
    """
    from .baseline_engine import mine_coarse_rules, refine_rules
    
    train, test = split_data(logs)

    # Train rules from allowed logs only
    baseline_logs = [
        log for log in train
        if log.get('label') == 'allowed' or 'label' not in log
    ]
    
    rules = refine_rules(mine_coarse_rules(baseline_logs))

    TP = FP = FN = TN = 0

    for log in test:
        pred = evaluate_request(log['userId'], log['resource'], log['action'], rules)
        # Require explicit labels - no hardcoded fallback
        actual = log.get('label', None)
        
        # Skip logs without labels (need explicit ground truth)
        if actual is None:
            continue

        if pred == 'over-granted' and actual == 'over-granted':
            TP += 1
        elif pred == 'over-granted' and actual == 'allowed':
            FP += 1
        elif pred == 'allowed' and actual == 'over-granted':
            FN += 1
        else:
            TN += 1

    precision = TP / max((TP + FP), 1)
    recall = TP / max((TP + FN), 1)
    f1 = 2 * precision * recall / max((precision + recall), 1)

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "train_size": len(baseline_logs),
        "test_size": len([l for l in test if l.get('label')]),
        "tp": TP,
        "fp": FP,
        "fn": FN,
        "tn": TN
    }
