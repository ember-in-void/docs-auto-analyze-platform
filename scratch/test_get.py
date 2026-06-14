import urllib.request
import json
import time

def test_get():
    base_url = "http://localhost:8081"
    
    # 1. Login to get token
    # We will use the QA Tester credentials. We'll register a unique tester first.
    email = f"qa_test_pers@example.com"
    password = "securepassword123"
    
    # Register
    try:
        reg_data = json.dumps({"email": email, "password": password, "name": "QA Tester"}).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/api/v1/auth/register", data=reg_data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
    except Exception:
        pass # might already be registered

    # Login
    login_data = json.dumps({"email": email, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        token = res["data"]["token"]

    # Create Project
    proj_data = json.dumps({"name": "Persistence Test Project", "description": "Testing DB persistence"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/projects", data=proj_data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        project_id = res["data"]["id"]

    # Upload Doc
    doc_data = json.dumps({"title": "spec.txt", "content": "Целью проекта является разработка и внедрение внутренней CRM-системы для управления продажами и интеграция ее со складом. Бюджет 5 млн рублей. Срок 15 октября 2026 года. Стек React и Golang.", "doc_type": "TZ"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/documents", data=doc_data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))

    # Generate Prediction
    print("Generating prediction...")
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/predictions/generate", data=b"", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Prediction generated successfully.")

    # Now, test the GET predictions endpoint!
    print("Fetching predictions via GET...")
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/predictions", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        predictions = res["data"]
        print(f"GET returned {len(predictions)} predictions.")
        if len(predictions) > 0:
            print("Latest prediction details:")
            print(f"  Executive Summary: {predictions[0].get('executive_summary')}")
            print(f"  Gap Analysis exists: {predictions[0].get('gap_analysis') is not None}")

if __name__ == "__main__":
    test_get()
