"""
Remediation Suggestions Engine

Provides actionable remediation recommendations based on detected security issues.
"""

from typing import Dict, List, Any


class RemediationEngine:
    """Generate remediation suggestions for security issues."""
    
    def __init__(self):
        self.remediation_rules = self._build_remediation_rules()
    
    def _build_remediation_rules(self) -> List[Dict[str, Any]]:
        """Build rule-based remediation suggestions."""
        return [
            {
                'pattern': 'public_exposure',
                'condition': lambda cfg: cfg.get('is_public', False),
                'suggestions': [
                    'Remove public access from configuration (Principal: *)',
                    'Restrict access to specific principal identities',
                    'Add IP allowlist restrictions instead of open access',
                    'Require authentication and authorization',
                    'Enable access logs for audit trail'
                ],
                'severity': 'CRITICAL'
            },
            {
                'pattern': 'wildcard_permissions',
                'condition': lambda cfg: '*' in str(cfg.get('actions', [])),
                'suggestions': [
                    'Apply principle of least privilege: replace * with specific actions',
                    'List only required permissions (e.g., s3:GetObject, s3:PutObject)',
                    'Create separate roles for different permission levels',
                    'Regularly audit and remove unused permissions',
                    'Use condition keys to further restrict access'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'sensitive_resources_unprotected',
                'condition': lambda cfg: len(cfg.get('sensitive_resources', [])) > 0,
                'suggestions': [
                    'Encrypt sensitive resources at rest and in transit',
                    'Implement encryption key management and rotation',
                    'Apply additional access controls to sensitive data',
                    'Enable MFA for access to sensitive resources',
                    'Use temporary credentials with short expiry times'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'privilege_escalation_risk',
                'condition': lambda cfg: cfg.get('privilege_level') in ['critical', 'high'],
                'suggestions': [
                    'Apply principle of least privilege to reduce attack surface',
                    'Separate admin and user roles',
                    'Implement role-based access control (RBAC)',
                    'Require approval workflow for privilege escalation',
                    'Monitor and audit privilege usage'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'missing_conditions',
                'condition': lambda cfg: not cfg.get('conditions'),
                'suggestions': [
                    'Add condition restrictions to limit access scope',
                    'Restrict by IP address/CIDR ranges',
                    'Add time-based access restrictions',
                    'Require MFA or specific protocols',
                    'Limit access to specific platforms/regions'
                ],
                'severity': 'MEDIUM'
            },
            {
                'pattern': 'k8s_privileged_container',
                'condition': lambda cfg: any(c.get('privileged') for c in cfg.get('containers', [])),
                'suggestions': [
                    'Remove privileged: true from security context',
                    'Use capabilities instead of full privilege',
                    'Add securityContext with read-only root filesystem',
                    'Drop dangerous Linux capabilities',
                    'Use AppArmor or SELinux profiles'
                ],
                'severity': 'CRITICAL'
            },
            {
                'pattern': 'k8s_run_as_root',
                'condition': lambda cfg: any(c.get('run_as_root') for c in cfg.get('containers', [])),
                'suggestions': [
                    'Set runAsNonRoot: true in securityContext',
                    'Specify runAsUser with non-zero UID',
                    'Set runAsGroup for group-based access',
                    'Use fsGroup for volume permissions',
                    'Add SecurityPolicy to enforce this cluster-wide'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'k8s_host_path_mount',
                'condition': lambda cfg: any('host_path' in str(v) for v in cfg.get('volumes', [])),
                'suggestions': [
                    'Replace hostPath with emptyDir for temporary storage',
                    'Use persistent volumes (PV) for data storage',
                    'If hostPath required, restrict to specific paths',
                    'Use allowedHostPaths in PodSecurityPolicy',
                    'Enable audit logging for hostPath access'
                ],
                'severity': 'CRITICAL'
            },
            {
                'pattern': 'k8s_exposed_service',
                'condition': lambda cfg: cfg.get('network_exposure', {}).get('is_exposed', False),
                'suggestions': [
                    'Restrict Service type to ClusterIP if not needed externally',
                    'Use NetworkPolicy to limit traffic sources',
                    'Implement API gateway or service mesh for external access',
                    'Add authentication/authorization at ingress layer',
                    'Monitor and audit external access'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'weak_rbac',
                'condition': lambda cfg: cfg.get('kind') == 'ClusterRoleBinding',
                'suggestions': [
                    'Use RoleBinding (namespaced) instead of ClusterRoleBinding when possible',
                    'Limit subjects to specific service accounts',
                    'Audit who has cluster admin roles',
                    'Implement RBAC best practices (least privilege)',
                    'Use admission controllers to prevent privilege escalation'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'plaintext_secrets_in_env',
                'condition': lambda cfg: any(
                    any(s in str(ev.get('name', '')).lower()
                        for s in ['password', 'secret', 'api_key', 'apikey', 'token', 'access_key'])
                    for c in cfg.get('containers', [])
                    for ev in (c.get('env_vars') or [])
                    if isinstance(ev, dict)
                ),
                'suggestions': [
                    'Move credentials to a Kubernetes Secret resource (kind: Secret)',
                    'Reference secrets via valueFrom.secretKeyRef in env vars',
                    'Enable encryption at rest for etcd to protect Secret values',
                    'Use external secret managers (HashiCorp Vault, AWS Secrets Manager, Sealed Secrets)',
                    'Rotate any credential that appeared in plaintext in version control'
                ],
                'severity': 'HIGH'
            },
            {
                'pattern': 'externally_exposed_service_no_tls',
                'condition': lambda cfg: (
                    cfg.get('network_exposure', {}).get('is_exposed', False)
                    and cfg.get('network_exposure', {}).get('service_type') in ('LoadBalancer', 'NodePort')
                ),
                'suggestions': [
                    'Terminate TLS at an Ingress controller (e.g., nginx-ingress) instead of plain LoadBalancer',
                    'Use cert-manager for automatic Let\'s Encrypt certificate issuance',
                    'Apply a NetworkPolicy that restricts traffic to known CIDRs',
                    'Place the service behind an API gateway with WAF rules',
                    'Switch to Service type ClusterIP if external traffic is not actually required'
                ],
                'severity': 'MEDIUM'
            },
            {
                'pattern': 'public_storage_acl',
                'condition': lambda cfg: (
                    cfg.get('policy_type', '').lower() in ('bucket', 'storage', 'unknown')
                    and cfg.get('is_public', False)
                    and any('s3' in str(a).lower() or 'storage' in str(a).lower() or '*' == str(a)
                            for a in (cfg.get('actions') or []))
                ),
                'suggestions': [
                    'Disable public ACLs on the bucket and enable Block Public Access',
                    'Replace bucket policy Principal: "*" with specific AWS account IDs or roles',
                    'Use pre-signed URLs for time-limited public read access instead of permanent ACLs',
                    'Enable bucket logging and versioning for audit and recovery',
                    'Turn on default server-side encryption (SSE-S3 or SSE-KMS)'
                ],
                'severity': 'CRITICAL'
            }
        ]
    
    def generate_suggestions(self, config_analysis: Dict[str, Any], 
                            risk_score: float) -> Dict[str, Any]:
        """
        Generate remediation suggestions for a configuration.
        
        Args:
            config_analysis: Result from ConfigParser
            risk_score: Risk score from RiskScoringEngine
        
        Returns:
            Dict with grouped remediation suggestions
        """
        suggestions = []
        severity_groups = {}
        
        # Apply remediation rules
        for rule in self.remediation_rules:
            try:
                if rule['condition'](config_analysis):
                    severity = rule['severity']
                    if severity not in severity_groups:
                        severity_groups[severity] = {
                            'pattern': rule['pattern'],
                            'suggestions': rule['suggestions'],
                            'severity': severity
                        }
            except:
                # Skip rules that error
                pass
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        suggestions = sorted(
            severity_groups.values(),
            key=lambda x: severity_order.get(x['severity'], 4)
        )
        
        # Add general recommendations based on risk level
        general_recommendations = self._get_general_recommendations(risk_score)
        
        return {
            'risk_score': risk_score,
            'total_issues': len(suggestions),
            'critical_issues': len([s for s in suggestions if s['severity'] == 'CRITICAL']),
            'recommendations_by_severity': suggestions,
            'general_recommendations': general_recommendations,
            'action_plan': self._create_action_plan(suggestions)
        }
    
    def _get_general_recommendations(self, risk_score: float) -> List[str]:
        """Get general recommendations based on risk level."""
        if risk_score >= 9.0:
            return [
                '⚠️ CRITICAL: This configuration poses severe security risks',
                'Immediately restrict access and implement recommended mitigations',
                'Consider disabling this configuration until addressed',
                'Notify security team and compliance officers',
                'Document current access and who deployed this'
            ]
        elif risk_score >= 6.0:
            return [
                '⚠️ HIGH RISK: Multiple security issues detected',
                'Implement remediation suggestions within 24-48 hours',
                'Review who currently has access',
                'Consider limiting scope temporarily',
                'Schedule security review of this configuration'
            ]
        elif risk_score >= 3.0:
            return [
                '⚠️ MEDIUM RISK: Some security concerns identified',
                'Review and implement relevant suggestions',
                'Monitor usage patterns for anomalies',
                'Plan for improvements in next review cycle',
                'Educate team on security best practices'
            ]
        else:
            return [
                '✓ LOW RISK: Configuration appears reasonably secure',
                'Continue monitoring and regular audits',
                'Follow principle of least privilege',
                'Document any exceptions to security policies'
            ]
    
    def _create_action_plan(self, suggestions: List[Dict]) -> List[Dict[str, str]]:
        """Create prioritized action plan."""
        action_plan = []
        priority = 1
        
        for suggestion in suggestions:
            for rec in suggestion['suggestions'][:2]:  # Top 2 recommendations per severity
                action_plan.append({
                    'priority': priority,
                    'severity': suggestion['severity'],
                    'issue': suggestion['pattern'],
                    'action': rec
                })
                priority += 1
        
        return action_plan[:10]  # Top 10 actions
    
    def remediate_specific_issue(self, issue_type: str, config: Dict) -> List[str]:
        """Get remediation for a specific issue type."""
        for rule in self.remediation_rules:
            if rule['pattern'] == issue_type:
                return rule['suggestions']
        
        return ['Unable to find specific remediation for this issue type']
    
    def batch_remediation(self, configs_with_scores: List[Dict]) -> Dict[str, Any]:
        """Generate remediation for multiple configs."""
        all_issues = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        total_critical_actions = 0
        
        for config in configs_with_scores:
            remediation = self.generate_suggestions(
                config.get('config_analysis', {}),
                config.get('risk_score', 0)
            )
            
            for rec in remediation['recommendations_by_severity']:
                severity = rec['severity']
                all_issues[severity].append({
                    'config': config.get('config_id', 'unknown'),
                    'pattern': rec['pattern'],
                    'suggestions': rec['suggestions']
                })
                
                if severity == 'CRITICAL':
                    total_critical_actions += 1
        
        return {
            'total_configs_analyzed': len(configs_with_scores),
            'issues_by_severity': {k: len(v) for k, v in all_issues.items()},
            'critical_action_items': total_critical_actions,
            'issues_detail': all_issues,
            'overall_recommendation': self._get_overall_recommendation(all_issues)
        }
    
    def _get_overall_recommendation(self, all_issues: Dict) -> str:
        """Get overall recommendation based on issues."""
        if all_issues['CRITICAL']:
            return 'HALT AND REMEDIATE: Critical security issues detected. Immediate action required.'
        elif all_issues['HIGH']:
            return 'URGENT: Multiple high-risk issues. Implement remediation within 48 hours.'
        elif all_issues['MEDIUM']:
            return 'REVIEW: Implement recommendations during next maintenance window.'
        else:
            return 'COMPLIANT: Configuration meets basic security standards. Continue monitoring.'
