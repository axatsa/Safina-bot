import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./media/safina_blank_test.db"

from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.core.auth import get_password_hash
from app.core import database

Base.metadata.create_all(bind=engine)

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[database.get_db] = get_test_db
client = TestClient(app)

def test_blank_refund_submission():
    print("Testing Blank Refund Submission...")
    # Setup
    db = SessionLocal()
    admin = models.User(
        id="admin", login="safina", password_hash=get_password_hash("admin123"),
        first_name="Admin", last_name="Safina", role="admin"
    )
    db.add(admin)
    db.commit()
    db.close()

    resp = client.post("/api/auth/login", json={"login": "safina", "password": "admin123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit Blank Refund
    refund_data = {
        "client_name": "John Doe",
        "amount": 500000,
        "contract_number": "SA-12345",
        "reason": "Relocation",
        "branch_id": "test_br"
    }
    
    resp = client.post("/api/expenses/refund-application-submit", json=refund_data, headers=headers)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["request_type"] == "blank_refund"
    assert res_json["refund_data"]["client_name"] == "John Doe"
    print("Blank Refund Submission: OK")

if __name__ == "__main__":
    try:
        test_blank_refund_submission()
    finally:
        if os.path.exists("./media/safina_blank_test.db"):
            os.remove("./media/safina_blank_test.db")
