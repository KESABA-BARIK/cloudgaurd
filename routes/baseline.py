"""
Routes for baseline rule inference and evaluation.
"""

from flask import Blueprint, jsonify, request
from db import logs_collection, rules_collection
from services import mine_coarse_rules, refine_rules, evaluate_request
from utils.serializer import serialize

baseline_bp = Blueprint('baseline', __name__, url_prefix='/api/baseline')


@baseline_bp.route('/infer', methods=['POST'])
def infer_baseline():
    """
    Generate baseline rules from access logs.
    
    Process:
    1. Load all logs from database
    2. Filter to only "allowed" logs for baseline
    3. Mine patterns using Trie-based extraction
    4. Store refined rules in database
    """
    all_logs = list(logs_collection.find({}, {"_id": 0}))

    if not all_logs:
        return jsonify({"error": "Upload logs first"}), 400

    # Only learn baseline from "allowed" logs
    baseline_logs = [
        log for log in all_logs 
        if log.get('label') == 'allowed' or 'label' not in log
    ]
    
    if not baseline_logs:
        return jsonify({"error": "No allowed logs to train from. Add logs with label='allowed'"}), 400

    coarse = mine_coarse_rules(baseline_logs)
    refined = refine_rules(coarse)

    rules_collection.delete_many({})
    if refined:
        rules_collection.insert_many([dict(r) for r in refined])

    return jsonify(serialize({
        "coarse_rules": coarse,
        "refined_rules": refined,
        "baseline_logs": len(baseline_logs),
        "logs_processed": len(all_logs),
        "rules_generated": len(refined)
    }))


@baseline_bp.route('/rules', methods=['GET'])
def get_rules():
    """Retrieve current baseline rules."""
    rules = list(rules_collection.find({}, {"_id": 0}))
    return jsonify({
        "rules": rules,
        "count": len(rules)
    })
