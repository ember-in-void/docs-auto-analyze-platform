import urllib.request
import json
import time
import random
import os

def run_test():
    base_url = "http://localhost:8081"
    email = f"tester_{random.randint(1000, 9999)}@example.com"
    password = "securepassword123"
    
    print(f"--- Starting Integration & Speed Test ---")
    print(f"Registering user with email: {email}")
    
    # 1. Register
    reg_data = json.dumps({
        "email": email,
        "password": password,
        "name": "QA Tester"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{base_url}/api/v1/auth/register",
        data=reg_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            print("User registered successfully.")
    except Exception as e:
        print(f"Registration failed: {e}")
        return

    # 2. Login
    login_data = json.dumps({
        "email": email,
        "password": password
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{base_url}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            token = res["data"]["token"]
            print("User logged in successfully. Token acquired.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 3. Create Project
    proj_data = json.dumps({
        "name": "Integration test project",
        "description": "Validating speed and quality of dynamic Ollama parsing"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{base_url}/api/v1/projects",
        data=proj_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            project_id = res["data"]["id"]
            print(f"Created project. ID: {project_id}")
    except Exception as e:
        print(f"Project creation failed: {e}")
        return

    # 4. Read CRM Technical Specification document
    doc_path = "/home/adam/dw/docs-auto-analyze-platform/demo-docs/tz_crm_medium_risk.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    # 5. Upload Document
    doc_data = json.dumps({
        "title": "tz_crm_medium_risk.txt",
        "content": doc_content,
        "doc_type": "TZ"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{base_url}/api/v1/projects/{project_id}/documents",
        data=doc_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            doc_id = res["data"]["id"]
            print(f"Uploaded technical specification. ID: {doc_id}")
    except urllib.error.HTTPError as e:
        print(f"Document upload failed (HTTPError): {e}")
        try:
            print("Response body:", e.read().decode('utf-8'))
        except:
            pass
        return
    except Exception as e:
        print(f"Document upload failed: {e}")
        return

    # 6. Generate Prediction (measures speed of Ollama execution)
    print("Triggering document analysis (LLM query + Fallbacks if any)...")
    start_time = time.time()
    
    req = urllib.request.Request(
        f"{base_url}/api/v1/projects/{project_id}/predictions/generate",
        data=b"",  # POST requires data
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_time
            pred = res["data"]
            print(f"\n✓ Analysis completed successfully in {elapsed:.2f} seconds!")
            print(f"==================================================")
            print(f"Executive Summary:")
            print(pred.get("executive_summary"))
            print(f"--------------------------------------------------")
            print(f"Metadata Extracted:")
            meta = pred.get("meta_info", {})
            print(f"  Budget: {meta.get('budget')}")
            print(f"  Timeline: {meta.get('timeline')}")
            print(f"  Domain: {meta.get('domain')}")
            print(f"--------------------------------------------------")
            
            gap = pred.get("gap_analysis")
            if gap:
                print(f"Gap Analysis Details:")
                print(f"  Completeness Score: {gap.get('completeness_score')}%")
                print(f"  Clarifying Questions:")
                for q in gap.get("clarifying_questions", []):
                    print(f"    - {q}")
                print(f"  Sections Statuses:")
                for name, info in gap.get("sections", {}).items():
                    print(f"    * {name}: {info.get('status')} (Gaps: {info.get('gaps')})")
            else:
                print("⚠ WARNING: gap_analysis structure is null!")
            print(f"==================================================")
    except Exception as e:
        print(f"Prediction generation failed: {e}")

if __name__ == "__main__":
    run_test()
