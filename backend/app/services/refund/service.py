"""
Refund Service — бизнес-логика модуля возвратов.

Этот слой ничего не знает о HTTP (FastAPI) и о боте (aiogram).
Принимает и возвращает только Python-объекты / Pydantic-схемы.
"""
from __future__ import annotations

import re
import os
import uuid
import shutil
from typing import Optional, Tuple
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db import models, schemas, crud
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

SCHOOL_KEYWORDS = ("школ", "school")   # case-insensitive; оба языка

EXPORTABLE_STATUSES = [
    "confirmed",
    "approved_senior",
    "approved_ceo",
    "declined",
    "revision",
]

EXCLUDED_FROM_EXPORT = {"pending_senior", "pending_ceo", "archived"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_school_branch(branch: Optional[str]) -> bool:
    """True если филиал — школьный (рус. «школ» или англ. «school»)."""
    if not branch:
        return False
    branch_lower = branch.lower()
    return any(kw in branch_lower for kw in SCHOOL_KEYWORDS)


def validate_card_number(card_number: str) -> Tuple[bool, str]:
    """Возвращает (ok, очищенный_номер) или (False, описание_ошибки)."""
    digits = re.sub(r"\D", "", card_number)
    if len(digits) != 16:
        return False, f"Номер карты должен содержать 16 цифр, получено {len(digits)}"
    return True, digits


def save_receipt_photo(upload_file) -> str:
    """Сохраняет загруженный файл чека и возвращает путь."""
    upload_dir = "uploads/receipts"
    os.makedirs(upload_dir, exist_ok=True)
    ext = upload_file.filename.rsplit(".", 1)[-1] if "." in upload_file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as buf:
        shutil.copyfileobj(upload_file.file, buf)
    return file_path


# ---------------------------------------------------------------------------
# Основная бизнес-логика
# ---------------------------------------------------------------------------

async def create_refund(
    db: Session,
    *,
    student_id: str,
    reason: str,
    amount: Decimal,
    card_number: str,
    retention: bool = False,
    receipt_photo_ref: Optional[str] = None,          # Telegram file_id ИЛИ локальный путь
    user_id: Optional[str] = None,
    branch: Optional[str] = None,
    team: Optional[str] = None,
) -> models.ExpenseRequest:
    """
    Создаёт заявку типа 'refund' в БД.
    """
    from app.services.currency.service import currency_service
    
    ok, cleaned_card = validate_card_number(card_number)
    if not ok:
        raise ValueError(cleaned_card)

    refund_data = schemas.RefundDataSchema(
        student_id=student_id,
        reason=reason,
        card_number=cleaned_card,
        retention=retention,
        branch=branch,
        team=team,
    )

    items = [
        schemas.ExpenseItemSchema(
            name=f"Возврат (ID: {student_id})",
            quantity=1,
            amount=amount,
            currency=schemas.CurrencyEnum.UZS,
        )
    ]

    expense_create = schemas.ExpenseRequestCreate(
        purpose=f"Возврат (Ученик: {student_id})",
        items=items,
        total_amount=amount,
        currency=schemas.CurrencyEnum.UZS,
        project_id=None,
        request_type="refund",
        receipt_photo_file_id=receipt_photo_ref,
        refund_data=refund_data,
    )

    usd_rate = await currency_service.get_usd_rate()
    db_expense = crud.create_expense_request(db, expense_create, user_id=user_id, usd_rate=usd_rate)
    logger.info(
        "Refund created: %s | student=%s | amount=%s | branch=%s",
        db_expense.request_id, student_id, amount, branch,
    )
    return db_expense


def get_exportable_expenses_query(db: Session, *, all_statuses: bool = False):
    """
    Возвращает SQLAlchemy-запрос с правильным фильтром для экспорта.

    all_statuses=False  → только 'confirmed'
    all_statuses=True   → все допустимые, но без pending_* и archived
    """
    query = db.query(models.ExpenseRequest)
    if all_statuses:
        query = query.filter(
            ~models.ExpenseRequest.status.in_(list(EXCLUDED_FROM_EXPORT))
        )
    else:
        query = query.filter(
            models.ExpenseRequest.status.in_(EXPORTABLE_STATUSES)
        )
    return query
