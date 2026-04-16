"""
Routes for dashboard and summary endpoints.
"""

from flask import Blueprint, jsonify
from db import logs_collection, rules_collection
from services import evaluate_request
from collections import defaultdict
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/summary', methods=['GET'])
def dashboard_summary():
    """
    Return dashboard summary with real computed values.
    
    Aggregates actual log detection results by date and returns
    detection rate, trend analysis, and summary statistics.
    """
    logs = list(logs_collection.find({}, {"_id": 0}))
    rules = list(rules_collection.find({}, {"_id": 0}))

    # Count over-granted detections
    over_granted_count = sum(
        1 for log in logs
        if evaluate_request(log['userId'], log['resource'], log['action'], rules) == "over-granted"
    )

    # Calculate trend from actual logs (by date)
    trend_by_date = defaultdict(lambda: {"over_granted": 0, "normal": 0})
    
    for log in logs:
        # Parse timestamp and get date
        if 'timestamp' in log:
            try:
                ts = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                date_key = ts.strftime("%b %d")
            except:
                date_key = "Unknown"
        else:
            date_key = "Unknown"
        
        verdict = evaluate_request(log['userId'], log['resource'], log['action'], rules)
        if verdict == "over-granted":
            trend_by_date[date_key]["over_granted"] += 1
        else:
            trend_by_date[date_key]["normal"] += 1
    
    # Format trend as sorted list
    trend = [
        {"date": date, **counts}
        for date, counts in sorted(trend_by_date.items())
    ]

    return jsonify({
        "total": len(logs),
        "over_granted": over_granted_count,
        "normal": len(logs) - over_granted_count,
        "detection_rate": round((over_granted_count / max(len(logs), 1)) * 100, 2),
        "trend": trend,
        "rules_active": len(list(rules_collection.find({}, {"_id": 0})))
    })


@dashboard_bp.route('/stats', methods=['GET'])
def dashboard_stats():
    """
    Return detailed statistics for dashboard.
    
    Includes breakdown by user, action, and resource type.
    """
    logs = list(logs_collection.find({}, {"_id": 0}))
    rules = list(rules_collection.find({}, {"_id": 0}))

    # Stats by user
    user_stats = defaultdict(lambda: {"allowed": 0, "over_granted": 0})
    for log in logs:
        verdict = evaluate_request(log['userId'], log['resource'], log['action'], rules)
        if verdict == "over-granted":
            user_stats[log['userId']]["over_granted"] += 1
        else:
            user_stats[log['userId']]["allowed"] += 1

    # Stats by action
    action_stats = defaultdict(lambda: {"allowed": 0, "over_granted": 0})
    for log in logs:
        verdict = evaluate_request(log['userId'], log['resource'], log['action'], rules)
        if verdict == "over-granted":
            action_stats[log['action']]["over_granted"] += 1
        else:
            action_stats[log['action']]["allowed"] += 1

    return jsonify({
        "by_user": dict(user_stats),
        "by_action": dict(action_stats),
        "total_logs": len(logs),
        "total_rules": len(rules)
    })
