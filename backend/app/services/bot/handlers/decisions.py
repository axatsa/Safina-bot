import asyncio
import os
from aiogram import Router, types, F

from app.core import database
from app.db import crud, models, schemas
from ..notifications import send_ceo_decision_notification, get_admin_chat_id, get_senior_financier_chat_ids

router = Router()

@router.callback_query(F.data.startswith("approve_senior_"))
async def handle_approve_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_senior_")
    with next(database.get_db()) as db:
        update = schemas.ExpenseStatusUpdate(status="approved_senior", comment="Утверждено CFO")
        crud.update_expense_status(db, expense_id, update)
    await callback.message.edit_text(callback.message.text + "\n\n✅ *Утверждено CFO*", parse_mode="Markdown")
    await callback.answer("Заявка утверждена!")

@router.callback_query(F.data.startswith("reject_senior_"))
async def handle_reject_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_senior_")
    with next(database.get_db()) as db:
        update = schemas.ExpenseStatusUpdate(status="rejected_senior", comment="Отклонено CFO")
        crud.update_expense_status(db, expense_id, update)
    await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CFO*", parse_mode="Markdown")
    await callback.answer("Заявка отклонена!")

@router.callback_query(F.data.startswith("approve_ceo_"))
async def handle_approve_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_ceo_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        update = schemas.ExpenseStatusUpdate(status="approved_ceo", comment="Одобрено CEO")
        crud.update_expense_status(db, expense_id, update)

    await callback.message.edit_text(callback.message.text + "\n\n✅ *Одобрено CEO*", parse_mode="Markdown")
    await callback.answer("Заявка одобрена CEO!")

    # Notifications
    admin_id = get_admin_chat_id()
    if admin_id:
        asyncio.create_task(send_ceo_decision_notification(admin_id, expense.request_id, float(expense.total_amount), expense.currency, True))
    for cfo_id in get_senior_financier_chat_ids():
        asyncio.create_task(send_ceo_decision_notification(cfo_id, expense.request_id, float(expense.total_amount), expense.currency, True))

@router.callback_query(F.data.startswith("reject_ceo_"))
async def handle_reject_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_ceo_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        update = schemas.ExpenseStatusUpdate(status="rejected_ceo", comment="Отклонено CEO")
        crud.update_expense_status(db, expense_id, update)

    await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CEO*", parse_mode="Markdown")
    await callback.answer("Заявка отклонена CEO!")

    admin_id = get_admin_chat_id()
    if admin_id:
        asyncio.create_task(send_ceo_decision_notification(admin_id, expense.request_id, float(expense.total_amount), expense.currency, False))
    for cfo_id in get_senior_financier_chat_ids():
        asyncio.create_task(send_ceo_decision_notification(cfo_id, expense.request_id, float(expense.total_amount), expense.currency, False))
