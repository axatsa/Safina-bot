import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

# Setup environment to use test sqlite DB
os.environ["DATABASE_URL"] = "sqlite:///./media/safina_test.db"

# We must import from app after setting environment var
from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.core.auth import get_password_hash

# Create tables for testing
Base.metadata.create_all(bind=engine)

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override dependency
from app.core import database
app.dependency_overrides[database.get_db] = get_test_db

client = TestClient(app)

def setup_admin_and_project():
    db = SessionLocal()
    # Create admin
    admin = db.query(models.User).filter_by(login="testadmin").first()
    if not admin:
        admin = models.User(
            id="admin_uuid", 
            login="testadmin", 
            password_hash=get_password_hash("testpass"),
            first_name="Admin", 
            last_name="Test", 
            role="admin"
        )
        db.add(admin)
        db.commit()

    # Create project and branch
    project = db.query(models.Project).filter_by(code="TEST").first()
    if not project:
        project = models.Project(id="proj_uuid", name="Test Project", code="TEST", category="startup")
        db.add(project)
        branch = models.Branch(id="branch_uuid", name="Test Branch", code="TBR", project_id="proj_uuid")
        db.add(branch)
        db.commit()

    db.close()
    return "admin_uuid", "proj_uuid", "branch_uuid"

def get_admin_token():
    resp = client.post("/api/auth/login", json={"login": "testadmin", "password": "testpass"})
    return resp.json()["access_token"]

def teardown_test_data():
    Base.metadata.drop_all(bind=engine)

def run_tests():
    setup_admin_and_project()
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("Test 1: Create user WITHOUT branch")
    resp1 = client.post(
        "/api/team", 
        json={
            "login": "user_no_branch", "password": "123", "first_name": "No", "last_name": "Branch",
            "role": "user", "project_ids": [], "branch_ids": []
        }, headers=headers
    )
    assert resp1.status_code == 200, resp1.text
    user1_id = resp1.json()["id"]

    print("Test 2: Create user WITH branch")
    resp2 = client.post(
        "/api/team", 
        json={
            "login": "user_with_branch", "password": "123", "first_name": "With", "last_name": "Branch",
            "role": "user", "project_ids": ["proj_uuid"], "branch_ids": ["branch_uuid"]
        }, headers=headers
    )
    assert resp2.status_code == 200, resp2.text
    user2_id = resp2.json()["id"]

    print("Test 3: Connect user WITHOUT branch to branch (via PATCH)")
    resp3 = client.patch(
        f"/api/team/{user1_id}",
        json={"branch_ids": ["branch_uuid"], "project_ids": ["proj_uuid"]},
        headers=headers
    )
    assert resp3.status_code == 200, resp3.text
    assert len(resp3.json()["branches"]) > 0

    def test_expense(login, user_id):
        # login
        u_token = client.post("/api/auth/login", json={"login": login, "password": "123"}).json()["access_token"]
        u_header = {"Authorization": f"Bearer {u_token}"}
        
        # post expense
        exp_resp = client.post("/api/expenses", json={
            "purpose": "Test Expense", "request_type": "expense",
            "project_id": "proj_uuid", "branch_id": "branch_uuid",
            "items": [{"name": "Item", "quantity": 1, "amount": 100, "currency": "UZS"}]
        }, headers=u_header)
        assert exp_resp.status_code == 200, exp_resp.text
        
        # post refund
        ref_resp = client.post("/api/expenses", json={
            "purpose": "Test Refund", "request_type": "refund",
            "project_id": "proj_uuid", "branch_id": "branch_uuid",
            "refund_data": {"client_name": "Client", "amount": 1000}
        }, headers=u_header)
        assert ref_resp.status_code == 200, ref_resp.text
        print(f"User {login} successfully created requests.")

    print("Test 4: Send request from user with branch")
    test_expense("user_with_branch", user2_id)

    print("Test 5: Send request from user newly assigned to branch")
    test_expense("user_no_branch", user1_id)

    print("All tests passed.")
    teardown_test_data()

if __name__ == "__main__":
    run_tests()
