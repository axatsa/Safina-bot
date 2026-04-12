import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

# Setup environment to use test sqlite DB
os.environ["DATABASE_URL"] = "sqlite:///./media/safina_extended_test.db"

from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.core.auth import get_password_hash
from app.core import database

# Create tables
Base.metadata.create_all(bind=engine)

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[database.get_db] = get_test_db
client = TestClient(app)

def get_admin_token():
    # Ensure admin exists or uses default env
    resp = client.post("/api/auth/login", json={"login": "safina", "password": "admin123"})
    if resp.status_code != 200:
        # Fallback if env check fails: create a manual admin
        db = SessionLocal()
        admin = db.query(models.User).filter_by(login="testadmin").first()
        if not admin:
            admin = models.User(
                id="admin_uuid", login="testadmin", 
                password_hash=get_password_hash("testpass"),
                first_name="Admin", last_name="Test", role="admin"
            )
            db.add(admin)
            db.commit()
        db.close()
        resp = client.post("/api/auth/login", json={"login": "testadmin", "password": "testpass"})
    return resp.json()["access_token"]

def test_projects_crud():
    print("Testing Projects CRUD...")
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    resp = client.post("/api/projects", json={"name": "New Project", "code": "NEWP", "category": "startup"}, headers=headers)
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["id"]

    # 2. Add Branch to Project
    resp = client.post(f"/api/projects/{project_id}/branches", json={"name": "Branch 1", "code": "BR1"}, headers=headers)
    assert resp.status_code == 200, resp.text
    branch_id = resp.json()["id"]

    # 3. List Projects
    resp = client.get("/api/projects", headers=headers)
    assert resp.status_code == 200
    assert any(p["id"] == project_id for p in resp.json())

    # 4. Delete Project
    resp = client.delete(f"/api/projects/{project_id}", headers=headers)
    assert resp.status_code == 200

    # 5. Verify Cleanup
    db = SessionLocal()
    branch = db.query(models.Branch).filter_by(id=branch_id).first()
    assert branch is None, "Branch should be cascade deleted"
    db.close()
    print("Projects CRUD: PASSED")

def test_full_workflow():
    print("Testing Full Approval Workflow...")
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Setup project/branch/user
    client.post("/api/projects", json={"name": "Workflow Proj", "code": "FLOW", "category": "startup"}, headers=headers)
    proj_resp = client.get("/api/projects", headers=headers)
    proj = [p for p in proj_resp.json() if p["code"] == "FLOW"][0]
    proj_id = proj["id"]
    
    br_resp = client.post(f"/api/projects/{proj_id}/branches", json={"name": "Head", "code": "HED"}, headers=headers)
    branch_id = br_resp.json()["id"]

    # Create user
    user_resp = client.post("/api/team", json={
        "login": "flow_user", "password": "123", "first_name": "Flow", "last_name": "User",
        "role": "user", "project_ids": [proj_id], "branch_ids": [branch_id]
    }, headers=headers)
    user_id = user_resp.json()["id"]

    # User login
    u_token = client.post("/api/auth/login", json={"login": "flow_user", "password": "123"}).json()["access_token"]
    u_headers = {"Authorization": f"Bearer {u_token}"}

    # 1. Submit Expense
    exp_resp = client.post("/api/expenses", json={
        "purpose": "Workflow Test", "request_type": "expense",
        "project_id": proj_id, "branch_id": branch_id,
        "items": [{"name": "Server", "quantity": 1, "amount": 500, "currency": "USD"}]
    }, headers=u_headers)
    assert exp_resp.status_code == 200
    exp_id = exp_resp.json()["id"]

    # 2. Forward to Senior (Admin action)
    fwd_resp = client.post(f"/api/expenses/{exp_id}/forward_senior", headers=headers)
    assert fwd_resp.status_code == 200
    assert fwd_resp.json()["status"] == "pending_senior"

    # 3. Senior Approve (Actually CFO/Admin)
    # Note: In real app, senior_financier role would do this. Admin can also do it via status update.
    app_resp = client.patch(f"/api/expenses/{exp_id}/status", json={"status": "approved_senior", "comment": "CFO Approved"}, headers=headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "approved_senior"

    # 4. Forward to CEO
    ceo_fwd = client.post(f"/api/expenses/{exp_id}/forward_ceo", headers=headers)
    assert ceo_fwd.status_code == 200
    assert ceo_fwd.json()["status"] == "pending_ceo"

    # 5. CEO Approve
    ceo_app = client.patch(f"/api/expenses/{exp_id}/status", json={"status": "approved_ceo", "comment": "CEO Approved"}, headers=headers)
    assert ceo_app.status_code == 200
    assert ceo_app.json()["status"] == "approved_ceo"

    # 6. Confirm (Safina admin)
    conf = client.patch(f"/api/expenses/{exp_id}/status", json={"status": "confirmed", "comment": "Paid"}, headers=headers)
    assert conf.status_code == 200
    assert conf.json()["status"] == "confirmed"

    print("Approval Workflow: PASSED")

def test_exports_and_analytics():
    print("Testing Exports and Analytics...")
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Analytics
    resp = client.get("/api/analytics", headers=headers)
    assert resp.status_code == 200
    print("- Analytics Stats: OK")

    # 2. Export Excel (XLSX)
    resp = client.get("/api/expenses/export-xlsx", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    print("- Excel Export: OK")

    # 3. Export CSV
    resp = client.get("/api/expenses/export", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    print("- CSV Export: OK")

    print("Exports and Analytics: PASSED")

def test_team_management():
    print("Testing Team Management...")
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List Team
    resp = client.get("/api/team", headers=headers)
    assert resp.status_code == 200
    
    # 2. Update User
    # Find the user we created earlier
    users = resp.json()
    user_id = [u["id"] for u in users if u["login"] == "flow_user"][0]
    
    resp = client.patch(f"/api/team/{user_id}", json={"first_name": "UpdatedName"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "UpdatedName"

    # 3. Block User
    resp = client.patch(f"/api/team/{user_id}/status", json={"status": "blocked"}, headers=headers)
    assert resp.status_code == 200
    
    # 4. Try Login as Blocked
    resp = client.post("/api/auth/login", json={"login": "flow_user", "password": "123"})
    assert resp.status_code == 403
    print("- User Blocking: OK")

    # 5. Delete User
    resp = client.delete(f"/api/team/{user_id}", headers=headers)
    assert resp.status_code == 200
    print("- User Deletion: OK")

    print("Team Management: PASSED")

def run_all():
    try:
        test_projects_crud()
        test_full_workflow()
        test_exports_and_analytics()
        test_team_management()
        print("\nSUMMARY: ALL EXTENDED TESTS PASSED.")
    except Exception as e:
        print(f"\nFAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        # Cleanup
        if os.path.exists("./media/safina_extended_test.db"):
            os.remove("./media/safina_extended_test.db")

if __name__ == "__main__":
    run_all()
