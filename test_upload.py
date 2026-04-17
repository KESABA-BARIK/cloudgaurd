#!/usr/bin/env python3
"""Test upload functionality with backend"""

import requests
import json
import time

API_BASE = 'http://localhost:5000'

# Test IAM config
iam_config = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::123456789012:user/testuser"},
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::my-bucket/*"
        }
    ]
}

# Test K8s config
k8s_config = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-image:latest
        securityContext:
          runAsNonRoot: true
"""

def test_upload_iam():
    print("=" * 60)
    print("TEST 1: Upload IAM Policy")
    print("=" * 60)
    
    try:
        res = requests.post(
            f'{API_BASE}/api/config/upload',
            json={
                'config_type': 'iam',
                'config_name': 'test-iam-policy',
                'config_text': json.dumps(iam_config),
                'environment': 'test'
            },
            timeout=5
        )
        
        if res.status_code == 201:
            data = res.json()
            print(f"✓ Upload successful!")
            print(f"  Config ID: {data.get('config_id')}")
            print(f"  Config Name: {data.get('config_name')}")
            print(f"  Config Type: {data.get('config_type')}")
            return data.get('config_id')
        else:
            print(f"✗ Upload failed with status {res.status_code}")
            print(f"  Response: {res.text}")
            return None
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None

def test_upload_k8s():
    print("\n" + "=" * 60)
    print("TEST 2: Upload Kubernetes Manifest")
    print("=" * 60)
    
    try:
        res = requests.post(
            f'{API_BASE}/api/config/upload',
            json={
                'config_type': 'k8s',
                'config_name': 'test-k8s-deployment',
                'config_text': k8s_config,
                'environment': 'test'
            },
            timeout=5
        )
        
        if res.status_code == 201:
            data = res.json()
            print(f"✓ Upload successful!")
            print(f"  Config ID: {data.get('config_id')}")
            print(f"  Config Name: {data.get('config_name')}")
            print(f"  Config Type: {data.get('config_type')}")
            return data.get('config_id')
        else:
            print(f"✗ Upload failed with status {res.status_code}")
            print(f"  Response: {res.text}")
            return None
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None

def test_scan(config_id):
    print(f"\n" + "=" * 60)
    print(f"TEST 3: Scan Config {config_id}")
    print("=" * 60)
    
    try:
        res = requests.post(
            f'{API_BASE}/api/config/scan',
            json={
                'config_ids': [config_id],
                'run_autoencoder': False
            },
            timeout=10
        )
        
        if res.status_code == 200:
            data = res.json()
            if data.get('scan_results') and len(data['scan_results']) > 0:
                result = data['scan_results'][0]
                risk = result.get('risk_score', {})
                print(f"✓ Scan successful!")
                print(f"  Risk Score: {risk.get('risk_score')}")
                print(f"  Risk Level: {risk.get('risk_level')}")
                print(f"  Anomaly Score: {risk.get('anomaly_score')}")
                return True
            else:
                print(f"✗ No scan results returned")
                return False
        else:
            print(f"✗ Scan failed with status {res.status_code}")
            print(f"  Response: {res.text}")
            return False
    except Exception as e:
        print(f"✗ Scan error: {e}")
        return False

def test_list_configs():
    print(f"\n" + "=" * 60)
    print(f"TEST 4: List All Configs")
    print("=" * 60)
    
    try:
        res = requests.get(
            f'{API_BASE}/api/config/list',
            timeout=5
        )
        
        if res.status_code == 200:
            data = res.json()
            configs = data.get('configurations', [])
            print(f"✓ Retrieved {len(configs)} configurations")
            for cfg in configs[:3]:  # Show first 3
                print(f"  - {cfg['name']} ({cfg['config_type']}) - Risk: {cfg.get('risk_level', 'Not analyzed')}")
            return True
        else:
            print(f"✗ List failed with status {res.status_code}")
            return False
    except Exception as e:
        print(f"✗ List error: {e}")
        return False

def main():
    print("\n🔍 Testing CloudGuard Upload & Scan API")
    print(f"Backend: {API_BASE}\n")
    
    # Test if backend is running
    try:
        res = requests.get(f'{API_BASE}/api/config/list', timeout=2)
        print("✓ Backend is running!\n")
    except:
        print("✗ ERROR: Backend is not running!")
        print("   Start it with: python backend_app.py\n")
        return
    
    # Run tests
    iam_id = test_upload_iam()
    if iam_id:
        test_scan(iam_id)
    
    k8s_id = test_upload_k8s()
    if k8s_id:
        test_scan(k8s_id)
    
    test_list_configs()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
