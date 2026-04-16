"""
Quick Endpoint Test - Run after starting Flask server manually
Usage: python backend_app.py  # in terminal 1
       python test_quick_endpoints.py  # in terminal 2
"""

import requests

BASE_URL = "http://localhost:5000"

def test(method, endpoint, desc, payload=None):
    try:
        if method == 'GET':
            r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        else:
            r = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=5)
        status = "✓" if r.status_code < 400 else "✗"
        print(f"{status} {desc:45} | {method:4} {endpoint:40} | {r.status_code}")
        return r.status_code < 400
    except Exception as e:
        print(f"✗ {desc:45} | {method:4} {endpoint:40} | ERROR: {type(e).__name__}")
        return False

print("\n" + "="*110)
print("QUICK ENDPOINT TEST SUITE")
print("="*110 + "\n")

passed = 0
failed = 0

# Configuration Routes
print("CONFIGURATION ROUTES (/api/config)")
print("-" * 110)
tests = [
    ('GET', '/api/config/list', 'List configurations', None),
    ('POST', '/api/config/upload', 'Upload configuration', {
        'config_name': 'test', 'config_type': 'iam',
        'config_text': '{"Version": "2012-10-17"}', 'environment': 'prod'
    }),
    ('POST', '/api/config/scan', 'Scan for risks', {'threshold': 5.0}),
    ('POST', '/api/config/export/summary', 'Export summary', {}),
]

for method, endpoint, desc, payload in tests:
    if test(method, endpoint, desc, payload):
        passed += 1
    else:
        failed += 1

# Baseline Routes
print("\nBASELINE ROUTES (/api/baseline)")
print("-" * 110)
tests = [
    ('POST', '/api/baseline/infer', 'Mine baseline rules', {
        'logs': [
            {'userId': 'user1', 'action': 'read', 'resource': 'file1', 'label': 'allowed'},
            {'userId': 'user1', 'action': 'write', 'resource': 'file2', 'label': 'over-granted'}
        ]
    }),
    ('GET', '/api/baseline/rules', 'Get baseline rules', None),
]

for method, endpoint, desc, payload in tests:
    if test(method, endpoint, desc, payload):
        passed += 1
    else:
        failed += 1

# Evaluation Routes
print("\nEVALUATION ROUTES (/api)")
print("-" * 110)
tests = [
    ('POST', '/api/logs/upload', 'Upload logs', {'logs': []}),
    ('GET', '/api/logs', 'Get logs', None),
    ('GET', '/api/evaluate/metrics', 'Get metrics', None),
    ('POST', '/api/ml/analyze', 'ML analyze', {'data': []}),
    ('GET', '/api/evaluate/cross-validate', 'Cross-validate', None),
    ('GET', '/api/evaluate/compare-baselines', 'Compare baselines', None),
    ('GET', '/api/evaluate/ablation', 'Ablation study', None),
    ('GET', '/api/health', 'Health check', None),
]

for method, endpoint, desc, payload in tests:
    if test(method, endpoint, desc, payload):
        passed += 1
    else:
        failed += 1

# Dashboard Routes
print("\nDASHBOARD ROUTES (/api/dashboard)")
print("-" * 110)
tests = [
    ('GET', '/api/dashboard/summary', 'Dashboard summary', None),
    ('GET', '/api/dashboard/stats', 'Dashboard stats', None),
]

for method, endpoint, desc, payload in tests:
    if test(method, endpoint, desc, payload):
        passed += 1
    else:
        failed += 1

print("\n" + "="*110)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*110 + "\n")
