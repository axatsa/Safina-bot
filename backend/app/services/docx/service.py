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

        # Sender Name Short
        full_name = expense.created_by or ""
        parts = full_name.split()
        if len(parts) >= 2:
            sender_name_short = f"{parts[0]} {parts[1][0]}."
            if len(parts) >= 3:
                sender_name_short += f"{parts[2][0]}."
        else:
            sender_name_short = full_name

        # Sender Position Filtering
        raw_position = expense.created_by_position or ""
        SYSTEM_ROLES = {"user", "admin", "senior_financier", "ceo", ""}
        sender_position = raw_position if raw_position not in SYSTEM_ROLES else "Сотрудник"

        data = {
            "sender_name": expense.created_by,
            "sender_name_short": sender_name_short,
            "sender_position": sender_position,
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": Decimal(str(expense.total_amount)),
            "currency": expense.currency,
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y") if hasattr(expense.date, "strftime") else expense.date,
            "project_name": expense.project_name or "-",
            "project_code": expense.project_code or "-",
            "usd_rate": float(expense.usd_rate) if expense.usd_rate else "-"
        }

        # Director Name Logic
        DIRECTOR_NAMES = {
            "school": "Ганиев Б.Б.",
            "land": "Ганиев Б.Б.",
            "drujba": "Ганиев Б.Б.",
            "management": "Ганиев Б.Б.",
        }
        data["director_name"] = DIRECTOR_NAMES.get(expense.template_key or "default", "Ганиев Б.Б.")
        
        # Add refund specific data if available
        if expense.refund_data:
            rd = expense.refund_data
            data.update(rd)
            
            # Reasons Mapping for Checkboxes
            reason = rd.get("reason", "")
            reasons_map = {
                "Переезд": "reason_pereezd",
                "Изменение графика": "reason_grafik",
                "Несоответствие": "reason_ozhidaniy",
                "Материальные трудности": "reason_trudnosti",
                "По личным причинам": "reason_lichnye",
                "Другое": "reason_drugoe",
            }
            for label, key in reasons_map.items():
                data[key] = "☑" if reason == label else "□"
            
            if reason != "Другое":
                data["reason_drugoe_text"] = ""
            else:
                data["reason_drugoe_text"] = rd.get("reason_other", "")

            # Branch from user profile if not in refund_data
            if expense.created_by_user and expense.created_by_user.branch:
                data["branch"] = expense.created_by_user.branch
            elif not data.get("branch"):
                data["branch"] = ""

            # Defaults for optional fields
            for field in ["transit_account", "bank_iin", "bank_mfo", "amount_words"]:
                if not data.get(field):
                    data[field] = ""

            # Ensure some common keys are also available as top-level if needed by templates
            if "client_name" in rd:
                data["client"] = rd["client_name"]
            if "amount" in rd:
                data["refund_amount"] = rd["amount"]
                data["total_amount"] = Decimal(str(rd["amount"]))
            
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
