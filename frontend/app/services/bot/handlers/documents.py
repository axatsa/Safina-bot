import os
from aiogram import Router, types, F

from app.core import database
from app.db import models
from app.services.docx.generator import generate_docx
from app.services.excel.generator import generate_smeta_excel
from ..utils import prepare_items_data

router = Router()

@router.callback_query(F.data.startswith("download_smeta_"))
async def handle_download_smeta(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_smeta_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Не найдено")
            return
        await callback.answer("Генерирую Docx...")
        items_data = prepare_items_data(expense.items)
        data = {
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": float(expense.total_amount),
            "currency": expense.currency,
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y"),
        }
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docx", "template.docx")
        file_stream = generate_docx(template_path, data)
        doc = types.BufferedInputFile(file_stream.read(), filename=f"smeta_{expense.request_id}.docx")
        await callback.message.answer_document(doc)

@router.callback_query(F.data.startswith("download_excel_"))
async def handle_download_excel(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_excel_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Не найдено")
            return
        await callback.answer("Генерирую Excel...")
        items_data = prepare_items_data(expense.items)
        data = {
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y"),
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": float(expense.total_amount),
            "currency": expense.currency,
        }
        file_stream = generate_smeta_excel(data)
        doc = types.BufferedInputFile(file_stream.read(), filename=f"smeta_{expense.request_id}.xlsx")
        await callback.message.answer_document(doc)
