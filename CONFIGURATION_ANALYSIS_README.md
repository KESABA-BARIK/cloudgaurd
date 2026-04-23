# Cloud Configuration Analysis System

A comprehensive security analysis platform for cloud configurations (IAM policies, Kubernetes manifests) with advanced ML-based anomaly detection and risk scoring.

## Features

### 1. **Cloud Configuration Ingestion** ☁️
- Parse **AWS IAM Policies** (JSON format)
- Parse **Kubernetes Manifests** (YAML format)
- Auto-detect configuration type
- Extract security-relevant features:
  - Principal/Subject information
  - Actions/Permissions granted
  - Resources accessed
  - Conditions/Restrictions
  - Sensitive resource detection

### 2. **Advanced Risk Scoring Engine** 📊
- **Formula**: `Risk Score = Anomaly Score × Impact Factor × Sensitivity Score`
- **Components**:
  - **Anomaly Score**: ML-based statistical anomaly detection (0-10)
  - **Impact Factor**: Privilege level + public exposure + sensitive resources (0-10)
  - **Sensitivity Score**: Keyword-based detection for secrets, credentials, etc. (0-10)
- **Risk Levels**: CRITICAL, HIGH, MEDIUM, LOW, MINIMAL
- **Threshold-based Classification**:
  - CRITICAL: ≥ 9.0
  - HIGH: 6.0 - 9.0
  - MEDIUM: 3.0 - 6.0
  - LOW: 1.0 - 3.0
  - MINIMAL: < 1.0

### 3. **Automated Remediation Suggestions** 🔧
- **Issue Detection Patterns**:
  - ❌ Public exposure (Principal: *)
  - ❌ Wildcard permissions (Action: *)
  - ❌ Unprotected sensitive resources
  - ❌ Privilege escalation risks
  - ❌ Missing access restrictions
  - ❌ Kubernetes security issues:
    - Privileged containers
    - Running as root
    - Host path mounts
    - Exposed services
    - Weak RBAC

- **Remediation Types**:
  - Specific technical recommendations (e.g., "Replace * with specific actions")
  - Implementation guidance
  - Best practice references
  - Prioritized action plan

### 4. **PyTorch Autoencoder for Anomaly Detection** 🤖
- **Architecture**: 3-layer autoencoder (input → 64 → 32 → 64 → output)
- **Feature Space**: 12-dimensional feature vector:
  1. Privilege level (0-3)
  2. Public access (0-1)
  3. Sensitive resources count
  4. Action count
  5. Resource count
  6. Principal count
  7. Condition presence (0-1)
  8. Sensitivity score (0-10)
  9. Resource depth
  10. Principal diversity
  11. K8s exposure (0-1)
  12. Volume sensitivity

- **Training**: MSE loss on normal configurations
- **Anomaly Detection**: Reconstruction error threshold (95th percentile)
- **Output**: Anomaly score (0-10) and binary classification

### 5. **SHAP Explainability** 📈
- **Explains** why configurations are flagged as risky
- **Feature Importance**: Identifies which features most contribute to risk
- **Human-Readable**: Natural language explanations
- **Confidence Scores**: Measures reliability of explanations
- **Visualization Ready**: Compatible with SHAP plotting

### 6. **HTTP API Endpoints** 🌐

#### Upload Configuration
```bash
POST /api/config/upload
Content-Type: application/json

{
  "config_type": "iam | k8s | auto",
  "config_name": "my-policy",
  "config_text": "JSON or YAML content...",
  "environment": "prod | staging | dev",
  "tags": ["security", "prod"]
}

Response:
{
  "config_id": "507f1f77bcf86cd799439011",
  "config_type": "iam",
  "parsed_features": {
    "privilege_level": "critical",
    "is_public": true,
    "sensitive_resources_count": 2
  }
}
```

#### Scan Configurations
```bash
POST /api/config/scan
Content-Type: application/json

{
  "config_ids": ["id1", "id2"] or null,
  "run_autoencoder": true
}

Response:
{
  "scan_results": [
    {
      "config_id": "507f...",
      "config_name": "my-policy",
      "risk_score": {
        "risk_score": 8.5,
        "risk_level": "HIGH",
        "anomaly_score": 6.2,
        "impact_factor": 2.8,
        "sensitivity_score": 5.4
      },
      "remediation": {
        "total_issues": 4,
        "critical_issues": 2,
        "recommendations_by_severity": [...]
      },
      "explanation": {
        "risk_factors": [...],
        "remediation_priorities": [...]
      }
    }
  ],
  "summary": {
    "risk_distribution": {"CRITICAL": 1, "HIGH": 2, ...},
    "total_critical_issues": 5,
    "highest_risk_config": {...}
  }
}
```

#### List Configurations
```bash
GET /api/config/list?environment=prod&risk_level=HIGH&analyzed=true

Response:
{
  "configs": [
    {
      "_id": "507f...",
      "name": "my-policy",
      "config_type": "iam",
      "risk_level": "HIGH",
      "risk_score": 7.2,
      "uploaded_at": "2026-04-16T10:30:00"
    }
  ],
  "total": 15
}
```

#### Get Configuration Details
```bash
GET /api/config/<config_id>?include_raw=false

Response:
{
  "config_id": "507f...",
  "name": "my-policy",
  "config_type": "iam",
  "environment": "prod",
  "risk_level": "HIGH",
  "risk_score": 7.2,
  "analysis": {...},
  "remediation": {...},
  "explanation": {...}
}
```

#### Get Remediation Plan
```bash
GET /api/config/<config_id>/remediation

Response:
{
  "config_id": "507f...",
  "config_name": "my-policy",
  "risk_level": "HIGH",
  "remediation": {
    "critical_issues": 2,
    "recommendations_by_severity": [
      {
        "severity": "CRITICAL",
        "pattern": "public_exposure",
        "suggestions": [
          "Remove public access from configuration (Principal: *)",
          "Restrict access to specific principal identities",
          ...
        ]
      }
    ],
    "action_plan": [...]
  }
}
```

#### Export Summary Report
```bash
POST /api/config/export/summary
Content-Type: application/json

{
  "format": "json | csv | html",
  "include_details": false
}

Response: JSON/CSV report with summary statistics and recommendations
```

#### Train Autoencoder
```bash
POST /api/config/train-autoencoder
Content-Type: application/json

{
  "config_ids": ["id1", "id2", ...],
  "epochs": 50,
  "learning_rate": 0.001
}

Response:
{
  "message": "Autoencoder trained successfully",
  "configs_used": 10,
  "model_info": {
    "total_parameters": 2048,
    "threshold": 0.0852
  }
}
```

## Installation

### Prerequisites
- Python 3.8+
- MongoDB (running on localhost:27017)
- CUDA (optional, for GPU acceleration)

### Setup

1. **Clone/Download the project**

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start MongoDB**
```bash
mongod
```

5. **Run the application**
```bash
python app.py
```

Server will be available at `http://localhost:5000`

## Usage Examples

### Python Client Example
```python
import requests
import json

BASE_URL = "http://localhost:5000/api"

# 1. Upload a configuration
iam_policy = {
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::bucket/*"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/config/upload",
    json={
        "config_type": "iam",
        "config_name": "s3-policy",
        "config_text": json.dumps(iam_policy),
        "environment": "prod"
    }
)

config_id = response.json()["config_id"]
print(f"Uploaded config: {config_id}")

# 2. Scan configuration
response = requests.post(
    f"{BASE_URL}/config/scan",
    json={
        "config_ids": [config_id],
        "run_autoencoder": True
    }
)

results = response.json()
print(f"Risk Level: {results['scan_results'][0]['risk_score']['risk_level']}")
print(f"Risk Score: {results['scan_results'][0]['risk_score']['risk_score']}")

# 3. Get remediation
response = requests.get(f"{BASE_URL}/config/{config_id}/remediation")
remediation = response.json()
print(f"Critical Issues: {remediation['remediation']['critical_issues']}")
```

### Command Line Testing
```bash
# Start server
python app.py

# In another terminal
# Upload and scan a config
curl -X POST http://localhost:5000/api/config/upload \
  -H "Content-Type: application/json" \
  -d @config.json

# List all configs
curl http://localhost:5000/api/config/list

# Get details
curl http://localhost:5000/api/config/<config_id>
```

## Risk Scoring Formula Explained

```
Risk Score = (Anomaly Score × Impact Factor × Sensitivity Score) / 10

Where:

Anomaly Score (0-10):
  = ML Detection + Baseline Deviation + Reconstruction Error
  Detects unusual patterns in configuration

Impact Factor (0-10):
  = Privilege Level × Exposure Multiplier + Resource Sensitivity
  - Critical privilege: 3.0x multiplier
  - Public exposure: 3.0x multiplier
  - Multiple sensitive resources: +0.5 per resource

Sensitivity Score (0-10):
  = Keyword matching for secrets, credentials, admin access
  - Keywords: password, token, secret, key, admin, etc.
  - Logarithmic scale for multiple occurrences
```

## Architecture

```
Frontend (Next.js) ─┐
                   ├─► Flask App ─┐
CLI Tools ─────────┘              ├─► Services ─┐
                                  │             ├─► ConfigParser
                                  │             ├─► RiskScoringEngine
                                  │             ├─► RemediationEngine
                                  │             ├─► AutoencoderAnomalyDetector
                                  │             ├─► SHAPExplainer
                                  │             └─► Baseline Engine
                                  │
                                  └─► MongoDB

Services Flow:
1. Upload → ConfigParser (Extract features)
2. Scan → RiskScoringEngine (Calculate risk)
3. Scan → RemediationEngine (Generate suggestions)
4. Scan → AutoencoderAnomalyDetector (Anomaly score)
5. Scan → SHAPExplainer (Explain predictions)
```

## Database Schema

### configs Collection
```json
{
  "_id": ObjectId,
  "name": String,
  "config_type": String,  // "iam" or "k8s"
  "environment": String,
  "tags": [String],
  "config_text": String,
  "analysis": Object,     // Raw parsed features
  "uploaded_at": DateTime,
  "analyzed": Boolean,
  "risk_score": Number,
  "risk_level": String,
  "remediation": Object,
  "explanation": Object,
  "last_analyzed": DateTime
}

Indexes:
- name
- config_type
- environment
- risk_level
- analyzed
- uploaded_at
```

## Performance Considerations

### Large Batch Processing
```python
# Process multiple configs efficiently
configs = load_all_configs()
results = risk_engine.score_batch(configs)  # Vectorized

# Filter high-risk only
critical = [r for r in results if r['risk_level'] == 'CRITICAL']
```

### Autoencoder Training
- **Training Time**: ~30 seconds for 50 epochs on 100 configs
- **Memory**: ~500MB GPU / 2GB CPU
- **Inference**: ~5ms per config on GPU

### API Limits
- Recommend batching: 50-100 configs per scan request
- Rate limit: Configure via Flask middleware if needed

## Troubleshooting

### MongoDB Connection Error
```
Error: Connection refused
Solution: Ensure mongod is running
mongod --dbpath C:\data\db  # Windows
```

### PyTorch Installation Issues
```
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### YAML Parsing Errors
```
Ensure YAML is properly formatted
Use: yaml.safe_load() for parsing
```

## Future Enhancements

- [ ] Real-time monitoring of cloud configurations
- [ ] Integration with cloud provider APIs (AWS, GCP, Azure)
- [ ] Advanced SHAP visualizations
- [ ] Policy recommendation engine
- [ ] Compliance framework mapping (CIS, PCI-DSS, etc.)
- [ ] Cost optimization analysis
- [ ] Drift detection for configuration changes

## License

MIT License

## Contributing

Contributions welcome! Please follow PEP 8 style guide.

## Support

For issues or questions, create an issue in the repository.
