"""
Routes for cloud configuration analysis and management.

Endpoints:
- POST /api/config/upload - Upload IAM policies or K8s manifests
- POST /api/config/scan - Scan uploaded configs for issues
- GET /api/config/list - List all analyzed configs
- GET /api/config/<config_id> - Get details and remediation for a specific config
"""

from flask import Blueprint, jsonify, request
from db import configs_collection
from services import (
    ConfigParser,
    RiskScoringEngine,
    RemediationEngine,
    AutoencoderAnomalyDetector,
    SHAPExplainer
)
import json
from datetime import datetime
from bson.objectid import ObjectId

config_bp = Blueprint('config', __name__, url_prefix='/api/config')

# Global services
parser = ConfigParser()
risk_engine = RiskScoringEngine()
remediation_engine = RemediationEngine()
explainer = SHAPExplainer()

# Autoencoder (lazily initialized on first training data)
autoencoder = None


@config_bp.route('/upload', methods=['POST'])
def upload_config():
    """
    Upload cloud configuration (IAM policy or Kubernetes manifest).
    
    Expected JSON:
    {
        "config_type": "iam" or "k8s" or "auto",
        "config_name": "my-policy",
        "config_text": "JSON or YAML content",
        "environment": "prod/staging/dev",
        "tags": ["tag1", "tag2"]
    }
    
    Returns:
        Config ID and preliminary analysis
    """
    data = request.json or {}
    
    # Validate input
    if 'config_text' not in data:
        return jsonify({'error': 'Missing config_text'}), 400
    
    config_type = data.get('config_type', 'auto')
    config_name = data.get('config_name', f'config_{datetime.now().isoformat()}')
    config_text = data['config_text']
    environment = data.get('environment', 'unknown')
    tags = data.get('tags', [])
    
    # Parse configuration
    config_analysis = parser.analyze_config(config_text, config_type)
    
    if 'error' in config_analysis:
        return jsonify({'error': config_analysis['error']}), 400
    
    # Store in database
    config_doc = {
        'name': config_name,
        'config_type': config_analysis.get('config_type'),
        'environment': environment,
        'tags': tags,
        'config_text': config_text,
        'analysis': config_analysis,
        'uploaded_at': datetime.utcnow().isoformat(),
        'analyzed': False,
        'risk_score': None
    }
    
    result = configs_collection.insert_one(config_doc)
    config_id = str(result.inserted_id)
    
    return jsonify({
        'message': 'Configuration uploaded successfully',
        'config_id': config_id,
        'config_name': config_name,
        'config_type': config_analysis.get('config_type'),
        'parsed_features': {
            'privilege_level': config_analysis.get('privilege_level'),
            'is_public': config_analysis.get('is_public'),
            'sensitive_resources': len(config_analysis.get('sensitive_resources', []))
        }
    }), 201


@config_bp.route('/scan', methods=['POST'])
def scan_config():
    """
    Analyze uploaded config for security issues.
    
    Expected JSON:
    {
        "config_ids": ["id1", "id2"] or null for all,
        "run_autoencoder": true/false
    }
    
    Returns:
        Risk scores, remediation suggestions, and explanations
    """
    data = request.json or {}
    
    config_ids = data.get('config_ids')
    run_autoencoder = data.get('run_autoencoder', False)
    
    # Get configs to analyze
    if config_ids:
        try:
            configs = list(configs_collection.find(
                {'_id': {'$in': [ObjectId(cid) for cid in config_ids]}},
                {'_id': 1, 'analysis': 1, 'name': 1, 'config_text': 1}
            ))
        except:
            return jsonify({'error': 'Invalid config IDs'}), 400
    else:
        configs = list(configs_collection.find(
            {'analyzed': False},
            {'_id': 1, 'analysis': 1, 'name': 1, 'config_text': 1}
        ))
    
    if not configs:
        return jsonify({'error': 'No configurations to analyze'}), 400
    
    results = []
    
    for config in configs:
        config_id = str(config['_id'])
        analysis = config.get('analysis', {})
        
        # Calculate risk score
        risk_result = risk_engine.calculate_risk_score(analysis)
        
        # Generate remediation suggestions
        remediation = remediation_engine.generate_suggestions(
            analysis,
            risk_result['risk_score']
        )
        
        # Generate SHAP explanation
        explanation = explainer.explain_risk_score(
            {'components': risk_result.get('components', {})},
            risk_result['risk_score']
        )
        
        # Autoencoder analysis (optional)
        autoencoder_result = None
        if run_autoencoder:
            autoencoder_result = _run_autoencoder_analysis(analysis)
        
        result = {
            'config_id': config_id,
            'config_name': config.get('name', 'unnamed'),
            'risk_score': risk_result,
            'remediation': remediation,
            'explanation': explanation,
            'scan_time': datetime.utcnow().isoformat()
        }
        
        if autoencoder_result:
            result['anomaly_detection'] = autoencoder_result
        
        results.append(result)
        
        # Update database
        configs_collection.update_one(
            {'_id': config['_id']},
            {'$set': {
                'analyzed': True,
                'risk_score': risk_result['risk_score'],
                'risk_level': risk_result['risk_level'],
                'remediation': remediation,
                'explanation': explanation,
                'last_analyzed': datetime.utcnow().isoformat()
            }}
        )
    
    # Sort by risk score
    results.sort(key=lambda x: x['risk_score']['risk_score'], reverse=True)
    
    # Get summary
    summary = _get_scan_summary(results)
    
    return jsonify({
        'scan_results': results,
        'summary': summary,
        'total_configs': len(results),
        'configs_analyzed': len([r for r in results if r.get('risk_score')])
    }), 200


@config_bp.route('/list', methods=['GET'])
def list_configs():
    """
    List all uploaded configurations.
    
    Query params:
    - environment: filter by environment
    - risk_level: filter by risk level
    - analyzed: true/false
    """
    query = {}
    
    environment = request.args.get('environment')
    if environment:
        query['environment'] = environment
    
    risk_level = request.args.get('risk_level')
    if risk_level:
        query['risk_level'] = risk_level
    
    analyzed = request.args.get('analyzed')
    if analyzed is not None:
        query['analyzed'] = analyzed.lower() == 'true'
    
    configs = list(configs_collection.find(query, {
        '_id': 1, 'name': 1, 'config_type': 1, 'environment': 1,
        'risk_score': 1, 'risk_level': 1, 'uploaded_at': 1, 'analyzed': 1
    }).sort('uploaded_at', -1))
    
    # Convert ObjectId to string
    configs = [
        {**cfg, '_id': str(cfg['_id'])}
        for cfg in configs
    ]
    
    return jsonify({
        'configs': configs,
        'total': len(configs)
    }), 200


@config_bp.route('/<config_id>', methods=['GET'])
def get_config_detail(config_id):
    """
    Get detailed analysis and remediation for a specific config.
    """
    try:
        config = configs_collection.find_one({'_id': ObjectId(config_id)})
    except:
        return jsonify({'error': 'Invalid config ID'}), 400
    
    if not config:
        return jsonify({'error': 'Config not found'}), 404
    
    # Prepare response
    response = {
        'config_id': str(config['_id']),
        'name': config.get('name'),
        'config_type': config.get('config_type'),
        'environment': config.get('environment'),
        'tags': config.get('tags', []),
        'uploaded_at': config.get('uploaded_at'),
        'analyzed': config.get('analyzed'),
        'analysis': config.get('analysis', {}),
        'risk_score': config.get('risk_score'),
        'risk_level': config.get('risk_level'),
        'remediation': config.get('remediation'),
        'explanation': config.get('explanation'),
        'last_analyzed': config.get('last_analyzed')
    }
    
    # Optionally include raw config
    include_raw = request.args.get('include_raw', 'false').lower() == 'true'
    if include_raw:
        response['config_text'] = config.get('config_text')
    
    return jsonify(response), 200


@config_bp.route('/<config_id>/remediation', methods=['GET'])
def get_remediation(config_id):
    """Get detailed remediation plan for a config."""
    try:
        config = configs_collection.find_one({'_id': ObjectId(config_id)})
    except:
        return jsonify({'error': 'Invalid config ID'}), 400
    
    if not config:
        return jsonify({'error': 'Config not found'}), 404
    
    remediation = config.get('remediation')
    if not remediation:
        return jsonify({'error': 'Config has not been analyzed yet'}), 400
    
    return jsonify({
        'config_id': str(config['_id']),
        'config_name': config.get('name'),
        'risk_level': config.get('risk_level'),
        'remediation': remediation
    }), 200


@config_bp.route('/export/summary', methods=['POST'])
def export_summary():
    """
    Export summary report of all analyzed configurations.
    
    Useful for compliance and audit purposes.
    """
    data = request.json or {}
    
    format_type = data.get('format', 'json')  # json, csv, html
    include_details = data.get('include_details', False)
    
    # Get all analyzed configs
    configs = list(configs_collection.find(
        {'analyzed': True},
        {'_id': 1, 'name': 1, 'risk_level': 1, 'risk_score': 1, 'environment': 1, 'remediation': 1}
    ).sort('risk_score', -1))
    
    # Build summary
    summary = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_configs': len(configs),
        'risk_distribution': _count_risk_levels(configs),
        'by_environment': _group_by_environment(configs),
        'recommendations': _aggregate_recommendations(configs)
    }
    
    if include_details:
        summary['configs'] = [
            {**cfg, '_id': str(cfg['_id'])}
            for cfg in configs
        ]
    
    if format_type == 'json':
        return jsonify(summary), 200
    elif format_type == 'csv':
        # Simple CSV conversion
        csv_content = _dict_to_csv(configs)
        return csv_content, 200, {'Content-Type': 'text/csv'}
    else:
        return jsonify({'error': f'Unsupported format: {format_type}'}), 400


@config_bp.route('/train-autoencoder', methods=['POST'])
def train_autoencoder():
    """
    Train autoencoder on normal configurations.
    
    Expected JSON:
    {
        "config_ids": ["id1", "id2", ...],
        "epochs": 50,
        "learning_rate": 0.001
    }
    """
    global autoencoder
    
    data = request.json or {}
    config_ids = data.get('config_ids', [])
    epochs = data.get('epochs', 50)
    learning_rate = data.get('learning_rate', 0.001)
    
    if not config_ids:
        return jsonify({'error': 'No config IDs provided'}), 400
    
    try:
        configs = list(configs_collection.find(
            {'_id': {'$in': [ObjectId(cid) for cid in config_ids]}},
            {'_id': 1, 'analysis': 1}
        ))
    except:
        return jsonify({'error': 'Invalid config IDs'}), 400
    
    if not configs:
        return jsonify({'error': 'No configurations found'}), 404
    
    # Initialize and train autoencoder
    autoencoder = AutoencoderAnomalyDetector()
    
    try:
        history = autoencoder.train(
            [cfg['analysis'] for cfg in configs],
            epochs=epochs,
            learning_rate=learning_rate
        )
        
        model_info = autoencoder.get_model_info()
        
        return jsonify({
            'message': 'Autoencoder trained successfully',
            'configs_used': len(configs),
            'model_info': model_info,
            'training_epochs': epochs
        }), 200
    except Exception as e:
        return jsonify({'error': f'Training failed: {str(e)}'}), 500


# Helper functions

def _run_autoencoder_analysis(analysis):
    """Run autoencoder analysis if model is trained."""
    global autoencoder
    
    if autoencoder is None:
        return None
    
    try:
        result = autoencoder.predict(analysis)
        return result
    except:
        return None


def _get_scan_summary(results):
    """Create summary of scan results."""
    risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    
    for result in results:
        level = result['risk_score'].get('risk_level', 'MINIMAL')
        if level in risk_counts:
            risk_counts[level] += 1
    
    critical_actions = sum(
        result['remediation'].get('critical_issues', 0)
        for result in results
    )
    
    return {
        'risk_distribution': risk_counts,
        'total_critical_issues': critical_actions,
        'highest_risk_config': results[0] if results else None
    }


def _count_risk_levels(configs):
    """Count configs by risk level."""
    counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    
    for cfg in configs:
        level = cfg.get('risk_level', 'MINIMAL')
        if level in counts:
            counts[level] += 1
    
    return counts


def _group_by_environment(configs):
    """Group configs by environment."""
    groups = {}
    
    for cfg in configs:
        env = cfg.get('environment', 'unknown')
        if env not in groups:
            groups[env] = {'count': 0, 'critical': 0}
        
        groups[env]['count'] += 1
        if cfg.get('risk_level') == 'CRITICAL':
            groups[env]['critical'] += 1
    
    return groups


def _aggregate_recommendations(configs):
    """Aggregate top recommendations across all configs."""
    recommendations = {}
    
    for cfg in configs:
        remediation = cfg.get('remediation', {})
        for rec in remediation.get('recommendations_by_severity', []):
            pattern = rec.get('pattern', 'unknown')
            if pattern not in recommendations:
                recommendations[pattern] = 0
            recommendations[pattern] += 1
    
    # Sort by frequency
    return dict(sorted(recommendations.items(), key=lambda x: x[1], reverse=True))


def _dict_to_csv(configs):
    """Convert configs to CSV format."""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Config ID', 'Name', 'Risk Level', 'Risk Score', 'Environment'])
    
    for cfg in configs:
        writer.writerow([
            str(cfg['_id']),
            cfg.get('name', ''),
            cfg.get('risk_level', ''),
            cfg.get('risk_score', ''),
            cfg.get('environment', '')
        ])
    
    return output.getvalue()
