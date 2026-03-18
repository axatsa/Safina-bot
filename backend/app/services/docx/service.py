import os
from sqlalchemy.orm import Session
from decimal import Decimal
from app.db import models
from .generator import generate_docx

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

class DocxService:
    DEFAULT_TEMPLATE = "Management.docx"
    REFUND_TEMPLATE = "Заявление_на_возврат_денег.docx"
    
    BRANCH_MAPPING = {
        "school": "School.docx",
        "школ": "School.docx",
        "land": "LAND.docx",
        "drujba": "Drujba.docx",
        "дружба": "Drujba.docx"
    }

    def get_template_path(self, expense: models.ExpenseRequest) -> str:
        """Select the correct template based on expense type, template_key, and branch."""
        # 1. Если это refund (старый тип или новый)
        if expense.request_type in ["refund", "blank_refund"] or expense.template_key == "refund":
            return os.path.join(TEMPLATES_DIR, self.REFUND_TEMPLATE)
            
        # 2. Если есть явный ключ шаблона (новый выбор в боте)
        if expense.template_key:
            tpl_name = self.BRANCH_MAPPING.get(expense.template_key)
            if tpl_name:
                return os.path.join(TEMPLATES_DIR, tpl_name)

        # 3. Fallback: по филиалу сотрудника (старая логика)
        branch = None
        if expense.created_by_user and expense.created_by_user.branch:
            branch = expense.created_by_user.branch.lower()
        elif expense.refund_data and expense.refund_data.get("branch"):
            branch = expense.refund_data.get("branch").lower()

        template_name = self.DEFAULT_TEMPLATE
        if branch:
            for key, tpl in self.BRANCH_MAPPING.items():
                if key in branch:
                    template_name = tpl
                    break
                    
        return os.path.join(TEMPLATES_DIR, template_name)

    def prepare_docx_data(self, expense: models.ExpenseRequest):
        """Prepare data dictionary for the docxtpl template."""
        items_data = []
        raw_items = expense.items
        if isinstance(raw_items, list):
            for idx, item in enumerate(raw_items):
                if isinstance(item, dict):
                    qty = float(item.get("quantity", 0))
                    price = float(item.get("amount", 0))
                    items_data.append({
                        "no": idx + 1,
                        "name": item.get("name", "Без названия"),
                        "quantity": qty,
                        "price": price,
                        "total": qty * price
                    })

        data = {
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": Decimal(str(expense.total_amount)),
            "currency": expense.currency,
            "request_id": expense.request_id,
            "date": expense.date,
            "project_name": expense.project_name or "-",
            "project_code": expense.project_code or "-",
            "usd_rate": float(expense.usd_rate) if expense.usd_rate else "-"
        }
        
        # Add refund specific data if available
        if expense.refund_data:
            data.update(expense.refund_data)
            
        return data

    def generate_expense_docx(self, expense: models.ExpenseRequest):
        """Main method to generate DOCX for an expense."""
        template_path = self.get_template_path(expense)
        if not os.path.exists(template_path):
            # Fallback to default if somehow file is missing
            template_path = os.path.join(TEMPLATES_DIR, self.DEFAULT_TEMPLATE)
            
        data = self.prepare_docx_data(expense)
        return generate_docx(template_path, data)

docx_service = DocxService()
