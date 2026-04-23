"""
Routes for request evaluation and performance metrics.
"""

from flask import Blueprint, jsonify, request
from db import logs_collection, rules_collection
from services import evaluate_request, run_isolation_forest, evaluate_metrics
from services.baselines import compare_baselines
from services.evaluation import cross_validate

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api')


@evaluation_bp.route('/logs/upload', methods=['POST'])
def upload_logs():
    """
    Upload access logs to the system.
    
    Expected JSON:
    {
        "logs": [
            {"userId": "alice", "action": "READ", "resource": "s3://bucket/file.txt", 
             "label": "allowed", "timestamp": "2026-04-15T..."},
            ...
        ]
    }
    """
    from datetime import datetime
    
    data = request.json
    if not data or "logs" not in data:
        return jsonify({"error": "No logs provided"}), 400

    valid = []
    for log in data["logs"]:
        if all(k in log for k in ("userId", "action", "resource")):
            log["timestamp"] = log.get("timestamp", datetime.utcnow().isoformat())
            valid.append(log)

    if not valid:
        return jsonify({"error": "No valid logs"}), 400

    logs_collection.insert_many(valid)
    return jsonify({"message": "Logs uploaded", "count": len(valid)})


@evaluation_bp.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve all logs with evaluation verdicts."""
    logs = list(logs_collection.find({}, {"_id": 0}))
    rules = list(rules_collection.find({}, {"_id": 0}))

    enriched = [{
        **log,
        "verdict": evaluate_request(log['userId'], log['resource'], log['action'], rules)
    } for log in logs]

    return jsonify({"logs": enriched, "count": len(enriched)})


@evaluation_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Evaluate a single access request.
    
    Expected JSON:
    {"userId": "alice", "action": "READ", "resource": "s3://bucket/file.txt"}
    """
    data = request.json or {}
    rules = list(rules_collection.find({}, {"_id": 0}))

    if not rules:
        return jsonify({"error": "Run baseline inference first"}), 400

    if not all(k in data for k in ("userId", "resource", "action")):
        return jsonify({"error": "Missing fields: userId, resource, action"}), 400

    verdict = evaluate_request(data['userId'], data['resource'], data['action'], rules)

    return jsonify({
        "verdict": verdict,
        "risk": "over-granted" if verdict == "over-granted" else "normal"
    })


@evaluation_bp.route('/evaluate/metrics', methods=['GET'])
def get_metrics():
    """
    Calculate evaluation metrics (precision, recall, f1-score).
    
    Requires logs with explicit 'label' field (allowed/over-granted).
    """
    logs = list(logs_collection.find({}, {"_id": 0}))
    
    if not logs:
        return jsonify({"error": "No logs available"}), 400
    
    metrics = evaluate_metrics(logs)
    return jsonify(metrics)


@evaluation_bp.route('/ml/analyze', methods=['POST'])
def ml_analyze():
    """
    Analyze configurations using ML model integrated with baseline rules.
    
    Returns breakdown of statistical anomalies vs baseline deviations.
    """
    configs = request.json.get("configs", [])
    rules = list(rules_collection.find({}, {"_id": 0}))
    
    results = run_isolation_forest(configs, rules=rules)

    return jsonify({
        "results": results,
        "flagged": sum(1 for r in results if r['flagged']),
        "statistical_anomalies": sum(1 for r in results if r.get('statistical_anomaly')),
        "baseline_deviations": sum(1 for r in results if r.get('baseline_deviation'))
    })


@evaluation_bp.route('/evaluate/cross-validate', methods=['GET'])
def cross_validate_endpoint():
    """
    Perform 5-fold cross-validation.
    
    Reduces variance on small datasets by training/testing on multiple splits.
    Returns mean and standard deviation of metrics across folds.
    """
    logs = list(logs_collection.find({}, {"_id": 0}))
    
    if not logs:
        return jsonify({"error": "No logs available"}), 400
    
    # Get n_folds from query param (default 5)
    n_folds = request.args.get('folds', 5, type=int)
    
    results = cross_validate(logs, n_folds=n_folds)
    
    return jsonify({
        "cross_validation": results,
        "note": f"{n_folds}-fold cross-validation reduces variance on small datasets",
        "total_logs": len([l for l in logs if l.get('label')])
    })


@evaluation_bp.route('/evaluate/compare-baselines', methods=['GET'])
def compare_baselines_endpoint():
    """
    Compare naive (frequency-based) vs Trie-based baselines.
    
    Shows how pattern extraction (Trie) improves over simple frequency counting.
    """
    logs = list(logs_collection.find({}, {"_id": 0}))
    
    if not logs:
        return jsonify({"error": "No logs available"}), 400
    
    comparison = compare_baselines(logs)
    
    return jsonify({
        "comparison": comparison,
        "note": "Naive = top-K frequency, Trie = pattern-based extraction",
        "logs_evaluated": len([l for l in logs if l.get('label')])
    })


@evaluation_bp.route('/evaluate/ablation', methods=['GET'])
def ablation_study_endpoint():
    """
    Run ablation study comparing multiple rule mining variants:
    1. Current Trie (optimized parameters: min_support=3, min_conf=0.6)
    2. Loose Trie (minimal parameters: min_support=1, min_conf=0.1)
    3. Simple Prefix (no pattern mining, prefix-based matching)
    
    Returns 5-fold cross-validation results for each variant showing impact
    of design choices on detection performance.
    """
    from services import run_ablation_study
    import traceback
    
    logs = list(logs_collection.find({}, {"_id": 0}))
    
    if not logs or not any(l.get('label') for l in logs):
        return jsonify({"error": "No labeled logs available for ablation study"}), 400
    
    try:
        study_results = run_ablation_study(logs)
    except Exception as e:
        import traceback
        return jsonify({
            "error": f"Ablation study failed: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500
    
    return jsonify({
        "ablation_study": study_results,
        "note": "Compares impact of thresholds, parameters, and algorithm choices",
        "method": "5-fold cross-validation per variant",
        "total_logs": len([l for l in logs if l.get('label')])
    })


@evaluation_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})
