import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from app.core import auth
from app.db import models
from sqlalchemy.orm import Session
from app.core.database import get_db

def test_export():
    client = TestClient(app)
    
    # Mock auth.get_current_user to return an admin
    # We can override the dependency
    def get_mock_admin():
        return models.TeamMember(id="mock-admin", last_name="Admin", first_name="Safina", position="admin")
    
    app.dependency_overrides[auth.get_current_user] = get_mock_admin
    
    # Test XLSX export
    response = client.get("/api/expenses/export-xlsx?allStatuses=true")
    print(f"XLSX Export Status: {response.status_code}")
    if response.status_code == 200:
        print("XLSX Export SUCCESS")
        print(f"Content Length: {len(response.content)}")
    else:
        print(f"XLSX Export FAILED: {response.text}")

    # Test CSV export
    response = client.get("/api/expenses/export?allStatuses=true")
    print(f"CSV Export Status: {response.status_code}")
    if response.status_code == 200:
        print("CSV Export SUCCESS")
    else:
        print(f"CSV Export FAILED: {response.text}")

if __name__ == "__main__":
    test_export()
