"""
Refund DOCX Export — генерация заявления на возврат денег по шаблону школы.

Этот модуль изолирован: не знает о HTTP и боте.
Принимает модель ExpenseRequest, возвращает BytesIO с DOCX.
"""
from __future__ import annotations

import io
import os
import datetime
from typing import Optional

from docxtpl import DocxTemplate

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Путь к шаблону
_TEMPLATE_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "../docx/templates/возврат шаблон лс.docx"),
    "возврат шаблон лс.docx",
]


def _find_template() -> str:
    for path in _TEMPLATE_CANDIDATES:
        normalized = os.path.normpath(path)
        if os.path.exists(normalized):
            return normalized
    raise FileNotFoundError(
        "Шаблон 'возврат шаблон лс.docx' не найден. "
        "Убедитесь, что файл лежит в app/services/docx/templates/."
    )


def generate_application_docx(
    *,
    student_id: str,
    reason: str,
    amount: float,
    card_number: str,
    retention: bool,
    branch: Optional[str],
    team: Optional[str],
    sender_name: str,
    sender_position: Optional[str],
    request_id: str,
    date: datetime.datetime,
    template_path: Optional[str] = None,
) -> io.BytesIO:
    """
    Заполняет шаблон 'возврат шаблон лс.docx' и возвращает BytesIO.

    Все переменные шаблона передаются через context-словарь docxtpl.
    Имена переменных должны совпадать с {{ var_name }} в самом .docx.
    """
    path = template_path or _find_template()

    retention_text = "Да" if retention else "Нет"
    formatted_date = date.strftime("%d.%m.%Y") if isinstance(date, (datetime.date, datetime.datetime)) else str(date)
    formatted_amount = f"{amount:,.0f}".replace(",", " ")

    context = {
        # Данные заявителя
        "sender_name": sender_name,
        "client_name": sender_name, # In short template it's {{ client_name }}
        "sender_position": sender_position or "Администратор",
        "branch": branch or "",
        "team": team or "",
        # Данные возврата
        "student_id": student_id,
        "reason": reason,
        "amount": formatted_amount,
        "amount_raw": amount,
        "card_number": card_number,
        "retention": retention_text,
        # Служебные
        "request_id": request_id,
        "date": formatted_date,
    }

    doc = DocxTemplate(path)
    doc.render(context)

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)
    logger.info("Application DOCX generated for request %s (student=%s)", request_id, student_id)
    return stream
