"""
Advanced Risk Scoring Engine

Combines multiple factors for comprehensive risk assessment:
- Anomaly Score (from ML models)
- Impact Factor (privilege level, resource sensitivity)
- Sensitivity Score (keyword detection)
- Public Exposure Factor
"""

import numpy as np
from typing import Dict, List, Any


class RiskScoringEngine:
    """Advanced risk assessment combining ML and domain knowledge."""
    
    # Sensitivity weights for keywords
    SENSITIVITY_KEYWORDS = {
        'secret': 10,
        'password': 10,
        'token': 9,
        'key': 8,
        'api_key': 10,
        'apikey': 10,
        'admin': 8,
        'root': 9,
        'private': 7,
        'confidential': 7,
        'credential': 9,
        'certificate': 7,
        'cert': 7,
        'pem': 8,
        'ssh': 8,
        'aws_secret': 10,
        'encryption': 6,
        'database': 8,
        'prod': 7,
        'production': 7,
        'credit_card': 10,
        'ssn': 10,
        'pii': 10
    }
    
    # Impact factors by privilege level
    PRIVILEGE_IMPACT = {
        'critical': 3.0,    # Full admin access
        'high': 2.5,        # Write/modify access
        'medium': 1.5,      # Read access
        'low': 1.0          # Limited access
    }
    
    # Public exposure penalties
    PUBLIC_EXPOSURE_MULTIPLIER = 3.0
    
    def __init__(self):
        self.risk_threshold_low = 2.5
        self.risk_threshold_medium = 4.0
        self.risk_threshold_high = 7.0
        self.risk_threshold_critical = 8.5
    
    def calculate_sensitivity_score(self, text: str) -> float:
        """
        Calculate sensitivity score based on keyword detection.
        
        Args:
            text: Configuration text or resource string
        
        Returns:
            Sensitivity score (0-10)
        """
        if not text:
            return 0.0
        
        text_lower = str(text).lower()
        total_score = 0.0
        keyword_count = 0
        
        for keyword, weight in self.SENSITIVITY_KEYWORDS.items():
            # Count occurrences
            occurrences = text_lower.count(keyword)
            if occurrences > 0:
                # Log scale for multiple occurrences
                score = weight * np.log1p(occurrences)
                total_score += score
                keyword_count += 1
        
        # Normalize to 0-10 range
        if keyword_count > 0:
            return min(10.0, total_score / keyword_count)
        
        return 0.0
    
    def calculate_impact_factor(self, privilege_level: str, 
                               is_public: bool, 
                               sensitive_resources_count: int) -> float:
        """
        Calculate impact factor based on privilege and scope.
        
        Args:
            privilege_level: 'critical', 'high', 'medium', 'low'
            is_public: Whether accessible to public
            sensitive_resources_count: Number of sensitive resources accessed
        
        Returns:
            Impact factor (0-10)
        """
        base_impact = self.PRIVILEGE_IMPACT.get(privilege_level, 1.0)
        
        # Public exposure multiplier
        if is_public:
            base_impact *= self.PUBLIC_EXPOSURE_MULTIPLIER
        
        # Sensitive resources add to impact
        resource_impact = min(3.0, sensitive_resources_count * 0.5)
        base_impact += resource_impact
        
        return min(10.0, base_impact)
    
    def calculate_anomaly_score(self, 
                               is_statistical_anomaly: bool,
                               baseline_deviation: bool,
                               ml_anomaly_score: float = 0.0) -> float:
        """
        Calculate anomaly score from multiple signals.
        
        Args:
            is_statistical_anomaly: Isolation Forest detection
            baseline_deviation: Deviates from learned baseline
            ml_anomaly_score: Raw ML score (0-1)
        
        Returns:
            Anomaly score (0-10)
        """
        score = 0.0
        
        if is_statistical_anomaly:
            score += 5.0
        
        if baseline_deviation:
            score += 3.0
        
        # Add ML score (normalized to 0-2)
        score += ml_anomaly_score * 2
        
        return min(10.0, score)
    
    def calculate_risk_score(self,
                           config_analysis: Dict[str, Any],
                           anomaly_score: float = None) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score using formula:
        Risk Score = Anomaly Score × Impact Factor × Sensitivity Score
        
        Args:
            config_analysis: Result from ConfigParser
            anomaly_score: ML-based anomaly score (0-10), or None to auto-detect
        
        Returns:
            Dict with risk score and breakdown
        """
        # Extract components
        privilege_level = config_analysis.get('privilege_level', 'low')
        is_public = config_analysis.get('is_public', False)
        sensitive_resources = config_analysis.get('sensitive_resources', [])
        raw_config = config_analysis.get('raw_config', {})
        
        # Calculate individual scores
        sensitivity_score = self.calculate_sensitivity_score(
            str(raw_config)
        )
        
        impact_factor = self.calculate_impact_factor(
            privilege_level,
            is_public,
            len(sensitive_resources)
        )
        
        # Auto-detect anomaly score from config features if not provided
        if anomaly_score is None:
            # Derive anomaly score from config characteristics
            anomaly_score = 0.0
            
            # Increase for public exposure
            if is_public:
                anomaly_score += 4.0
            
            # Increase for high privilege
            if privilege_level in ['high', 'critical']:
                anomaly_score += 3.0
            
            # Increase for sensitive resources
            if sensitive_resources:
                anomaly_score += 2.0
            
            # Increase if has no conditions/restrictions
            if not config_analysis.get('conditions'):
                anomaly_score += 1.0
        
        # Ensure anomaly score is in valid range
        anomaly_score = max(0.0, min(10.0, anomaly_score))
        
        # Calculate composite risk score using weighted sum instead of product
        # This ensures sensitivity_score and impact_factor still contribute when anomaly_score=0
        risk_score = (anomaly_score * 0.4 + sensitivity_score * impact_factor * 0.6)
        
        # Normalize to 0-10 range
        risk_score = min(10.0, max(0.0, risk_score))
        
        # Determine risk level
        if risk_score >= self.risk_threshold_critical:
            risk_level = 'CRITICAL'
        elif risk_score >= self.risk_threshold_high:
            risk_level = 'HIGH'
        elif risk_score >= self.risk_threshold_medium:
            risk_level = 'MEDIUM'
        elif risk_score >= self.risk_threshold_low:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'anomaly_score': round(anomaly_score, 2),
            'impact_factor': round(impact_factor, 2),
            'sensitivity_score': round(sensitivity_score, 2),
            'components': {
                'privilege_level': privilege_level,
                'is_public': is_public,
                'sensitive_resources_count': len(sensitive_resources),
                'sensitive_resources': sensitive_resources[:5]  # Top 5
            }
        }
    
    def score_batch(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple configurations."""
        results = []
        
        for config in configs:
            risk = self.calculate_risk_score(config)
            results.append({
                'config_id': config.get('id', 'unknown'),
                'config_name': config.get('policy_type', 'unnamed'),
                **risk
            })
        
        # Sort by risk score
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return results
    
    def get_risk_distribution(self, scored_configs: List[Dict]) -> Dict[str, int]:
        """Get distribution of risk levels."""
        distribution = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'MINIMAL': 0
        }
        
        for config in scored_configs:
            level = config.get('risk_level', 'MINIMAL')
            if level in distribution:
                distribution[level] += 1
        
        return distribution
