"""
Test Examples and Demo for Cloud Configuration Analysis

This module contains examples for testing all the new features:
- Config parsing (IAM + K8s)
- Risk scoring
- Remediation suggestions
- Autoencoder anomaly detection
- SHAP explainability
"""

import json
import yaml

# Example 1: IAM Policy (AWS)
EXAMPLE_IAM_POLICY = {
    "PolicyName": "TestPolicy",
    "Statement": [
        {
            "Sid": "PublicAccess",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:*",
                "iam:*"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket/*",
                "arn:aws:secretsmanager:*:*:secret/*"
            ]
        }
    ]
}

# Example 2: Kubernetes Deployment
EXAMPLE_K8S_DEPLOYMENT = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "risky-app",
        "namespace": "production"
    },
    "spec": {
        "template": {
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "myapp:latest",
                        "env": [
                            {
                                "name": "DB_PASSWORD",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "db-credentials",
                                        "key": "password"
                                    }
                                }
                            }
                        ],
                        "securityContext": {
                            "privileged": True,
                            "runAsUser": 0
                        }
                    }
                ],
                "volumes": [
                    {
                        "name": "host-fs",
                        "hostPath": {
                            "path": "/etc/hosts"
                        }
                    }
                ]
            }
        }
    }
}

# Example 3: Normal/Secure IAM Policy (for training autoencoder)
EXAMPLE_NORMAL_POLICY = {
    "PolicyName": "SecurePolicy",
    "Statement": [
        {
            "Sid": "ReadOnly",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:user/app-user"
            },
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::my-bucket/*",
            "Condition": {
                "IpAddress": {
                    "aws:SourceIp": "10.0.0.0/8"
                }
            }
        }
    ]
}


def example_config_parser():
    """Example 1: Parse configurations."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Config Parsing")
    print("="*60)
    
    from services import ConfigParser
    
    parser = ConfigParser()
    
    # Parse IAM policy
    print("\n--- Parsing IAM Policy ---")
    iam_text = json.dumps(EXAMPLE_IAM_POLICY)
    iam_features = parser.analyze_config(iam_text, 'iam')
    
    print(f"Config Type: {iam_features.get('config_type')}")
    print(f"Privilege Level: {iam_features.get('privilege_level')}")
    print(f"Is Public: {iam_features.get('is_public')}")
    print(f"Sensitive Resources: {iam_features.get('sensitive_resources')}")
    print(f"Actions: {iam_features.get('actions')}")
    
    # Parse K8s manifest
    print("\n--- Parsing Kubernetes Manifest ---")
    k8s_text = yaml.dump(EXAMPLE_K8S_DEPLOYMENT)
    k8s_features = parser.analyze_config(k8s_text, 'k8s')
    
    print(f"Config Type: {k8s_features.get('config_type')}")
    print(f"Kind: {k8s_features.get('kind')}")
    print(f"Containers: {[c['name'] for c in k8s_features.get('containers', [])]}")
    print(f"Sensitive Mounts: {k8s_features.get('sensitive_mounts')}")
    
    return iam_features, k8s_features


def example_risk_scoring(iam_features, k8s_features):
    """Example 2: Risk Scoring."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Risk Scoring")
    print("="*60)
    
    from services import RiskScoringEngine
    
    risk_engine = RiskScoringEngine()
    
    # Score IAM policy
    print("\n--- IAM Policy Risk Score ---")
    iam_risk = risk_engine.calculate_risk_score(iam_features)
    
    print(f"Risk Score: {iam_risk['risk_score']}")
    print(f"Risk Level: {iam_risk['risk_level']}")
    print(f"Anomaly Score: {iam_risk['anomaly_score']}")
    print(f"Impact Factor: {iam_risk['impact_factor']}")
    print(f"Sensitivity Score: {iam_risk['sensitivity_score']}")
    
    # Score K8s manifest
    print("\n--- K8s Manifest Risk Score ---")
    k8s_risk = risk_engine.calculate_risk_score(k8s_features)
    
    print(f"Risk Score: {k8s_risk['risk_score']}")
    print(f"Risk Level: {k8s_risk['risk_level']}")
    
    return iam_risk, k8s_risk


def example_remediation(iam_features, iam_risk):
    """Example 3: Remediation Suggestions."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Remediation Suggestions")
    print("="*60)
    
    from services import RemediationEngine
    
    remediation_engine = RemediationEngine()
    
    remediation = remediation_engine.generate_suggestions(
        iam_features,
        iam_risk['risk_score']
    )
    
    print(f"\nTotal Issues: {remediation['total_issues']}")
    print(f"Critical Issues: {remediation['critical_issues']}")
    
    print("\n--- Recommendations by Severity ---")
    for rec in remediation['recommendations_by_severity'][:3]:
        print(f"\n[{rec['severity']}] {rec['pattern']}")
        for suggestion in rec['suggestions'][:2]:
            print(f"  • {suggestion}")
    
    print("\n--- General Recommendations ---")
    for rec in remediation['general_recommendations']:
        print(f"  {rec}")
    
    print("\n--- Action Plan (Top 3) ---")
    for action in remediation['action_plan'][:3]:
        print(f"  {action['priority']}. [{action['severity']}] {action['action']}")
    
    return remediation


def example_autoencoder():
    """Example 4: Autoencoder Anomaly Detection."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Autoencoder Anomaly Detection")
    print("="*60)
    
    from services import ConfigParser, AutoencoderAnomalyDetector
    import json
    
    parser = ConfigParser()
    
    # Parse test configs
    normal_policy_text = json.dumps(EXAMPLE_NORMAL_POLICY)
    normal_features = parser.analyze_config(normal_policy_text, 'iam')
    
    risky_policy_text = json.dumps(EXAMPLE_IAM_POLICY)
    risky_features = parser.analyze_config(risky_policy_text, 'iam')
    
    # Create and train autoencoder
    print("\n--- Training Autoencoder ---")
    autoencoder = AutoencoderAnomalyDetector(device='cpu')
    
    # Train on normal configurations
    training_configs = [normal_features] * 5  # Repeat for demo
    history = autoencoder.train(training_configs, epochs=20, batch_size=2)
    
    print(f"Training completed. Final loss: {history['loss'][-1]:.6f}")
    
    # Test on normal config
    print("\n--- Anomaly Detection: Normal Config ---")
    normal_result = autoencoder.predict(normal_features)
    print(f"Reconstruction Error: {normal_result['reconstruction_error']:.6f}")
    print(f"Anomaly Score: {normal_result['anomaly_score']:.2f}")
    print(f"Is Anomaly: {normal_result['is_anomaly']}")
    
    # Test on risky config
    print("\n--- Anomaly Detection: Risky Config ---")
    risky_result = autoencoder.predict(risky_features)
    print(f"Reconstruction Error: {risky_result['reconstruction_error']:.6f}")
    print(f"Anomaly Score: {risky_result['anomaly_score']:.2f}")
    print(f"Is Anomaly: {risky_result['is_anomaly']}")
    
    # Model info
    print("\n--- Model Information ---")
    model_info = autoencoder.get_model_info()
    print(f"Status: {model_info['status']}")
    print(f"Input Dimension: {model_info['input_dim']}")
    print(f"Encoding Dimension: {model_info['encoding_dim']}")
    print(f"Total Parameters: {model_info['total_parameters']}")
    print(f"Threshold: {model_info['threshold']:.6f}")
    
    return autoencoder


def example_shap_explainability(iam_features, iam_risk):
    """Example 5: SHAP Explainability."""
    print("\n" + "="*60)
    print("EXAMPLE 5: SHAP Explainability")
    print("="*60)
    
    from services import SHAPExplainer
    import numpy as np
    
    explainer = SHAPExplainer()
    
    # Get features as numpy array
    from services.autoencoder import AutoencoderAnomalyDetector
    detector = AutoencoderAnomalyDetector()
    features = detector.extract_features(iam_features)
    
    # Explain anomaly score
    print("\n--- Anomaly Score Explanation ---")
    anomaly_explanation = explainer.explain_anomaly_score(
        features,
        iam_risk['anomaly_score']
    )
    
    print(f"Anomaly Score: {anomaly_explanation['anomaly_score']:.2f}")
    print(f"Confidence: {anomaly_explanation['confidence']}")
    print(f"\nExplanation: {anomaly_explanation['explanation']}")
    
    print("\n--- High-Value Features ---")
    for feature, value in anomaly_explanation['high_value_features'].items():
        print(f"  {feature}: {value:.2f}")
    
    # Explain risk score
    print("\n--- Risk Score Explanation ---")
    risk_explanation = explainer.explain_risk_score(
        {'components': iam_risk['components']},
        iam_risk['risk_score']
    )
    
    print(f"Risk Score: {risk_explanation['risk_score']:.2f}")
    print(f"Total Risk Factors: {risk_explanation['total_factors']}")
    print(f"Critical Factors: {risk_explanation['critical_factors']}")
    
    print("\n--- Risk Factors ---")
    for factor in risk_explanation['risk_factors']:
        print(f"\n[{factor['severity']}] {factor['factor']}")
        print(f"  Contribution: {factor['contribution']}")
        print(f"  Remediation: {factor['remediation']}")
    
    return anomaly_explanation, risk_explanation


def example_api_usage():
    """Example 6: API Usage Guide."""
    print("\n" + "="*60)
    print("EXAMPLE 6: API Endpoints Guide")
    print("="*60)
    
    endpoints = {
        "POST /api/config/upload": {
            "description": "Upload a new configuration (IAM policy or K8s manifest)",
            "payload": {
                "config_type": "iam | k8s | auto",
                "config_name": "my-policy",
                "config_text": "JSON or YAML content",
                "environment": "prod | staging | dev",
                "tags": ["tag1", "tag2"]
            }
        },
        "POST /api/config/scan": {
            "description": "Scan configurations for security issues",
            "payload": {
                "config_ids": ["id1", "id2"],
                "run_autoencoder": True
            }
        },
        "GET /api/config/list": {
            "description": "List all uploaded configurations",
            "query_params": {
                "environment": "prod",
                "risk_level": "CRITICAL",
                "analyzed": "true"
            }
        },
        "GET /api/config/<config_id>": {
            "description": "Get detailed analysis for a configuration",
            "query_params": {
                "include_raw": "false"
            }
        },
        "GET /api/config/<config_id>/remediation": {
            "description": "Get detailed remediation plan"
        },
        "POST /api/config/export/summary": {
            "description": "Export summary report",
            "payload": {
                "format": "json | csv | html",
                "include_details": False
            }
        },
        "POST /api/config/train-autoencoder": {
            "description": "Train autoencoder on normal configurations",
            "payload": {
                "config_ids": ["id1", "id2", "id3"],
                "epochs": 50,
                "learning_rate": 0.001
            }
        }
    }
    
    for endpoint, info in endpoints.items():
        print(f"\n{endpoint}")
        print(f"  Description: {info['description']}")
        if 'payload' in info:
            try:
                payload_str = json.dumps(info['payload'], indent=4)
                print(f"  Payload: {payload_str}")
            except:
                # Fallback if JSON serialization fails
                print(f"  Payload: {info['payload']}")
        if 'query_params' in info:
            print(f"  Query Params: {info['query_params']}")


def run_all_examples():
    """Run all examples."""
    print("\n" + "="*70)
    print("CLOUD CONFIGURATION ANALYSIS - COMPLETE FEATURE DEMONSTRATION")
    print("="*70)
    
    try:
        # Example 1: Config Parsing
        iam_features, k8s_features = example_config_parser()
        
        # Example 2: Risk Scoring
        iam_risk, k8s_risk = example_risk_scoring(iam_features, k8s_features)
        
        # Example 3: Remediation
        remediation = example_remediation(iam_features, iam_risk)
        
        # Example 4: Autoencoder
        autoencoder = example_autoencoder()
        
        # Example 5: SHAP Explainability
        anomaly_exp, risk_exp = example_shap_explainability(iam_features, iam_risk)
        
        # Example 6: API Guide
        example_api_usage()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
