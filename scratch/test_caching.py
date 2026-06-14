import urllib.request
import json
import time
import random

def run_test():
    base_url = "http://localhost:8081"
    email = f"tester_cache_{random.randint(1000, 9999)}@example.com"
    password = "securepassword123"
    
    print(f"--- Starting Cache Verification Test ---")
    
    # 1. Register
    reg_data = json.dumps({"email": email, "password": password, "name": "Cache Tester"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/auth/register", data=reg_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        pass
        
    # 2. Login
    login_data = json.dumps({"email": email, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        token = res["data"]["token"]

    # 3. Create Project
    proj_data = json.dumps({"name": "Cache test project", "description": "Verification"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/projects", data=proj_data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        project_id = res["data"]["id"]

    # 4. Read document content
    doc_path = "/home/adam/dw/docs-auto-analyze-platform/demo-docs/tz_crm_medium_risk.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    # 5. Upload Document
    doc_data = json.dumps({"title": "test_doc.txt", "content": doc_content, "doc_type": "TZ"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/documents", data=doc_data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        pass

    # 6. Trigger Prediction 1 (Cold run)
    print("Triggering Prediction 1 (Cold)...")
    start_time = time.time()
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/predictions/generate", data=b"", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        
    # Poll status for Cold run
    success = False
    for i in range(60):
        time.sleep(2)
        status_req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/predictions", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(status_req) as resp:
            status_res = json.loads(resp.read().decode('utf-8'))
            preds = status_res["data"]
            if preds and preds[0].get("status") == "completed":
                success = True
                break
    cold_time = time.time() - start_time
    print(f"Cold run finished. Total time: {cold_time:.2f} seconds.")

    # 7. Trigger Prediction 2 (Hot run - should hit the cache immediately)
    print("Triggering Prediction 2 (Hot)...")
    start_time = time.time()
    req = urllib.request.Request(f"{base_url}/api/v1/projects/{project_id}/predictions/generate", data=b"", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        status = res["data"].get("status")
        
    hot_time = time.time() - start_time
    print(f"Hot run finished immediately. Return status: {status}. Time: {hot_time:.4f} seconds!")
    
    if hot_time < 0.1 and status == "completed":
        print("✓ SUCCESS: Caching is working correctly!")
    else:
        print("❌ FAILURE: Caching did not work as expected.")

if __name__ == "__main__":
    run_test()
