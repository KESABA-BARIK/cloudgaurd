"""
SHAP (SHapley Additive exPlanations) Explainability

Provides interpretable ML predictions using SHAP values.
Explains feature contributions to anomaly detection and risk scoring.
"""

import numpy as np
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')


class SHAPExplainer:
    """
    Simplified SHAP explainer for anomaly detection and risk scoring.
    
    Uses permutation-based feature importance (approximate SHAP values).
    Explains which features most influence the model's predictions.
    """
    
    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or [
            'Privilege Level',
            'Public Access',
            'Sensitive Resources',
            'Action Count',
            'Resource Count',
            'Principal Count',
            'Has Conditions',
            'Sensitivity Score',
            'Resource Depth',
            'Principal Diversity',
            'K8s Exposure',
            'Volume Sensitivity'
        ]
        self.baseline_values = None
    
    def calculate_permutation_importance(self,
                                       features: np.ndarray,
                                       model_fn,
                                       n_permutations: int = 10) -> Dict[str, float]:
        """
        Calculate approximate SHAP values using permutation importance.
        
        Args:
            features: Feature vector
            model_fn: Function that takes features and returns prediction
            n_permutations: Number of random permutations
        
        Returns:
            Dict mapping feature names to importance scores
        """
        # Get baseline prediction
        baseline_pred = model_fn(features.reshape(1, -1))[0]
        
        importances = {}
        
        for i, feature_name in enumerate(self.feature_names):
            importance = 0.0
            
            for _ in range(n_permutations):
                # Permute feature i
                features_permuted = features.copy()
                features_permuted[i] = np.random.choice(features[:, i] if len(features.shape) > 1 else [0, 1])
                
                # Get prediction with permuted feature
                permuted_pred = model_fn(features_permuted.reshape(1, -1))[0]
                
                # Importance = change in prediction
                importance += abs(baseline_pred - permuted_pred)
            
            importances[feature_name] = importance / n_permutations
        
        # Normalize to 0-100
        total = sum(importances.values())
        if total > 0:
            importances = {k: (v / total) * 100 for k, v in importances.items()}
        
        return importances
    
    def explain_anomaly_score(self, features: np.ndarray,
                             anomaly_score: float,
                             model_fn = None) -> Dict[str, Any]:
        """
        Explain why a configuration received a specific anomaly score.
        
        Args:
            features: Feature vector (12-dimensional)
            anomaly_score: Model's anomaly score prediction
            model_fn: Optional model function for importance calculation
        
        Returns:
            Explanation with feature contributions
        """
        # Feature analysis
        feature_values = {
            self.feature_names[i]: float(features[i])
            for i in range(len(features))
        }
        
        # Identify high-value features (may indicate anomalies)
        high_value_features = {
            name: value for name, value in feature_values.items()
            if self._is_anomalous_value(name, value)
        }
        
        # Generate explanation text
        explanation_text = self._generate_explanation_text(
            high_value_features,
            anomaly_score
        )
        
        # Calculate approximate feature importance
        importance = {}
        if model_fn:
            importance = self.calculate_permutation_importance(features, model_fn)
        else:
            # Use heuristic importance based on values
            importance = self._heuristic_importance(high_value_features)
        
        return {
            'anomaly_score': anomaly_score,
            'feature_values': feature_values,
            'high_value_features': high_value_features,
            'feature_importance': importance,
            'explanation': explanation_text,
            'confidence': self._calculate_confidence(high_value_features, anomaly_score)
        }
    
    def explain_risk_score(self, config_features: Dict[str, Any],
                          risk_score: float) -> Dict[str, Any]:
        """
        Explain risk score components and their contributions.
        
        Args:
            config_features: Config features dict (from risk scoring)
            risk_score: Calculated risk score
        
        Returns:
            Risk score explanation
        """
        components = config_features.get('components', {})
        
        risk_factors = []
        
        # Analyze privilege level
        privilege = components.get('privilege_level', 'low')
        if privilege in ['high', 'critical']:
            risk_factors.append({
                'factor': 'High Privilege Level',
                'severity': 'HIGH',
                'contribution': f'Privilege level "{privilege}" increases risk',
                'remediation': 'Apply principle of least privilege'
            })
        
        # Check public exposure
        if components.get('is_public', False):
            risk_factors.append({
                'factor': 'Public Access',
                'severity': 'CRITICAL',
                'contribution': 'Configuration is publicly accessible',
                'remediation': 'Restrict access to specific principals only'
            })
        
        # Check sensitive resources
        sensitive_count = components.get('sensitive_resources_count', 0)
        if sensitive_count > 0:
            risk_factors.append({
                'factor': 'Sensitive Resources Access',
                'severity': 'HIGH',
                'contribution': f'Accessing {sensitive_count} sensitive resource(s)',
                'remediation': 'Add encryption and additional access controls'
            })
        
        return {
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'total_factors': len(risk_factors),
            'critical_factors': len([f for f in risk_factors if f['severity'] == 'CRITICAL']),
            'remediation_priorities': [f['remediation'] for f in risk_factors]
        }
    
    def _is_anomalous_value(self, feature_name: str, value: float) -> bool:
        """Check if a feature value is anomalous."""
        thresholds = {
            'Privilege Level': (3, 3),          # Critical privilege
            'Public Access': (0.5, 1),          # Is public
            'Sensitive Resources': (2, float('inf')),  # Multiple sensitive resources
            'Sensitivity Score': (5, float('inf')),    # High sensitivity
            'Principal Diversity': (5, float('inf')),  # Many principals
            'K8s Exposure': (0.5, 1),           # Exposed
            'Volume Sensitivity': (1, float('inf'))    # Sensitive volumes
        }
        
        if feature_name in thresholds:
            lower, upper = thresholds[feature_name]
            return lower <= value <= upper
        
        return False
    
    def _generate_explanation_text(self, high_value_features: Dict,
                                   anomaly_score: float) -> str:
        """Generate human-readable explanation."""
        if not high_value_features:
            return f'Anomaly score {anomaly_score:.2f}: Configuration appears normal based on feature analysis.'
        
        feature_list = ', '.join(high_value_features.keys())
        
        if anomaly_score >= 7:
            return (
                f'Anomaly score {anomaly_score:.2f}: HIGH ANOMALY. '
                f'Detected unusual values in: {feature_list}. '
                f'This configuration significantly deviates from normal patterns.'
            )
        elif anomaly_score >= 4:
            return (
                f'Anomaly score {anomaly_score:.2f}: MEDIUM ANOMALY. '
                f'Detected unusual values in: {feature_list}. '
                f'This configuration shows some deviation from normal patterns.'
            )
        else:
            return (
                f'Anomaly score {anomaly_score:.2f}: LOW ANOMALY. '
                f'Minor deviations detected in: {feature_list}. '
                f'Configuration is mostly normal.'
            )
    
    def _heuristic_importance(self, high_value_features: Dict) -> Dict[str, float]:
        """Calculate importance using heuristic approach."""
        importance = {name: 0.0 for name in self.feature_names}
        
        # Assign importance to detected anomalies
        severity_map = {
            'Public Access': 30,
            'Privilege Level': 25,
            'Sensitive Resources': 20,
            'Sensitivity Score': 15,
            'Principal Diversity': 10
        }
        
        total = 0
        for feature, severity in severity_map.items():
            if feature in high_value_features:
                importance[feature] = severity
                total += severity
        
        # Normalize
        if total > 0:
            importance = {k: (v / total) * 100 if v > 0 else 0 for k, v in importance.items()}
        
        return importance
    
    def _calculate_confidence(self, high_value_features: Dict,
                            anomaly_score: float) -> float:
        """Calculate confidence in the explanation."""
        # More high-value features = higher confidence
        factor_count = len(high_value_features)
        base_confidence = min(0.95, 0.5 + (factor_count * 0.15))
        
        # Score consistency check
        if factor_count > 0 and anomaly_score < 3:
            # Few anomalies but high anomaly score = lower confidence
            base_confidence *= 0.7
        
        return round(base_confidence, 2)
    
    def batch_explain(self, configs: List[Dict[str, Any]],
                     scores: List[float]) -> List[Dict[str, Any]]:
        """Explain multiple configurations at once."""
        explanations = []
        
        for config, score in zip(configs, scores):
            explanation = self.explain_risk_score(config, score)
            explanations.append(explanation)
        
        return explanations
    
    def create_feature_importance_summary(self, 
                                         explanations: List[Dict]) -> Dict[str, Any]:
        """Create summary of feature importances across multiple configs."""
        feature_total = {name: 0.0 for name in self.feature_names}
        count = 0
        
        for exp in explanations:
            for name, importance in exp.get('feature_importance', {}).items():
                if name in feature_total:
                    feature_total[name] += importance
                    count += 1
        
        # Calculate averages
        avg_importance = {
            name: total / count if count > 0 else 0
            for name, total in feature_total.items()
        }
        
        # Sort by importance
        sorted_importance = dict(sorted(
            avg_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return {
            'feature_importance_avg': sorted_importance,
            'top_features': list(sorted_importance.keys())[:5],
            'bottom_features': list(sorted_importance.keys())[-3:]
        }
