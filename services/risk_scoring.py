"""
Advanced Risk Scoring Engine

Combines multiple factors for comprehensive risk assessment:
- Anomaly Score (from ML models)
- Impact Factor (privilege level, resource sensitivity)
- Sensitivity Score (keyword detection)
- Public Exposure Factor

Improvements over v1:
- Fixed formula normalization (sensitivity × impact no longer blows past 10)
- Word-boundary regex matching to cut false positives on keywords like 'key'
- Scans config values separately from keys to avoid key-name inflation
- Anomaly auto-derivation uses distinct signals (no double-counting)
- Every result includes `triggered_rules` list for UI explanation
- `score_batch` catches per-item errors without crashing the whole batch
- `calculate_risk_score` accepts optional `ml_anomaly_score` for ML pipeline integration
"""

import re
import numpy as np
from typing import Dict, List, Any, Optional


class RiskScoringEngine:
    """Advanced risk assessment combining ML and domain knowledge."""

    # Sensitivity weights for keywords (matched with word-boundary regex)
    SENSITIVITY_KEYWORDS = {
        'secret': 10,
        'password': 10,
        'passwd': 10,
        'token': 9,
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
        'pii': 10,
        # NOTE: bare 'key' removed — too noisy (sort_key, foreign_key, etc.)
        # Use api_key / private_key / secret_key instead
    }

    # Pre-compiled word-boundary patterns for performance
    _KEYWORD_PATTERNS: Dict[str, re.Pattern] = {}

    # Impact factors by privilege level
    PRIVILEGE_IMPACT = {
        'critical': 3.0,
        'high': 2.5,
        'medium': 1.5,
        'low': 1.0,
    }

    PUBLIC_EXPOSURE_MULTIPLIER = 3.0

    def __init__(self):
        self.risk_threshold_critical = 8.5
        self.risk_threshold_high = 7.0
        self.risk_threshold_medium = 4.0
        self.risk_threshold_low = 2.5

        # Build regex patterns once at init
        for keyword in self.SENSITIVITY_KEYWORDS:
            self._KEYWORD_PATTERNS[keyword] = re.compile(
                r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_values_from_config(self, raw_config: Any) -> str:
        """
        Recursively extract leaf values from a nested config dict/list.
        Returns a single string of values to scan for sensitive keywords.
        Avoids inflating scores by scanning key names.
        """
        if isinstance(raw_config, dict):
            parts = []
            for v in raw_config.values():
                parts.append(self._extract_values_from_config(v))
            return ' '.join(parts)
        elif isinstance(raw_config, list):
            return ' '.join(self._extract_values_from_config(item) for item in raw_config)
        else:
            return str(raw_config)

    # ------------------------------------------------------------------
    # Score components
    # ------------------------------------------------------------------

    def calculate_sensitivity_score(self, text: str) -> float:
        """
        Calculate sensitivity score based on keyword detection.
        Uses word-boundary regex to reduce false positives.

        Args:
            text: Config values string (use _extract_values_from_config)

        Returns:
            Sensitivity score (0–10)
        """
        if not text:
            return 0.0

        total_score = 0.0
        keyword_count = 0

        for keyword, weight in self.SENSITIVITY_KEYWORDS.items():
            pattern = self._KEYWORD_PATTERNS[keyword]
            occurrences = len(pattern.findall(text))
            if occurrences > 0:
                score = weight * np.log1p(occurrences)
                total_score += score
                keyword_count += 1

        if keyword_count > 0:
            return min(10.0, total_score / keyword_count)

        return 0.0

    def calculate_impact_factor(
        self,
        privilege_level: str,
        is_public: bool,
        sensitive_resources_count: int,
    ) -> float:
        """
        Calculate impact factor based on privilege and scope.

        Returns:
            Impact factor (0–10)
        """
        base_impact = self.PRIVILEGE_IMPACT.get(privilege_level.lower(), 1.0)

        if is_public:
            base_impact *= self.PUBLIC_EXPOSURE_MULTIPLIER

        resource_impact = min(3.0, sensitive_resources_count * 0.5)
        base_impact += resource_impact

        return min(10.0, base_impact)

    def calculate_anomaly_score(
        self,
        is_statistical_anomaly: bool,
        baseline_deviation: bool,
        ml_anomaly_score: float = 0.0,
    ) -> float:
        """
        Calculate anomaly score from multiple ML signals.

        Args:
            is_statistical_anomaly: Isolation Forest detection
            baseline_deviation: Deviates from learned baseline
            ml_anomaly_score: Raw ML score (0–1)

        Returns:
            Anomaly score (0–10)
        """
        score = 0.0

        if is_statistical_anomaly:
            score += 5.0
        if baseline_deviation:
            score += 3.0

        # ML score normalized to 0–2
        score += ml_anomaly_score * 2

        return min(10.0, score)

    # ------------------------------------------------------------------
    # Rule-based overrides
    # ------------------------------------------------------------------

    def _apply_rule_based_overrides(
        self, config_analysis: Dict[str, Any]
    ) -> tuple[float, list[str]]:
        """
        Apply rule-based detection for obvious critical misconfigurations.

        Returns:
            (minimum_risk_score, list_of_triggered_rule_descriptions)

        Rule Priority (highest wins):
        1. Wildcard Principal + Action + Resource  → 10.0 CRITICAL
        2. Wildcard Principal + (Action OR Resource) → 9.5 CRITICAL
        3. Privileged container (securityContext.privileged=true) → 9.0 CRITICAL
        4. Wildcard Principal OR Wildcard Action → 8.5 CRITICAL
        5. Wildcard Resource + Public → 7.5 HIGH
        6. Admin/critical privilege + Public → 8.5 CRITICAL
        7. Container running as root → 7.0 HIGH
        """
        principal = config_analysis.get('principal', [])
        actions = config_analysis.get('actions', [])
        resources = config_analysis.get('resources', [])
        privilege_level = config_analysis.get('privilege_level', 'low').lower()
        is_public = config_analysis.get('is_public', False)
        containers = config_analysis.get('containers', [])

        if isinstance(principal, str):
            principal = [principal]
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]

        has_wildcard_principal = '*' in principal or any('*' in str(p) for p in principal)
        has_wildcard_action = '*' in actions or any('*' in str(a) for a in actions)
        has_wildcard_resource = '*' in resources or any('*' in str(r) for r in resources)

        triggered_rules: list[str] = []

        # Rule 1
        if has_wildcard_principal and has_wildcard_action and has_wildcard_resource:
            triggered_rules.append(
                "RULE-1: Wildcard principal, action, and resource — full unrestricted access granted"
            )
            return 10.0, triggered_rules

        # Rule 2
        if has_wildcard_principal and (has_wildcard_action or has_wildcard_resource):
            triggered_rules.append(
                "RULE-2: Wildcard principal combined with wildcard action or resource"
            )
            return 9.5, triggered_rules

        # Rule 3
        privileged_containers = [
            c.get('name', 'unnamed') for c in containers if c.get('privileged', False)
        ]
        if privileged_containers:
            triggered_rules.append(
                f"RULE-3: Container(s) running in privileged mode: {', '.join(privileged_containers)}"
            )
            return 9.0, triggered_rules

        # Rule 4
        if has_wildcard_principal:
            triggered_rules.append("RULE-4: Wildcard principal — any identity can assume this role")
        if has_wildcard_action:
            triggered_rules.append("RULE-4: Wildcard action — all operations permitted")
        if triggered_rules:
            return 8.5, triggered_rules

        # Rule 5
        if has_wildcard_resource and is_public:
            triggered_rules.append(
                "RULE-5: Wildcard resource scope on a publicly accessible policy"
            )
            return 7.5, triggered_rules

        # Rule 5b — Wildcard action on critical/admin privilege (NOT public)
        # Catches single-user over-privileged policies like s3:* + dynamodb:* + iam:PassRole
        if has_wildcard_action and ('admin' in privilege_level or 'critical' in privilege_level):
            triggered_rules.append(
                f"RULE-5b: Wildcard action with {privilege_level} privilege level — over-privileged policy"
            )
            return 7.5, triggered_rules

        # Rule 6
        if ('admin' in privilege_level or 'critical' in privilege_level) and is_public:
            triggered_rules.append(
                f"RULE-6: {privilege_level.title()} privilege level on a publicly accessible resource"
            )
            return 8.5, triggered_rules

        # Rule 6b — Sensitive secrets in env vars (K8s)
        env_secret_count = 0
        for c in containers:
            for ev in (c.get('env_vars') or []):
                key = (ev.get('name') if isinstance(ev, dict) else str(ev)) or ''
                if any(s in key.lower() for s in ['password', 'secret', 'api_key', 'apikey', 'token', 'access_key']):
                    env_secret_count += 1
        if env_secret_count > 0:
            triggered_rules.append(
                f"RULE-6b: {env_secret_count} plaintext secret(s) detected in container env vars — should use Secret resource"
            )
            return 6.0, triggered_rules

        # Rule 6c — Externally exposed K8s service (LoadBalancer/NodePort) without NetworkPolicy
        net = config_analysis.get('network_exposure') or {}
        if net.get('is_exposed') and net.get('service_type') in ('LoadBalancer', 'NodePort'):
            triggered_rules.append(
                f"RULE-6c: K8s {net.get('service_type')} service is externally exposed — verify NetworkPolicy / TLS"
            )
            return 5.5, triggered_rules

        # Rule 7
        root_containers = [
            c.get('name', 'unnamed') for c in containers if c.get('run_as_root', False)
        ]
        if root_containers:
            triggered_rules.append(
                f"RULE-7: Container(s) running as root: {', '.join(root_containers)}"
            )
            return 7.0, triggered_rules

        return 0.0, []

    # ------------------------------------------------------------------
    # Main scoring
    # ------------------------------------------------------------------

    def calculate_risk_score(
        self,
        config_analysis: Dict[str, Any],
        ml_anomaly_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score.

        Formula:
            formula_score = (anomaly_score/10 * 0.4) + (sensitivity_score/10 * impact_factor/10 * 0.6)
            final_score   = max(rule_based_minimum, formula_score) * 10

        Both sensitivity and impact are normalized to 0–1 before multiplication,
        so the product can never exceed 1 and the composite stays in 0–10.

        Args:
            config_analysis: Result from ConfigParser
            ml_anomaly_score: Optional ML-based anomaly score (0–10).
                              If None, a proxy is derived from config signals
                              that are DISTINCT from impact_factor inputs.

        Returns:
            Dict with risk_score, risk_level, component breakdown, and
            triggered_rules list for UI display.
        """
        privilege_level = config_analysis.get('privilege_level', 'low')
        is_public = config_analysis.get('is_public', False)
        sensitive_resources = config_analysis.get('sensitive_resources', [])
        raw_config = config_analysis.get('raw_config', {})
        conditions = config_analysis.get('conditions')

        # --- Step 1: Rule-based overrides ---
        rule_based_minimum, triggered_rules = self._apply_rule_based_overrides(config_analysis)

        # --- Step 2: Sensitivity (values only, not key names) ---
        values_text = self._extract_values_from_config(raw_config)
        sensitivity_score = self.calculate_sensitivity_score(values_text)

        # --- Step 3: Impact factor ---
        impact_factor = self.calculate_impact_factor(
            privilege_level,
            is_public,
            len(sensitive_resources),
        )

        # --- Step 4: Anomaly score ---
        # If an ML score is provided, use it directly.
        # Otherwise derive a proxy from signals NOT already in impact_factor:
        #   - absence of conditions/restrictions (policy hygiene)
        #   - sensitivity keyword density (high keyword density is unusual)
        # Note: is_public and privilege_level are intentionally EXCLUDED here
        # because they are already captured in impact_factor, preventing double-counting.
        if ml_anomaly_score is not None:
            anomaly_score = float(np.clip(ml_anomaly_score, 0.0, 10.0))
            anomaly_source = 'ml_provided'
        else:
            anomaly_score = 0.0
            if not conditions:
                anomaly_score += 4.0   # No conditions = broader-than-expected scope
            if sensitive_resources:
                anomaly_score += min(3.0, len(sensitive_resources) * 0.75)
            if sensitivity_score > 6.0:
                anomaly_score += 3.0   # Very high keyword density is anomalous
            anomaly_score = float(np.clip(anomaly_score, 0.0, 10.0))
            anomaly_source = 'auto_derived'

        # --- Step 5: Normalized composite formula ---
        # Normalize all components to 0–1 before combining
        norm_anomaly = anomaly_score / 10.0
        norm_sensitivity = sensitivity_score / 10.0
        norm_impact = impact_factor / 10.0

        formula_risk_score = (norm_anomaly * 0.4 + norm_sensitivity * norm_impact * 0.6) * 10.0
        formula_risk_score = float(np.clip(formula_risk_score, 0.0, 10.0))

        # --- Step 6: Apply rule-based floor ---
        final_risk_score = float(np.clip(max(rule_based_minimum, formula_risk_score), 0.0, 10.0))

        # --- Step 7: Risk level ---
        if final_risk_score >= self.risk_threshold_critical:
            risk_level = 'CRITICAL'
        elif final_risk_score >= self.risk_threshold_high:
            risk_level = 'HIGH'
        elif final_risk_score >= self.risk_threshold_medium:
            risk_level = 'MEDIUM'
        elif final_risk_score >= self.risk_threshold_low:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'

        # Build remediation hints from triggered rules
        remediation = _build_remediation_hints(triggered_rules, config_analysis)

        return {
            'risk_score': round(final_risk_score, 2),
            'risk_level': risk_level,
            'anomaly_score': round(anomaly_score, 2),
            'anomaly_source': anomaly_source,
            'impact_factor': round(impact_factor, 2),
            'sensitivity_score': round(sensitivity_score, 2),
            'triggered_rules': triggered_rules,           # Human-readable explanations
            'remediation': remediation,                   # Suggested fixes
            'components': {
                'privilege_level': privilege_level,
                'is_public': is_public,
                'sensitive_resources_count': len(sensitive_resources),
                'sensitive_resources': sensitive_resources[:5],
                'rule_based_override': round(rule_based_minimum, 2),
                'formula_score': round(formula_risk_score, 2),
            },
        }

    # ------------------------------------------------------------------
    # Batch scoring
    # ------------------------------------------------------------------

    def score_batch(
        self,
        configs: List[Dict[str, Any]],
        ml_anomaly_scores: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple configurations. Errors per config are caught and
        returned as an 'error' field rather than crashing the whole batch.

        Args:
            configs: List of config_analysis dicts
            ml_anomaly_scores: Optional mapping of config id → ML anomaly score

        Returns:
            List sorted by risk_score descending.
        """
        ml_anomaly_scores = ml_anomaly_scores or {}
        results = []

        for config in configs:
            config_id = config.get('id', 'unknown')
            config_name = config.get('policy_type', 'unnamed')
            try:
                ml_score = ml_anomaly_scores.get(config_id)
                risk = self.calculate_risk_score(config, ml_anomaly_score=ml_score)
                results.append({
                    'config_id': config_id,
                    'config_name': config_name,
                    **risk,
                })
            except Exception as exc:  # noqa: BLE001
                results.append({
                    'config_id': config_id,
                    'config_name': config_name,
                    'risk_score': 0.0,
                    'risk_level': 'ERROR',
                    'error': str(exc),
                })

        results.sort(key=lambda x: x['risk_score'], reverse=True)
        return results

    def get_risk_distribution(self, scored_configs: List[Dict]) -> Dict[str, int]:
        """Get distribution of risk levels across a scored batch."""
        distribution = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0, 'ERROR': 0}
        for config in scored_configs:
            level = config.get('risk_level', 'MINIMAL')
            if level in distribution:
                distribution[level] += 1
        return distribution


# ------------------------------------------------------------------
# Remediation helper (module-level to keep the class clean)
# ------------------------------------------------------------------

def _build_remediation_hints(
    triggered_rules: List[str],
    config_analysis: Dict[str, Any],
) -> List[str]:
    """
    Map triggered rules and config signals to concrete remediation suggestions.
    Returns a list of actionable fix strings for the UI.
    """
    hints: List[str] = []
    rule_ids = {r.split(':')[0] for r in triggered_rules}

    if 'RULE-1' in rule_ids or 'RULE-2' in rule_ids:
        hints.append("Replace wildcard principal ('*') with specific IAM identities or roles.")
        hints.append("Replace wildcard actions ('*') with the minimum required action set.")
        hints.append("Replace wildcard resources ('*') with explicit ARNs or resource paths.")

    if 'RULE-3' in rule_ids:
        hints.append("Remove `securityContext.privileged: true` from container spec.")
        hints.append("Use specific Linux capabilities instead of full privileged mode.")

    if 'RULE-4' in rule_ids:
        hints.append("Scope the principal to specific service accounts or user identities.")
        hints.append("Enumerate only the required actions rather than allowing all operations.")

    if 'RULE-5' in rule_ids:
        hints.append("Restrict resource scope to specific ARNs before exposing publicly.")

    if 'RULE-6' in rule_ids:
        hints.append("Administrative access should not be granted on publicly reachable resources.")
        hints.append("Apply least-privilege: reduce privilege level or remove public access.")

    if 'RULE-7' in rule_ids:
        hints.append("Set `securityContext.runAsNonRoot: true` and specify a non-zero `runAsUser`.")

    if not config_analysis.get('conditions'):
        hints.append("Add conditions (e.g., IP allowlist, MFA required, time restrictions) to narrow the policy scope.")

    if config_analysis.get('is_public') and not triggered_rules:
        hints.append("Review whether public access is required; restrict to known IPs or authenticated identities if possible.")

    return hints