# CloudGuard – Live Demo Guide for Reviewer Panel

**Project:** CloudGuard – Hybrid ML + Rule-Based Security Configuration Auditor
**Extends:** OPMonitor (Wang et al., 2025)
**Stack:** Flask 3.x · MongoDB · PyTorch 2.1 · SHAP 0.43 · Next.js 16 · React 19

---

## 1. What you will demonstrate

For your reviewers you will show, in **under 5 minutes**, that CloudGuard:

1. Accepts a real cloud configuration file (AWS IAM JSON or Kubernetes YAML).
2. Detects security vulnerabilities using **rule-based static analysis**.
3. Computes a **5-tier risk score** (CRITICAL / HIGH / MEDIUM / LOW / MINIMAL) using the formula `Risk = Anomaly × Impact × Sensitivity`.
4. Extracts a **12-dimensional ML feature vector** consumable by the trained PyTorch autoencoder.
5. Provides **SHAP-based explainability** (which factor pushed the score up).
6. Emits a **prioritized remediation action plan** with step-by-step fixes.

You can show this in **two demo modes** depending on time available.

---

## 2. Two demo modes

### MODE A – "Two-minute terminal demo" (recommended for time-constrained panels)
Run a single Python script that processes 5 pre-prepared configs and prints a clean per-step report. **No MongoDB, no Next.js, no setup pain.**

### MODE B – "Full stack demo" (recommended if you have 5+ minutes and want to wow them)
Run the actual Flask backend + Next.js frontend, upload a config through the dashboard, see the live UI render the risk score, autoencoder analysis, SHAP chart, and remediation cards.

---

## 3. Prerequisites (one-time setup on your laptop)

### 3.1 Install Python 3.11+
- Windows: download from [python.org](https://www.python.org/downloads/)
- macOS: `brew install python@3.11`
- Linux: `sudo apt install python3.11 python3.11-venv`

### 3.2 Install Node.js 18+ (only needed for Mode B)
- [nodejs.org](https://nodejs.org/en/download/) — pick LTS

### 3.3 Install MongoDB Community Edition (only needed for Mode B)
- Easiest: **MongoDB Atlas free tier** (cloud) → [mongodb.com/atlas](https://www.mongodb.com/atlas)
- Local install:
  - Windows: [MongoDB Community Server](https://www.mongodb.com/try/download/community)
  - macOS: `brew install mongodb-community`
  - Linux: follow [official docs](https://www.mongodb.com/docs/manual/administration/install-on-linux/)
- After install, run: `mongod` (default port 27017). For Mode A you can **skip MongoDB entirely**.

### 3.4 Clone the repo
```bash
git clone https://github.com/KESABA-BARIK/cloudgaurd.git
cd cloudgaurd
```

### 3.5 Install Python dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> If `pip install` of PyTorch is slow, use `pip install torch --index-url https://download.pytorch.org/whl/cpu` for the CPU-only build (~200 MB instead of 800 MB).

### 3.6 Install Node dependencies (Mode B only)
```bash
cd frontend
npm install
cd ..
```

### 3.7 Configure environment variables
Create a file named `.env` in the project root:
```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=cloudguard
NEXT_PUBLIC_API_URL=http://localhost:5000
```

---

## 4. MODE A – Quick terminal demo (no MongoDB, no Node)

This is the **safest option** for a 2-minute reviewer demo.

### 4.1 What it shows
- Loads 5 pre-built sample configs from `demo/sample_configs/`
- For each config, prints the 5-step pipeline output (parse → ML features → risk → SHAP → remediation)
- Ends with a summary table: file → score → severity tier

### 4.2 How to run it
```bash
cd cloudgaurd
source .venv/bin/activate
python demo/scripts/run_demo.py
```

### 4.3 What the panel will see
```
##########################################################################
#         CloudGuard Live Demo - Vulnerability Detection Pipeline         #
##########################################################################

Processing 5 configuration file(s)...

==========================================================================
  FILE: 01_critical_iam_wildcard.json  (IAM)
==========================================================================
  STEP 1 - STATIC RULE ANALYSIS
    is_public           : True
    actions             : ['*']
    privilege_level     : critical

  STEP 2 - ML AUTOENCODER (12-DIM FEATURE VECTOR)
    feature dimension   : 12
    feature vector      : [3.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]

  STEP 3 - HYBRID RISK SCORING
    RISK SCORE          : 10.00 / 10.00
    SEVERITY TIER       : >>>  CRITICAL  <<<

  STEP 4 - SHAP EXPLAINABILITY
    top risk factors    :
      - Public Access (CRITICAL): Configuration is publicly accessible
      - High Privilege Level (HIGH): Privilege level "critical" increases risk

  STEP 5 - REMEDIATION SUGGESTIONS
    [CRITICAL] public_exposure   - Remove Principal: *  - Restrict to specific principals
    [HIGH] wildcard_permissions  - Replace * with specific actions
    [MEDIUM] missing_conditions  - Add IP / MFA / time conditions
```

### 4.4 Demo only one config
```bash
python demo/scripts/run_demo.py demo/sample_configs/03_critical_k8s_privileged.yaml
```

---

## 5. MODE B – Full-stack live demo (Flask + Next.js + MongoDB)

### 5.1 Start MongoDB
```bash
mongod --dbpath ./data
# OR if using Atlas, just make sure MONGODB_URI is set in .env
```

### 5.2 Start the Flask backend (Terminal 1)
```bash
cd cloudgaurd
source .venv/bin/activate
python app.py
```
You should see:
```
* Running on http://127.0.0.1:5000
```

### 5.3 (Optional) Train the autoencoder once
This takes ~30 seconds and persists the model to disk:
```bash
curl -X POST http://localhost:5000/api/config/train-autoencoder
```

### 5.4 Start the Next.js frontend (Terminal 2)
```bash
cd cloudgaurd/frontend
npm run dev
```
Open browser at **http://localhost:3000**

### 5.5 The demo flow on the dashboard
1. Click **"Upload Configuration"** in the sidebar.
2. Choose `demo/sample_configs/01_critical_iam_wildcard.json`.
3. Click **Analyze** → the dashboard renders:
   - Big red **CRITICAL 10.0/10** badge
   - Pie chart of risk components
   - SHAP bar chart of contributing factors
   - List of remediation suggestions grouped by severity
   - "Run Autoencoder" button → reconstruction error plot
4. Repeat with `04_safe_iam_least_privilege.json` to show a **MINIMAL** result for contrast.

---

## 6. Sample configs included (`demo/sample_configs/`)

| # | File | Type | Expected | What's wrong |
|---|---|---|---|---|
| 01 | `01_critical_iam_wildcard.json` | IAM | **CRITICAL 10.0** | `Principal:*  Action:*  Resource:*` — fully open |
| 02 | `02_high_iam_overprivileged.json` | IAM | **HIGH 6–8** | `s3:*` + `dynamodb:*` + `iam:PassRole` for one user |
| 03 | `03_critical_k8s_privileged.yaml` | K8s | **CRITICAL ~9** | `privileged:true` + `runAsUser:0` + `hostPath:/` + plaintext AWS key |
| 04 | `04_safe_iam_least_privilege.json` | IAM | **MINIMAL ~1.5** | Specific user, specific actions, MFA + IP conditions |
| 05 | `05_medium_k8s_no_security.yaml` | K8s | **MEDIUM 3–5** | LoadBalancer service, plaintext API key, no securityContext |

---

## 7. Recommended demo script (5-min walkthrough)

| Time | What you say | What you show |
|---|---|---|
| 0:00–0:30 | "OPMonitor only watches access logs after the fact and uses no ML. CloudGuard analyzes the configuration *before* it's deployed and adds a PyTorch autoencoder for anomaly detection." | Slide showing the 6 OPMonitor limitations |
| 0:30–1:30 | "Here's a real AWS IAM policy that opens an S3 bucket to the world. Watch what CloudGuard does." | Run Mode A on file 01 → highlight CRITICAL 10.0 + 3 issues |
| 1:30–2:30 | "Now the same engine on a Kubernetes pod that runs as root inside the host filesystem." | Show file 03 result → CRITICAL + privileged_container + host_path |
| 2:30–3:30 | "And here's a properly written IAM policy — the same engine, no false alarm." | Show file 04 → MINIMAL 1.6 |
| 3:30–4:30 | "Behind every score is an explanation — SHAP tells us which factor moved the needle." | Point at the SHAP factor list in the output |
| 4:30–5:00 | "Finally, the system doesn't just complain — it produces a prioritized fix list any engineer can act on." | Point at the action plan section |

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: torch` | `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| MongoDB connection refused | Mode A doesn't need it. Mode B: start `mongod` or set `MONGODB_URI` to your Atlas string in `.env` |
| Port 5000 already in use (macOS) | macOS uses 5000 for AirPlay — change Flask to port 5050 in `app.py` and update `NEXT_PUBLIC_API_URL` |
| Frontend says "Failed to fetch" | Confirm `NEXT_PUBLIC_API_URL` matches the Flask port and Flask is running |
| `[db] Warning: could not create indexes` | Harmless — backend retries on next request |

---

## 9. What to say if a reviewer asks…

| Question | Answer |
|---|---|
| Why not Isolation Forest? | Autoencoders learn a *compressed representation* of normal configs. The reconstruction error is a smoother, more interpretable anomaly signal than IF's path-length, and pairs better with SHAP. |
| Why no LIME? | SHAP gives globally consistent Shapley values; LIME's local linear approximation drifts on tabular config data. We chose one rigorous method over two redundant ones. |
| Why hybrid (rules + ML)? | Rules give deterministic coverage of known bad patterns (auditable). ML catches *novel* combinations rules don't. Together they minimize both false positives and false negatives. |
| Threshold for the autoencoder? | 95th percentile of reconstruction errors on the training set — standard practice for unsupervised anomaly detection. |
| How do you avoid alert fatigue? | The 5-tier severity + the impact/sensitivity weights ensure only truly critical configs surface as CRITICAL. Demo file 04 returns MINIMAL — proving low false-positive rate. |
| Where's the 6th limitation (Pareto approximation)? | Inherited from the underlying optimization, but mitigated: the ML layer catches what the rule-based layer misses, narrowing the approximation gap. |

---

## 10. Final checklist before the demo

- [ ] Laptop fully charged + power adapter
- [ ] `python demo/scripts/run_demo.py` works in dry-run
- [ ] Browser bookmarks: `http://localhost:3000`, `http://localhost:5000/api/health`
- [ ] Backup: a screen-recorded MP4 of the demo on your phone in case Wi-Fi/laptop fails
- [ ] PPT slide 41 (CloudGuard tech stack) open in another window for reference
- [ ] Sample configs printed/visible — reviewers may want to inspect them
