import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock DB
os.environ["DATABASE_URL"] = "sqlite:///./media/test_analytics_multi.db"

from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.core.auth import get_password_hash
from app.core import database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create Admin
    admin = models.User(
        id="admin", login="safina", password_hash=get_password_hash("admin123"), 
        role="admin", first_name="Safina", last_name="Admin"
    )
    db.add(admin)
    
    # Create Projects
    p1 = models.Project(id="p1", name="Project 1", code="P1")
    p2 = models.Project(id="p2", name="Project 2", code="P2")
    p3 = models.Project(id="p3", name="Project 3", code="P3")
    db.add_all([p1, p2, p3])
    
    # Create Expenses
    # P1: 2 expenses, P2: 1 expense, P3: 0 expenses
    e1 = models.ExpenseRequest(
        id="e1", request_id="E1", purpose="P1 Exp 1", total_amount=1000, 
        currency="UZS", status="confirmed", project_id="p1", branch_name="Branch A",
        created_by="User", items=[]
    )
    e2 = models.ExpenseRequest(
        id="e2", request_id="E2", purpose="P1 Exp 2", total_amount=2000, 
        currency="UZS", status="confirmed", project_id="p1", branch_name="Branch B",
        created_by="User", items=[]
    )
    e3 = models.ExpenseRequest(
        id="e3", request_id="E3", purpose="P2 Exp 1", total_amount=4000, 
        currency="UZS", status="confirmed", project_id="p2", branch_name="Branch A",
        created_by="User", items=[]
    )
    db.add_all([e1, e2, e3])
    
    db.commit()
    yield db
    db.close()

def get_token(login, password):
    resp = client.post("/api/auth/login", json={"login": login, "password": password})
    return resp.json()["access_token"]

def test_multi_project_filtering():
    token = get_token("safina", "admin123")
    
    # Select P1 only
    resp = client.get("/api/analytics?project_ids=p1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # Total UZS should be 1000 + 2000 = 3000
    total = sum(d["value"] for d in data["expense_distribution"])
    assert total == 3000
    
    # Select P1 and P2
    resp = client.get("/api/analytics?project_ids=p1&project_ids=p2", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # Total UZS should be 1000 + 2000 + 4000 = 7000
    total = sum(d["value"] for d in data["expense_distribution"])
    assert total == 7000

    # Select P3 only (empty)
    resp = client.get("/api/analytics?project_ids=p3", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["expense_distribution"]) == 0

def test_multi_branch_filtering():
    token = get_token("safina", "admin123")
    
    # Select Branch A only
    # E1 (P1) and E3 (P2) are Branch A. Total: 1000 + 4000 = 5000
    resp = client.get("/api/analytics?branch_names=Branch+A", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["value"] for d in data["expense_distribution"])
    assert total == 5000
    
    # Select Branch A and Branch B
    # All expenses: 1000 + 2000 + 4000 = 7000
    resp = client.get("/api/analytics?branch_names=Branch+A&branch_names=Branch+B", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["value"] for d in data["expense_distribution"])
    assert total == 7000

def test_combined_multi_filtering():
    token = get_token("safina", "admin123")
    
    # Select P1 AND Branch A
    # Only E1 fits. Total: 1000
    resp = client.get("/api/analytics?project_ids=p1&branch_names=Branch+A", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["value"] for d in data["expense_distribution"])
    assert total == 1000
