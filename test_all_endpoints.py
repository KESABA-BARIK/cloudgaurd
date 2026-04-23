"""
Smoke test that hits every CloudGuard endpoint and prints the status code.
Run with: python test_all_endpoints.py
"""

import requests

BASE = "http://localhost:5000"

ENDPOINTS = [
    ("GET",  "/api/health",                      None),
    ("GET",  "/api/logs",                        None),
    ("POST", "/api/logs/upload",                 {"logs": []}),
    ("POST", "/api/baseline/infer",              {}),
    ("GET",  "/api/baseline/rules",              None),
    ("POST", "/api/evaluate",                    {"userId": "u", "resource": "r", "action": "a"}),
    ("GET",  "/api/evaluate/metrics",            None),
    ("POST", "/api/ml/analyze",                  {"configs": []}),
    ("GET",  "/api/evaluate/cross-validate",     None),
    ("GET",  "/api/evaluate/compare-baselines",  None),
    ("GET",  "/api/evaluate/ablation",           None),
    ("GET",  "/api/dashboard/summary",           None),
    ("GET",  "/api/dashboard/stats",             None),
    ("GET",  "/api/config/list",                 None),
]


def main():
    print(f"{'Method':6} {'Endpoint':40} Status")
    print("-" * 60)
    for method, path, body in ENDPOINTS:
        try:
            r = requests.request(method, BASE + path, json=body, timeout=10)
            print(f"{method:6} {path:40} {r.status_code}")
        except Exception as e:
            print(f"{method:6} {path:40} ERR {e}")


if __name__ == "__main__":
    main()
