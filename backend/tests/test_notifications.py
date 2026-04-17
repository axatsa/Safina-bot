import os
import sys
from unittest.mock import MagicMock, patch, ANY
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock DB for test
os.environ["DATABASE_URL"] = "sqlite:///./media/test_notifications.db"

from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.core.auth import get_password_hash
from app.core import database

client = TestClient(app)

# Helper to create users
def setup_users(db):
    admin = models.User(
        id="admin_id", login="safina", 
        password_hash=get_password_hash("admin123"),
        first_name="Safina", last_name="Admin", role="admin", position="admin"
    )
    farrukh = models.User(
        id="farrukh_id", login="farrukh", 
        password_hash=get_password_hash("farrukh123"),
        first_name="Farrukh", last_name="CFO", role="senior_financier", position="senior_financier",
        telegram_chat_id=111
    )
    ganiev = models.User(
        id="ganiev_id", login="ganiev", 
        password_hash=get_password_hash("ganiev123"),
        first_name="Ganiev", last_name="CEO", role="ceo", position="ceo",
        telegram_chat_id=222
    )
    user = models.User(
        id="user_id", login="user", 
        password_hash=get_password_hash("user123"),
        first_name="User", last_name="Test", role="user",
        telegram_chat_id=333
    )
    
    # Setting for admin chat id
    admin_setting = models.Setting(key="admin_chat_id", value="444")
    
    db.add_all([admin, farrukh, ganiev, user, admin_setting])
    db.commit()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    setup_users(db)
    yield db
    db.close()

def get_token(login, password):
    resp = client.post("/api/auth/login", json={"login": login, "password": password})
    return resp.json()["access_token"]

@patch("app.api.expenses.send_status_notification")
@patch("app.api.expenses.send_ceo_decision_notification")
@patch("app.api.expenses.get_admin_chat_id")
@patch("app.api.expenses.get_senior_financier_chat_ids")
@patch("app.services.notifications.sse.publish_notification")
def test_ceo_approval_notifications(mock_sse, mock_get_senior, mock_get_admin, mock_send_decision, mock_send_status, setup_db):
    """Test that CEO approval via API notifies Admin and CFO."""
    db = setup_db
    mock_get_admin.return_value = 444
    mock_get_senior.return_value = [111]
    
    # 1. Create expense
    user_token = get_token("user", "user123")
    exp_resp = client.post("/api/expenses", json={
        "purpose": "Test Notifications", "request_type": "expense",
        "items": [{"name": "item", "quantity": 1, "amount": 100, "currency": "UZS"}]
    }, headers={"Authorization": f"Bearer {user_token}"})
    exp_id = exp_resp.json()["id"]
    
    # 2. Forward to Senior (Admin action)
    admin_token = get_token("safina", "admin123")
    client.post(f"/api/expenses/{exp_id}/forward_senior", headers={"Authorization": f"Bearer {admin_token}"})
    
    # 3. Approved by Senior (Farrukh)
    farrukh_token = get_token("farrukh", "farrukh123")
    client.patch(f"/api/expenses/{exp_id}/status", json={"status": "approved_senior", "comment": "CFO OK"}, headers={"Authorization": f"Bearer {farrukh_token}"})
    
    # 4. Forward to CEO
    client.post(f"/api/expenses/{exp_id}/forward_ceo", headers={"Authorization": f"Bearer {farrukh_token}"})
    
    # 5. CEO Approves via API (Ganiev)
    ganiev_token = get_token("ganiev", "ganiev123")
    
    resp = client.patch(f"/api/expenses/{exp_id}/status", 
                       json={"status": "approved_ceo", "comment": "CEO OK"}, 
                       headers={"Authorization": f"Bearer {ganiev_token}"})
    
    assert resp.status_code == 200
    
    # Verify notifications were added to background tasks
    # With TestClient, background tasks ARE executed before the response is returned 
    # OR they are accessible via the response object if using async client.
    # But for standard TestClient, it runs them sync.
    
    # Creator notified
    mock_send_status.assert_called()
    
    # Admin and CFO notified
    assert mock_send_decision.call_count == 2
    mock_send_decision.assert_any_call(444, ANY, ANY, "UZS", True, "CEO OK")
    mock_send_decision.assert_any_call(111, ANY, ANY, "UZS", True, "CEO OK")

if __name__ == "__main__":
    pytest.main([__file__])
