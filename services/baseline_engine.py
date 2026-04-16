"""
Baseline access control engine using Trie-based pattern extraction.

Learns normal user behavior patterns from access logs and generates
rules that distinguish between normal and anomalous access.
"""

import re
from collections import defaultdict, Counter


def parameterize(path):
    """Replace numeric IDs in path with {id} placeholder."""
    return re.sub(r'\d+', '{id}', path)


class TrieNode:
    """Single node in the Trie structure."""
    def __init__(self):
        self.children = {}
        self.count = 0
        self.end = False


class Trie:
    """
    Trie for pattern extraction with improved maximal pattern detection.
    
    Builds a tree of resource paths and extracts patterns that represent
    common access behaviors without being overly specific to individual files.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, path):
        """Insert a resource path into the Trie."""
        node = self.root
        parts = path.split('/')
        for part in parts:
            if part not in node.children:
                node.children[part] = TrieNode()
            node = node.children[part]
            node.count += 1
        node.end = True

    def extract_patterns(self, total_logs, min_support=3, min_conf=0.6):
        """
        Extract maximal patterns with strict criteria.
        
        Maximal = node has high support AND its parent has significantly 
        lower support, OR it's a non-leaf node with good confidence.
        
        This avoids outputting every individual file accessed.
        """
        patterns = []

        def dfs(node, path, parent_count=0):
            if not path:  # Root node
                for key, child in node.children.items():
                    dfs(child, [key], node.count)
                return

            confidence = node.count / total_logs
            
            # MAXIMAL PATTERN CRITERIA (improved):
            # 1. Strong support (min_support)
            # 2. Good confidence (min_conf)
            # 3. NOT a leaf node (has children = broader pattern) OR
            #    Parent count is significantly lower (>=2x difference)
            
            has_children = len(node.children) > 0
            significant_dropoff = (parent_count > 0 and node.count < parent_count * 0.5)
            is_maximal = (node.count >= min_support and 
                         (has_children or significant_dropoff))
            
            if is_maximal and confidence >= min_conf:
                patterns.append({
                    "pattern": "/".join(path) + "/*",
                    "support": node.count,
                    "confidence": round(confidence, 2)
                })
            
            # Recursively process children
            for key, child in node.children.items():
                dfs(child, path + [key], node.count)

        dfs(self.root, [])
        return patterns


def mine_coarse_rules(logs):
    """
    Mine access control rules from logs using Trie-based pattern extraction.
    
    Process:
    1. Group logs by (userId, action) pair
    2. For each group, build a Trie of resource paths
    3. Extract maximal patterns (broad access patterns)
    4. Filter by confidence threshold (0.5 minimum)
    
    Args:
        logs: List of access log entries with userId, action, resource
        
    Returns:
        List of rules with userId, action, resourcePattern, support, confidence
    """
    grouped = defaultdict(list)

    for log in logs:
        grouped[(log['userId'], log['action'])].append(log)

    rules = []

    for (uid, action), log_list in grouped.items():
        if not log_list:
            continue
        
        trie = Trie()
        for log in log_list:
            trie.insert(log['resource'])

        patterns = trie.extract_patterns(
            len(log_list),
            min_support=3,      # Need at least 3 accesses to a pattern
            min_conf=0.6        # 60% confidence minimum
        )

        # Fallback: if no patterns found, use most common resource
        if not patterns:
            resource_counts = Counter(log['resource'] for log in log_list)
            most_common, count = resource_counts.most_common(1)[0]
            patterns = [{
                "pattern": most_common,
                "support": count,
                "confidence": count / len(log_list)
            }]

        for p in patterns:
            confidence = p["confidence"]
            
            # Only include strong rules (50% confidence minimum)
            if confidence >= 0.5:
                rules.append({
                    "userId": uid,
                    "action": action,
                    "resourcePattern": parameterize(p["pattern"]),
                    "support": p["support"],
                    "confidence": round(confidence, 2)
                })

    return rules


def refine_rules(rules):
    """
    Clean up rules by preserving protocol separators.
    
    Removes doubled slashes while preserving :// protocol separators.
    """
    refined = []

    for r in rules:
        pattern = r['resourcePattern']

        # Preserve protocol separators (://) while removing duplicate slashes
        pattern = pattern.replace("://", "__PROTO__")
        pattern = pattern.replace("//", "/")
        pattern = pattern.replace("__PROTO__", "://")

        refined.append({
            'userId': r['userId'],
            'action': r['action'],
            'resourcePattern': pattern,
            'support': r.get('support', 1),
            'type': 'refined'
        })

    return refined


def matches_pattern(resource, pattern):
    """
    Check if a resource matches an access pattern using regex.
    
    Converts pattern placeholders to regex:
    - {id} matches one or more digits
    - * matches any characters
    """
    regex = pattern
    
    try:
        # Escape special regex characters first
        regex = regex.replace('\\', '/')
        regex = regex.replace('.', r'\.')
        regex = regex.replace('*', r'.*')
        regex = regex.replace('{id}', r'\d+')
        
        # Try both fullmatch (entire string) and search (substring)
        return re.fullmatch(regex, resource) is not None or re.search(regex, resource) is not None
    except:
        return False


def evaluate_request(user_id, resource, action, rules):
    """
    Evaluate if an access request matches the learned baseline.
    
    Returns 'allowed' if the request matches any rule for this user,
    'over-granted' if it doesn't match any rule (anomalous behavior).
    """
    matches_rule = any(
        r['userId'] == user_id and
        r['action'] == action and
        matches_pattern(resource, r['resourcePattern'])
        for r in rules
    )
    
    if matches_rule:
        return 'allowed'  # Matches learned baseline
    else:
        return 'over-granted'  # Anomalous - outside learned patterns
