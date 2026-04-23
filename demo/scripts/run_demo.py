"""
CloudGuard Live Demo Runner
============================
Run end-to-end pipeline on each sample config and print a clean,
reviewer-friendly report. No backend server, no MongoDB needed.

Usage:
    python demo/scripts/run_demo.py
    python demo/scripts/run_demo.py demo/sample_configs/01_critical_iam_wildcard.json
"""

import sys
import os
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.config_parser import ConfigParser
from services.risk_scoring import RiskScoringEngine
from services.remediation import RemediationEngine
from services.shap_explainer import SHAPExplainer

try:
    from services.autoencoder import AutoencoderAnomalyDetector
    HAVE_AE = True
except Exception:
    HAVE_AE = False


def banner(title, char="="):
    print("\n" + char * 72)
    print(f"  {title}")
    print(char * 72)


def detect_type(path):
    return "k8s" if path.lower().endswith((".yaml", ".yml")) else "iam"


def analyze_file(path, parser, scorer, remediator, explainer, detector=None):
    with open(path) as f:
        text = f.read()

    cfg_type = detect_type(path)
    banner(f"FILE: {os.path.basename(path)}  ({cfg_type.upper()})")
    print(text.strip()[:300] + ("..." if len(text) > 300 else ""))

    analysis = parser.analyze_config(text, cfg_type)
    if "error" in analysis:
        print(f"\n[!] Parser error: {analysis['error']}")
        return

    risk = scorer.calculate_risk_score(analysis)
    remed = remediator.generate_suggestions(analysis, risk["risk_score"])

    banner("STEP 1 - STATIC RULE ANALYSIS", "-")
    if cfg_type == "iam":
        print(f"  policy_type        : {analysis.get('policy_type')}")
        print(f"  is_public          : {analysis.get('is_public')}")
        print(f"  actions            : {analysis.get('actions')}")
        print(f"  privilege_level    : {analysis.get('privilege_level')}")
        print(f"  sensitive_resources: {len(analysis.get('sensitive_resources', []))}")
    else:
        print(f"  kind               : {analysis.get('kind')}")
        print(f"  containers         : {len(analysis.get('containers', []))}")
        for c in analysis.get("containers", [])[:2]:
            print(f"    - {c.get('name')}: privileged={c.get('privileged')}, root={c.get('run_as_root')}")
        print(f"  volumes            : {len(analysis.get('volumes', []))}")
        for v in analysis.get("volumes", [])[:2]:
            print(f"    - {v.get('name')}: type={v.get('type')}, sensitive={v.get('is_sensitive')}")
        print(f"  network exposure   : {analysis.get('network_exposure', {}).get('is_exposed')}")

    banner("STEP 2 - ML AUTOENCODER (12-DIM FEATURE VECTOR)", "-")
    if HAVE_AE and detector is not None:
        feats = detector.extract_features(analysis)
        print(f"  feature dimension  : {len(feats)}")
        print(f"  feature vector     : {[round(float(x), 2) for x in feats]}")
        print("  (in production, this would feed the trained autoencoder")
        print("   and produce a reconstruction error vs. learned threshold)")
    else:
        print("  [PyTorch not installed - skipping autoencoder demo]")
        print("  In production: 12-D feature vector -> Autoencoder -> reconstruction error")

    banner("STEP 3 - HYBRID RISK SCORING", "-")
    print(f"  RISK SCORE         : {risk['risk_score']:.2f} / 10.00")
    print(f"  SEVERITY TIER      : >>>  {risk['risk_level']}  <<<")
    print(f"  formula            : Anomaly x Impact x Sensitivity")
    print(f"  impact_factor      : {risk.get('impact_factor')}")
    print(f"  sensitivity_score  : {risk.get('sensitivity_score')}")
    components = risk.get("components", {})
    if components:
        print(f"  component breakdown:")
        for k, v in components.items():
            try:
                print(f"    - {k:25s} = {float(v):.2f}")
            except Exception:
                print(f"    - {k:25s} = {v}")

    banner("STEP 4 - SHAP EXPLAINABILITY", "-")
    explanation = explainer.explain_risk_score(
        {"components": components}, risk["risk_score"]
    )
    print(f"  total_factors      : {explanation.get('total_factors')}")
    print(f"  critical_factors   : {explanation.get('critical_factors')}")
    print(f"  top risk factors   :")
    for rf in explanation.get("risk_factors", [])[:5]:
        print(f"    - {rf}")

    banner("STEP 5 - REMEDIATION SUGGESTIONS", "-")
    print(f"  total_issues       : {remed['total_issues']}")
    print(f"  critical_issues    : {remed['critical_issues']}")
    for grp in remed.get("recommendations_by_severity", []):
        print(f"\n  [{grp['severity']}] {grp['pattern']}")
        for s in grp["suggestions"][:3]:
            print(f"    - {s}")

    plan = remed.get("action_plan", [])
    if plan:
        print(f"\n  PRIORITIZED ACTION PLAN ({len(plan)} steps):")
        for a in plan[:5]:
            print(f"    P{a.get('priority')}: {a.get('action', '')[:90]}")

    banner("GENERAL RECOMMENDATIONS", "-")
    for r in remed.get("general_recommendations", [])[:3]:
        print(f"  > {r}")


def main():
    parser = ConfigParser()
    scorer = RiskScoringEngine()
    remediator = RemediationEngine()
    explainer = SHAPExplainer()
    detector = AutoencoderAnomalyDetector() if HAVE_AE else None

    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        demo_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sample_configs",
        )
        files = sorted(glob.glob(os.path.join(demo_dir, "*.json")) +
                       glob.glob(os.path.join(demo_dir, "*.yaml")))

    print("\n" + "#" * 72)
    print("#" + " " * 70 + "#")
    print("#" + "        CloudGuard Live Demo - Vulnerability Detection Pipeline".center(70) + "#")
    print("#" + " " * 70 + "#")
    print("#" * 72)
    print(f"\nProcessing {len(files)} configuration file(s)...")

    summary = []
    for f in files:
        try:
            with open(f) as fh:
                text = fh.read()
            cfg_type = detect_type(f)
            analysis = parser.analyze_config(text, cfg_type)
            risk = scorer.calculate_risk_score(analysis)
            analyze_file(f, parser, scorer, remediator, explainer, detector)
            summary.append((os.path.basename(f), risk["risk_score"], risk["risk_level"]))
        except Exception as e:
            print(f"\n[!] Error processing {f}: {e}")
            summary.append((os.path.basename(f), 0, f"ERROR: {e}"))

    banner("FINAL DEMO SUMMARY", "=")
    print(f"  {'FILE':45s} {'SCORE':>8s}  TIER")
    print("  " + "-" * 70)
    for name, score, tier in summary:
        print(f"  {name:45s} {score:>8.2f}  {tier}")
    print()


if __name__ == "__main__":
    main()
