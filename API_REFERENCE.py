"""
QUICK API REFERENCE GUIDE
Cloud Configuration Analysis System

This guide provides practical examples for all endpoints.
"""

# ============================================================================
# 1. UPLOAD CONFIGURATION
# ============================================================================

POST_UPLOAD_REQUEST = """
POST /api/config/upload
Content-Type: application/json

Request Body:
{
  "config_type": "iam" | "k8s" | "auto",
  "config_name": "my-policy",
  "config_text": "JSON or YAML content as string",
  "environment": "prod" | "staging" | "dev",
  "tags": ["security", "aws"]
}

Example - IAM Policy:
{
  "config_type": "iam",
  "config_name": "s3-admin-policy",
  "config_text": "{\\"Statement\\": [{\\"Effect\\": \\"Allow\\", \\"Principal\\": \\"*\\", \\"Action\\": \\"s3:*\\", \\"Resource\\": \\"*\\"}]}",
  "environment": "prod"
}

Response (201 Created):
{
  "message": "Configuration uploaded successfully",
  "config_id": "507f1f77bcf86cd799439011",
  "config_name": "s3-admin-policy",
  "config_type": "iam",
  "parsed_features": {
    "privilege_level": "critical",
    "is_public": true,
    "sensitive_resources_count": 2
  }
}
"""

# ============================================================================
# 2. SCAN CONFIGURATIONS
# ============================================================================

POST_SCAN_REQUEST = """
POST /api/config/scan
Content-Type: application/json

Request Body:
{
  "config_ids": ["id1", "id2", "id3"] or null to scan all unanalyzed,
  "run_autoencoder": true | false
}

Example - Scan Specific:
{
  "config_ids": ["507f1f77bcf86cd799439011"],
  "run_autoencoder": true
}

Response (200 OK):
{
  "scan_results": [
    {
      "config_id": "507f1f77bcf86cd799439011",
      "config_name": "s3-admin-policy",
      "risk_score": {
        "risk_score": 8.5,
        "risk_level": "HIGH",
        "anomaly_score": 6.2,
        "impact_factor": 2.8,
        "sensitivity_score": 5.4,
        "components": {
          "privilege_level": "critical",
          "is_public": true,
          "sensitive_resources_count": 2
        }
      },
      "remediation": {
        "risk_score": 8.5,
        "total_issues": 4,
        "critical_issues": 2,
        "recommendations_by_severity": [
          {
            "severity": "CRITICAL",
            "pattern": "public_exposure",
            "suggestions": [
              "Remove public access from configuration (Principal: *)",
              "Restrict access to specific principal identities",
              "Add IP allowlist restrictions instead of open access",
              "Require authentication and authorization",
              "Enable access logs for audit trail"
            ]
          },
          {
            "severity": "HIGH",
            "pattern": "wildcard_permissions",
            "suggestions": [
              "Apply principle of least privilege: replace * with specific actions",
              "List only required permissions (e.g., s3:GetObject, s3:PutObject)",
              "Create separate roles for different permission levels"
            ]
          }
        ],
        "general_recommendations": [
          "⚠️ CRITICAL: This configuration poses severe security risks",
          "Immediately restrict access and implement recommended mitigations",
          "Consider disabling this configuration until addressed"
        ],
        "action_plan": [
          {
            "priority": 1,
            "severity": "CRITICAL",
            "issue": "public_exposure",
            "action": "Remove public access from configuration (Principal: *)"
          },
          {
            "priority": 2,
            "severity": "HIGH",
            "issue": "wildcard_permissions",
            "action": "Apply principle of least privilege: replace * with specific actions"
          }
        ]
      },
      "explanation": {
        "risk_score": 8.5,
        "risk_factors": [
          {
            "factor": "Public Access",
            "severity": "CRITICAL",
            "contribution": "Configuration is publicly accessible",
            "remediation": "Restrict access to specific principals only"
          },
          {
            "factor": "High Privilege Level",
            "severity": "HIGH",
            "contribution": "Privilege level \\"critical\\" increases risk",
            "remediation": "Apply principle of least privilege"
          }
        ],
        "total_factors": 2,
        "critical_factors": 1,
        "remediation_priorities": [
          "Restrict access to specific principals only",
          "Apply principle of least privilege"
        ]
      },
      "anomaly_detection": {
        "reconstruction_error": 0.0852,
        "anomaly_score": 7.5,
        "is_anomaly": true
      }
    }
  ],
  "summary": {
    "risk_distribution": {
      "CRITICAL": 1,
      "HIGH": 2,
      "MEDIUM": 1,
      "LOW": 0,
      "MINIMAL": 0
    },
    "total_critical_issues": 5,
    "highest_risk_config": {...}
  },
  "total_configs": 1,
  "configs_analyzed": 1
}
"""

# ============================================================================
# 3. LIST CONFIGURATIONS
# ============================================================================

GET_LIST_REQUEST = """
GET /api/config/list?environment=prod&risk_level=HIGH&analyzed=true

Query Parameters (all optional):
- environment: "prod" | "staging" | "dev"
- risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL"
- analyzed: "true" | "false"

Response (200 OK):
{
  "configs": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "name": "s3-admin-policy",
      "config_type": "iam",
      "environment": "prod",
      "risk_level": "HIGH",
      "risk_score": 8.5,
      "uploaded_at": "2026-04-16T10:30:00.000000",
      "analyzed": true
    },
    {
      "_id": "507f1f77bcf86cd799439012",
      "name": "risky-k8s-deployment",
      "config_type": "k8s",
      "environment": "prod",
      "risk_level": "CRITICAL",
      "risk_score": 9.2,
      "uploaded_at": "2026-04-16T11:00:00.000000",
      "analyzed": true
    }
  ],
  "total": 2
}
"""

# ============================================================================
# 4. GET CONFIGURATION DETAILS
# ============================================================================

GET_DETAIL_REQUEST = """
GET /api/config/507f1f77bcf86cd799439011?include_raw=false

Query Parameters (optional):
- include_raw: "true" | "false" (include full config text)

Response (200 OK):
{
  "config_id": "507f1f77bcf86cd799439011",
  "name": "s3-admin-policy",
  "config_type": "iam",
  "environment": "prod",
  "tags": ["security", "aws"],
  "uploaded_at": "2026-04-16T10:30:00",
  "analyzed": true,
  "risk_level": "HIGH",
  "risk_score": 8.5,
  "last_analyzed": "2026-04-16T10:35:00",
  "analysis": {
    "config_type": "iam",
    "privilege_level": "critical",
    "principal": ["*"],
    "actions": ["s3:*"],
    "resources": ["arn:aws:s3:::bucket/*"],
    "is_public": true,
    "sensitive_resources": ["arn:aws:secretsmanager:*:*:secret/*"],
    "conditions": {}
  },
  "remediation": {...full remediation object...},
  "explanation": {...full explanation object...}
}
"""

# ============================================================================
# 5. GET REMEDIATION PLAN
# ============================================================================

GET_REMEDIATION_REQUEST = """
GET /api/config/507f1f77bcf86cd799439011/remediation

Response (200 OK):
{
  "config_id": "507f1f77bcf86cd799439011",
  "config_name": "s3-admin-policy",
  "risk_level": "HIGH",
  "remediation": {
    "risk_score": 8.5,
    "total_issues": 4,
    "critical_issues": 2,
    "recommendations_by_severity": [
      {
        "severity": "CRITICAL",
        "pattern": "public_exposure",
        "suggestions": [
          "Remove public access from configuration (Principal: *)",
          "Restrict access to specific principal identities",
          "Add IP allowlist restrictions instead of open access",
          "Require authentication and authorization",
          "Enable access logs for audit trail"
        ]
      },
      ...
    ],
    "general_recommendations": [
      "⚠️ CRITICAL: This configuration poses severe security risks",
      "Immediately restrict access and implement recommended mitigations",
      "Consider disabling this configuration until addressed",
      "Notify security team and compliance officers",
      "Document current access and who deployed this"
    ],
    "action_plan": [
      {
        "priority": 1,
        "severity": "CRITICAL",
        "issue": "public_exposure",
        "action": "Remove public access from configuration (Principal: *)"
      },
      ...
    ]
  }
}
"""

# ============================================================================
# 6. EXPORT SUMMARY REPORT
# ============================================================================

POST_EXPORT_REQUEST = """
POST /api/config/export/summary
Content-Type: application/json

Request Body:
{
  "format": "json" | "csv" | "html",
  "include_details": true | false
}

Response (200 OK) - JSON:
{
  "generated_at": "2026-04-16T12:00:00.000000",
  "total_configs": 15,
  "risk_distribution": {
    "CRITICAL": 2,
    "HIGH": 5,
    "MEDIUM": 6,
    "LOW": 2,
    "MINIMAL": 0
  },
  "by_environment": {
    "prod": {"count": 10, "critical": 2},
    "staging": {"count": 3, "critical": 0},
    "dev": {"count": 2, "critical": 0}
  },
  "recommendations": {
    "public_exposure": 2,
    "wildcard_permissions": 8,
    "sensitive_resources_unprotected": 5,
    ...
  }
}

Response (200 OK) - CSV:
Config ID,Name,Risk Level,Risk Score,Environment
507f1f77bcf86cd799439011,s3-admin-policy,HIGH,8.5,prod
507f1f77bcf86cd799439012,k8s-risky,CRITICAL,9.2,prod
...
"""

# ============================================================================
# 7. TRAIN AUTOENCODER
# ============================================================================

POST_TRAIN_AUTOENCODER = """
POST /api/config/train-autoencoder
Content-Type: application/json

Request Body:
{
  "config_ids": ["id1", "id2", "id3", ...],  // Configs known to be normal/secure
  "epochs": 50,
  "learning_rate": 0.001
}

Example:
{
  "config_ids": ["507f1f77bcf86cd799439001", "507f1f77bcf86cd799439002"],
  "epochs": 100,
  "learning_rate": 0.0005
}

Response (200 OK):
{
  "message": "Autoencoder trained successfully",
  "configs_used": 10,
  "model_info": {
    "status": "trained",
    "input_dim": 12,
    "encoding_dim": 6,
    "total_parameters": 2048,
    "threshold": 0.0852,
    "mean_training_error": 0.0245,
    "max_training_error": 0.1823
  },
  "training_epochs": 100
}

Note: After training, subsequent /api/config/scan calls with
      'run_autoencoder': true will use this trained model.
"""

# ============================================================================
# PYTHON CLIENT EXAMPLE
# ============================================================================

PYTHON_CLIENT_EXAMPLE = """
import requests
import json

BASE_URL = "http://localhost:5000/api"

class ConfigAnalysisClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def upload_config(self, config_type, config_name, config_text, environment, tags=[]):
        response = requests.post(
            f"{self.base_url}/config/upload",
            json={
                "config_type": config_type,
                "config_name": config_name,
                "config_text": config_text,
                "environment": environment,
                "tags": tags
            }
        )
        return response.json()
    
    def scan_configs(self, config_ids=None, run_autoencoder=False):
        response = requests.post(
            f"{self.base_url}/config/scan",
            json={
                "config_ids": config_ids,
                "run_autoencoder": run_autoencoder
            }
        )
        return response.json()
    
    def list_configs(self, environment=None, risk_level=None, analyzed=None):
        params = {}
        if environment:
            params["environment"] = environment
        if risk_level:
            params["risk_level"] = risk_level
        if analyzed is not None:
            params["analyzed"] = "true" if analyzed else "false"
        
        response = requests.get(
            f"{self.base_url}/config/list",
            params=params
        )
        return response.json()
    
    def get_config_detail(self, config_id, include_raw=False):
        response = requests.get(
            f"{self.base_url}/config/{config_id}",
            params={"include_raw": "true" if include_raw else "false"}
        )
        return response.json()
    
    def get_remediation(self, config_id):
        response = requests.get(f"{self.base_url}/config/{config_id}/remediation")
        return response.json()
    
    def export_summary(self, format="json", include_details=False):
        response = requests.post(
            f"{self.base_url}/config/export/summary",
            json={
                "format": format,
                "include_details": include_details
            }
        )
        return response.text if format == "csv" else response.json()
    
    def train_autoencoder(self, config_ids, epochs=50, learning_rate=0.001):
        response = requests.post(
            f"{self.base_url}/config/train-autoencoder",
            json={
                "config_ids": config_ids,
                "epochs": epochs,
                "learning_rate": learning_rate
            }
        )
        return response.json()


# Usage Example
if __name__ == "__main__":
    client = ConfigAnalysisClient()
    
    # 1. Upload configuration
    iam_policy = json.dumps({
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "*"
        }]
    })
    
    result = client.upload_config(
        "iam",
        "my-policy",
        iam_policy,
        "prod",
        ["security", "aws"]
    )
    config_id = result["config_id"]
    print(f"Uploaded config: {config_id}")
    
    # 2. Scan configuration
    scan_result = client.scan_configs([config_id], run_autoencoder=True)
    risk_level = scan_result["scan_results"][0]["risk_score"]["risk_level"]
    print(f"Risk Level: {risk_level}")
    
    # 3. Get remediation
    remediation = client.get_remediation(config_id)
    for rec in remediation["remediation"]["recommendations_by_severity"]:
        print(f"\\n[{rec['severity']}] {rec['pattern']}")
        for suggestion in rec['suggestions'][:2]:
            print(f"  • {suggestion}")
    
    # 4. List all critical configs
    critical = client.list_configs(risk_level="CRITICAL")
    print(f"\\nCritical configs: {critical['total']}")
    
    # 5. Export report
    summary = client.export_summary(format="json", include_details=True)
    print(f"\\nTotal configs analyzed: {summary['total_configs']}")
"""

# ============================================================================
# BASH/CURL EXAMPLES
# ============================================================================

BASH_EXAMPLES = """
#!/bin/bash

BASE_URL="http://localhost:5000/api"

# 1. Upload configuration
echo "Uploading configuration..."
CONFIG_ID=$(curl -s -X POST $BASE_URL/config/upload \\
  -H "Content-Type: application/json" \\
  -d '{
    "config_type": "iam",
    "config_name": "test-policy",
    "config_text": "{\\"Statement\\": [{\\"Effect\\": \\"Allow\\", \\"Principal\\": \\"*\\", \\"Action\\": \\"s3:*\\", \\"Resource\\": \\"*\\"}]}",
    "environment": "prod"
  }' | jq -r '.config_id')

echo "Config ID: $CONFIG_ID"

# 2. Scan configuration
echo "\\nScanning configuration..."
curl -s -X POST $BASE_URL/config/scan \\
  -H "Content-Type: application/json" \\
  -d "{
    \\"config_ids\\": [\\"$CONFIG_ID\\"],
    \\"run_autoencoder\\": true
  }" | jq '.scan_results[0].risk_score'

# 3. Get remediation
echo "\\nGetting remediation..."
curl -s -X GET $BASE_URL/config/$CONFIG_ID/remediation | jq '.remediation.action_plan'

# 4. List critical configs
echo "\\nListing critical configs..."
curl -s -X GET "$BASE_URL/config/list?risk_level=CRITICAL" | jq '.configs'

# 5. Export summary
echo "\\nExporting summary..."
curl -s -X POST $BASE_URL/config/export/summary \\
  -H "Content-Type: application/json" \\
  -d '{"format": "json", "include_details": false}' | jq '.'
"""

# ============================================================================
# COMMON USE CASES
# ============================================================================

USE_CASES = """
╔════════════════════════════════════════════════════════════════════════════╗
║                         COMMON USE CASES                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

1. SECURITY AUDIT
   ├─ POST /api/config/upload (upload all configs)
   ├─ POST /api/config/scan (analyze all)
   └─ POST /api/config/export/summary (generate report)

2. COMPLIANCE CHECK
   ├─ GET /api/config/list?risk_level=CRITICAL
   ├─ GET /api/config/<id>/remediation (for each critical)
   └─ Create remediation tickets

3. CI/CD INTEGRATION
   ├─ POST /api/config/upload (before deployment)
   ├─ POST /api/config/scan (run analysis)
   ├─ Check risk_score < threshold
   └─ Block or warn if too risky

4. CONTINUOUS MONITORING
   ├─ POST /api/config/train-autoencoder (on known-good configs)
   ├─ Setup periodic scans
   ├─ Alert on new anomalies
   └─ Investigate changes

5. KNOWLEDGE BUILDING
   ├─ Review recommendations_by_severity
   ├─ Understand risk factors
   ├─ Learn from explanations
   └─ Apply fixes proactively

6. REMEDIATION TRACKING
   ├─ Get remediation plan
   ├─ Implement suggested fixes
   ├─ Re-scan configuration
   ├─ Verify risk score improved
   └─ Document compliance

╔════════════════════════════════════════════════════════════════════════════╗
║                          ERROR HANDLING                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

400 Bad Request
├─ Missing required fields
├─ Invalid JSON/YAML
└─ Invalid config IDs

404 Not Found
├─ Config ID doesn't exist
└─ Resource not found

500 Server Error
├─ MongoDB connection
├─ Model training failure
└─ Internal server error

Handling:
1. Always check response status code
2. Parse error message from response
3. Log for debugging
4. Retry with valid input
5. Contact support if persistent
"""

if __name__ == "__main__":
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "CLOUD CONFIGURATION ANALYSIS API - QUICK REFERENCE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n" + "="*80)
    print("API ENDPOINTS")
    print("="*80)
    
    print(POST_UPLOAD_REQUEST)
    print("\n" + "="*80)
    print(POST_SCAN_REQUEST)
    print("\n" + "="*80)
    print(GET_LIST_REQUEST)
    print("\n" + "="*80)
    print(GET_DETAIL_REQUEST)
    print("\n" + "="*80)
    print(GET_REMEDIATION_REQUEST)
    print("\n" + "="*80)
    print(POST_EXPORT_REQUEST)
    print("\n" + "="*80)
    print(POST_TRAIN_AUTOENCODER)
    print("\n" + "="*80)
    print(PYTHON_CLIENT_EXAMPLE)
    print("\n" + "="*80)
    print(BASH_EXAMPLES)
    print("\n" + "="*80)
    print(USE_CASES)
