import os
import sys
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.docx.service import docx_service
from app.db import models

def test_template_path_selection():
    # 1. Test refund template
    exp_refund = models.ExpenseRequest(request_type="refund")
    path = docx_service.get_template_path(exp_refund)
    assert "Заявление_на_возврат_денег.docx" in path

    # 2. Test explicit template key
    exp_land = models.ExpenseRequest(template_key="land")
    path = docx_service.get_template_path(exp_land)
    assert "LAND.docx" in path

    # 3. Test branch mapping
    exp_school = models.ExpenseRequest(branch_name="School 1")
    path = docx_service.get_template_path(exp_school)
    assert "School.docx" in path

    # 4. Fallback
    exp_default = models.ExpenseRequest(branch_name="Unknown")
    path = docx_service.get_template_path(exp_default)
    assert "Management.docx" in path

def test_data_preparation_standard():
    exp = models.ExpenseRequest(
        created_by="John Doe",
        created_by_position="Manager",
        purpose="Office supplies",
        items=[{"name": "Pen", "quantity": 10, "amount": 2}],
        total_amount=20,
        currency="USD",
        request_id="SCH-001",
        date=datetime(2023, 10, 27),
        project_name="Admin",
        project_code="ADM",
        usd_rate=12500
    )
    
    data = docx_service.prepare_docx_data(exp)
    
    assert data["sender_name"] == "John Doe"
    assert data["sender_name_short"] == "John D."
    assert data["sender_position"] == "Manager"
    assert data["total_amount"] == Decimal("20")
    assert data["items"][0]["total"] == 20.0
    assert data["date"] == "27.10.2023"
    assert data["usd_rate"] == 12500.0

def test_refund_data_mapping():
    refund_data = {
        "client_name": "Alice Smith",
        "amount": 50000,
        "reason": "Переезд",
        "phone": "+998901234567"
    }
    exp = models.ExpenseRequest(
        request_type="refund",
        refund_data=refund_data,
        total_amount=50000,
        currency="UZS",
        items=[]
    )
    
    data = docx_service.prepare_docx_data(exp)
    
    assert data["client"] == "Alice Smith"
    assert data["refund_amount"] == 50000
    assert data["reason_pereezd"] == "☑"
    assert data["reason_grafik"] == "□"
    assert data["branch"] == "" # Empty if not provided
    assert data["transit_account"] == "________________________" # Default underscore

def test_sender_name_shortening():
    # Russian formatting test
    data = docx_service.prepare_docx_data(models.ExpenseRequest(created_by="Иванов Иван Иванович", items=[]))
    assert data["sender_name_short"] == "Иванов И.И."
    
    # 2 parts
    data = docx_service.prepare_docx_data(models.ExpenseRequest(created_by="Ганиев Бахтиер", items=[]))
    assert data["sender_name_short"] == "Ганиев Б."

if __name__ == "__main__":
    pytest.main([__file__])
