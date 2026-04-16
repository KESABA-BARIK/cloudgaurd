"""
Cloud Configuration Parser

Parses IAM policies (JSON) and Kubernetes manifests (YAML) to extract security-relevant features.
Handles AWS IAM, GCP IAM, Azure RBAC, and basic Kubernetes manifests.
"""

import json
import yaml
from typing import Dict, List, Any, Tuple


class ConfigParser:
    """Parser for cloud configurations (IAM, Kubernetes, etc)."""
    
    # Sensitive keywords for detection
    SENSITIVE_KEYWORDS = [
        'secret', 'password', 'token', 'key', 'api_key', 'apikey',
        'admin', 'root', 'private', 'confidential', 'credential',
        'certificate', 'cert', 'pem', 'ssh', 'aws_secret',
        'encryption', 'database', 'prod', 'production'
    ]
    
    def __init__(self):
        self.parsed_configs = []
    
    def parse_json_config(self, config_text: str) -> Dict[str, Any]:
        """Parse JSON configuration (e.g., IAM policy)."""
        try:
            return json.loads(config_text)
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON: {str(e)}'}
    
    def parse_yaml_config(self, config_text: str) -> Dict[str, Any]:
        """Parse YAML configuration (e.g., Kubernetes manifest)."""
        try:
            return yaml.safe_load(config_text)
        except yaml.YAMLError as e:
            return {'error': f'Invalid YAML: {str(e)}'}
    
    def extract_iam_features(self, policy: Dict) -> Dict[str, Any]:
        """
        Extract features from IAM policy.
        
        Detects:
        - Principal (who can access)
        - Actions (what they can do)
        - Resources (what they access)
        - Conditions (restrictions)
        - Public exposure (Principal: *)
        - Privilege level (admin vs limited)
        """
        features = {
            'policy_type': policy.get('PolicyName', 'unknown'),
            'principal': self._extract_principals(policy),
            'actions': self._extract_actions(policy),
            'resources': self._extract_resources(policy),
            'conditions': self._extract_conditions(policy),
            'is_public': self._check_public_exposure(policy),
            'privilege_level': self._calculate_privilege_level(policy),
            'sensitive_resources': self._check_sensitive_resources(policy),
        }
        return features
    
    def extract_k8s_features(self, manifest: Dict) -> Dict[str, Any]:
        """
        Extract features from Kubernetes manifest.
        
        Detects:
        - Resource type (Pod, Deployment, etc)
        - Container security context
        - RBAC bindings
        - Sensitive mounts (secrets, host path)
        - Network policies
        """
        features = {
            'kind': manifest.get('kind', 'Unknown'),
            'name': manifest.get('metadata', {}).get('name', 'unknown'),
            'namespace': manifest.get('metadata', {}).get('namespace', 'default'),
            'containers': self._extract_k8s_containers(manifest),
            'security_context': manifest.get('spec', {}).get('securityContext', {}),
            'volumes': self._extract_k8s_volumes(manifest),
            'rbac_permissions': self._extract_rbac(manifest),
            'network_exposure': self._check_k8s_exposure(manifest),
            'sensitive_mounts': self._check_k8s_sensitive_mounts(manifest),
        }
        return features
    
    def _extract_principals(self, policy: Dict) -> List[str]:
        """Extract principals from policy."""
        principals = []
        
        # AWS format
        if 'Statement' in policy:
            for stmt in policy.get('Statement', []):
                principal = stmt.get('Principal', {})
                if isinstance(principal, dict):
                    principals.extend(principal.values())
                elif isinstance(principal, str):
                    principals.append(principal)
        
        # GCP/Azure format
        if 'members' in policy:
            principals.extend(policy.get('members', []))
        
        return principals
    
    def _extract_actions(self, policy: Dict) -> List[str]:
        """Extract actions/permissions from policy."""
        actions = []
        
        if 'Statement' in policy:
            for stmt in policy.get('Statement', []):
                action = stmt.get('Action', stmt.get('action', []))
                if isinstance(action, list):
                    actions.extend(action)
                else:
                    actions.append(action)
        
        if 'permissions' in policy:
            actions.extend(policy.get('permissions', []))
        
        return actions
    
    def _extract_resources(self, policy: Dict) -> List[str]:
        """Extract resources from policy."""
        resources = []
        
        if 'Statement' in policy:
            for stmt in policy.get('Statement', []):
                resource = stmt.get('Resource', stmt.get('resource', []))
                if isinstance(resource, list):
                    resources.extend(resource)
                else:
                    resources.append(resource)
        
        return resources
    
    def _extract_conditions(self, policy: Dict) -> Dict[str, Any]:
        """Extract condition restrictions."""
        conditions = {}
        
        if 'Statement' in policy:
            for stmt in policy.get('Statement', []):
                if 'Condition' in stmt:
                    conditions.update(stmt['Condition'])
        
        return conditions
    
    def _check_public_exposure(self, policy: Dict) -> bool:
        """Check if policy allows public access (Principal: *)."""
        principals = self._extract_principals(policy)
        
        for principal in principals:
            if principal == '*' or principal == 'allUsers' or principal == 'allAuthenticatedUsers':
                return True
        
        return False
    
    def _calculate_privilege_level(self, policy: Dict) -> str:
        """
        Calculate privilege level based on actions.
        
        Returns: 'critical', 'high', 'medium', 'low'
        """
        actions = self._extract_actions(policy)
        
        critical_actions = ['*', 'iam:*', 'admin', 'root', 'delete', 'modify']
        high_actions = ['write', 'create', 'update', 'put']
        medium_actions = ['read', 'get', 'list']
        
        action_str = ' '.join(actions).lower()
        
        if any(a.lower() in action_str for a in critical_actions):
            return 'critical'
        if any(a.lower() in action_str for a in high_actions):
            return 'high'
        if any(a.lower() in action_str for a in medium_actions):
            return 'medium'
        
        return 'low'
    
    def _check_sensitive_resources(self, policy: Dict) -> List[str]:
        """Identify sensitive resources in policy."""
        resources = self._extract_resources(policy)
        sensitive = []
        
        for resource in resources:
            resource_lower = str(resource).lower()
            if any(keyword in resource_lower for keyword in self.SENSITIVE_KEYWORDS):
                sensitive.append(resource)
        
        return sensitive
    
    def _extract_k8s_containers(self, manifest: Dict) -> List[Dict]:
        """Extract container info from Kubernetes manifest."""
        containers = []
        
        # Check Pod spec
        spec = manifest.get('spec', {})
        
        # For Deployment, DaemonSet, StatefulSet
        if 'template' in spec:
            spec = spec['template'].get('spec', {})
        
        for container in spec.get('containers', []):
            containers.append({
                'name': container.get('name', 'unknown'),
                'image': container.get('image', 'unknown'),
                'privileged': container.get('securityContext', {}).get('privileged', False),
                'run_as_root': container.get('securityContext', {}).get('runAsUser', 0) == 0,
                'env_vars': self._extract_env_secrets(container),
            })
        
        return containers
    
    def _extract_env_secrets(self, container: Dict) -> List[str]:
        """Extract secret references from environment variables."""
        secrets = []
        
        for env in container.get('env', []):
            if 'valueFrom' in env and 'secretKeyRef' in env.get('valueFrom', {}):
                secrets.append(env.get('valueFrom', {}).get('secretKeyRef', {}).get('name', 'unknown'))
        
        return secrets
    
    def _extract_k8s_volumes(self, manifest: Dict) -> List[Dict]:
        """Extract volume information."""
        volumes = []
        
        spec = manifest.get('spec', {})
        if 'template' in spec:
            spec = spec['template'].get('spec', {})
        
        for volume in spec.get('volumes', []):
            vol_info = {
                'name': volume.get('name', 'unknown'),
                'type': list(volume.keys())[1] if len(volume) > 1 else 'unknown',
                'is_sensitive': False
            }
            
            # Check for secret volumes
            if 'secret' in volume:
                vol_info['is_sensitive'] = True
                vol_info['secret_name'] = volume['secret'].get('secretName', 'unknown')
            
            # Check for hostPath (dangerous)
            if 'hostPath' in volume:
                vol_info['is_sensitive'] = True
                vol_info['host_path'] = volume['hostPath'].get('path', 'unknown')
            
            volumes.append(vol_info)
        
        return volumes
    
    def _extract_rbac(self, manifest: Dict) -> Dict[str, Any]:
        """Extract RBAC information from RoleBinding/ClusterRoleBinding."""
        rbac = {
            'role_ref': manifest.get('roleRef', {}),
            'subjects': manifest.get('subjects', []),
            'rules': manifest.get('rules', [])
        }
        
        return rbac
    
    def _check_k8s_exposure(self, manifest: Dict) -> Dict[str, Any]:
        """Check for network exposure (Services, Ingress)."""
        kind = manifest.get('kind', '')
        exposure = {
            'is_exposed': False,
            'type': None,
            'port': None
        }
        
        if kind == 'Service':
            service_type = manifest.get('spec', {}).get('type', 'ClusterIP')
            if service_type in ['LoadBalancer', 'NodePort']:
                exposure['is_exposed'] = True
                exposure['type'] = service_type
                exposure['port'] = manifest.get('spec', {}).get('ports', [{}])[0].get('port')
        
        if kind == 'Ingress':
            exposure['is_exposed'] = True
            exposure['type'] = 'Ingress'
        
        return exposure
    
    def _check_k8s_sensitive_mounts(self, manifest: Dict) -> List[str]:
        """Check for sensitive volume mounts."""
        sensitive = []
        volumes = self._extract_k8s_volumes(manifest)
        
        for vol in volumes:
            if vol.get('is_sensitive'):
                sensitive.append(vol.get('name', 'unknown'))
        
        return sensitive
    
    def analyze_config(self, config_text: str, config_type: str = 'auto') -> Dict[str, Any]:
        """
        Analyze configuration and return extracted features.
        
        Args:
            config_text: Configuration as string
            config_type: 'iam', 'k8s', 'auto' (auto-detect)
        
        Returns:
            Dict with extracted features and risk indicators
        """
        # Auto-detect config type
        if config_type == 'auto':
            config_type = self._detect_config_type(config_text)
        
        # Parse configuration
        if config_type in ['iam', 'json']:
            config = self.parse_json_config(config_text)
        elif config_type in ['k8s', 'yaml']:
            config = self.parse_yaml_config(config_text)
        else:
            return {'error': f'Unknown config type: {config_type}'}
        
        if 'error' in config:
            return config
        
        # Extract features based on type
        if config_type in ['iam', 'json']:
            features = self.extract_iam_features(config)
        else:  # k8s, yaml
            features = self.extract_k8s_features(config)
        
        features['config_type'] = config_type
        features['raw_config'] = config
        
        return features
    
    def _detect_config_type(self, config_text: str) -> str:
        """Auto-detect configuration type based on content."""
        content_lower = config_text.lower()
        
        # Check for Kubernetes indicators
        if any(k in content_lower for k in ['kind:', 'apiversion:', 'metadata:', 'spec:']):
            return 'k8s'
        
        # Check for IAM indicators
        if any(i in content_lower for i in ['statement', 'principal', 'action', 'resource']):
            return 'iam'
        
        # Try to parse as JSON first
        try:
            json.loads(config_text)
            return 'iam'
        except:
            pass
        
        # Default to YAML/K8s
        return 'k8s'
