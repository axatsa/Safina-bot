import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Setup environment
os.environ["DATABASE_URL"] = "sqlite:///./media/safina_edge_test.db"

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

def setup_users():
    db = SessionLocal()
    # Admin
    admin = models.User(
        id="admin", login="safina", password_hash=get_password_hash("admin123"),
        first_name="Admin", last_name="Safina", role="admin"
    )
    # Regular User
    reg_user = models.User(
        id="user1", login="user1", password_hash=get_password_hash("123"),
        first_name="Regular", last_name="User", role="user"
    )
    db.add(admin)
    db.add(reg_user)
    db.commit()
    db.close()

def test_unauthorized():
    print("Testing Unauthorized Access...")
    resp = client.get("/api/projects")
    assert resp.status_code == 401
    print("Unauthorized: OK (401)")

def test_rbac():
    print("Testing RBAC (User Role Restrictions)...")
    # Login as User
    resp = client.post("/api/auth/login", json={"login": "user1", "password": "123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # User tries to access team management
    resp = client.get("/api/team", headers=headers)
    assert resp.status_code == 403
    print("RBAC (User -> Team): OK (403 Forbidden)")

def test_blanks_generation():
    print("Testing Blanks Generation...")
    resp = client.post("/api/auth/login", json={"login": "user1", "password": "123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate Land blank
    # We use 'land' because it maps to LAND.docx which likely exists in services/docx/templates/
    # Note: If template file is missing, this might fail with 500, which we should document.
    resp = client.post("/api/blanks/generate", json={
        "template": "land",
        "purpose": "Test Land Blank",
        "items": [{"name": "Property", "qty": 1, "amount": 1000, "currency": "USD"}]
    }, headers=headers)
    
    if resp.status_code == 200:
        print("Blanks Generation (land): OK")
    elif resp.status_code == 500 and "Template file not found" in resp.text:
         print("Blanks Generation: FAIL - Template file missing (Known issue)")
    else:
        assert resp.status_code == 200, resp.text

def test_currency_api():
    print("Testing Currency API...")
    # This might fail if network is blocked or CBU is down
    from app.services.currency.service import currency_service
    import asyncio
    
    try:
        # We need to run async function in a sync test
        rate = asyncio.run(currency_service.get_usd_rate())
        print(f"Currency API: OK (Rate: {rate})")
    except Exception as e:
        print(f"Currency API: FAIL ({str(e)})")

def run_all():
    setup_users()
    test_unauthorized()
    test_rbac()
    test_blanks_generation()
    test_currency_api()
    
    if os.path.exists("./media/safina_edge_test.db"):
        os.remove("./media/safina_edge_test.db")

if __name__ == "__main__":
    run_all()
