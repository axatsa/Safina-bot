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
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == callback.from_user.id).first()
        if not user or user.position not in ["senior_financier", "admin"]:
            await callback.answer("У вас нет прав для этого действия", show_alert=True)
            return

        update = schemas.ExpenseStatusUpdate(status="approved_senior", comment="Утверждено CFO")
        crud.update_expense_status(db, expense_id, update, user_name=f"{user.last_name} {user.first_name} (CFO)")
    
    await callback.message.edit_text(callback.message.text + "\n\n✅ *Утверждено CFO*", parse_mode="Markdown")
    await callback.answer("Инвестиция утверждена!")

@router.callback_query(F.data.startswith("reject_senior_"))
async def handle_reject_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_senior_")
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == callback.from_user.id).first()
        if not user or user.position not in ["senior_financier", "admin"]:
            await callback.answer("У вас нет прав для этого действия", show_alert=True)
            return

        update = schemas.ExpenseStatusUpdate(status="rejected_senior", comment="Отклонено CFO")
        crud.update_expense_status(db, expense_id, update, user_name=f"{user.last_name} {user.first_name} (CFO)")
    
    await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CFO*", parse_mode="Markdown")
    await callback.answer("Инвестиция отклонена!")

@router.callback_query(F.data.startswith("approve_ceo_"))
async def handle_approve_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_ceo_")
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == callback.from_user.id).first()
        if not user or user.position != "ceo":
            await callback.answer("У вас нет прав для этого действия (Только CEO)", show_alert=True)
            return

        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Ошибка: Заявка не найдена")
            return
            
        update = schemas.ExpenseStatusUpdate(status="approved_ceo", comment="Одобрено CEO")
        crud.update_expense_status(db, expense_id, update, user_name=f"{user.last_name} {user.first_name} (CEO)")
        
        # Сохраняем данные для уведомлений ДО выхода из сессии
        req_id = expense.request_id
        from decimal import Decimal
        amount = Decimal(str(expense.total_amount))
        currency = expense.currency

    await callback.message.edit_text(callback.message.text + "\n\n✅ *Одобрено CEO*", parse_mode="Markdown")
    await callback.answer("Инвестиция одобрена CEO!")

    # Notifications
    admin_id = get_admin_chat_id()
    cfo_ids = get_senior_financier_chat_ids()
    
    tasks = []
    if admin_id:
        tasks.append(send_ceo_decision_notification(admin_id, req_id, amount, currency, True))
    
    for cfo_id in cfo_ids:
        tasks.append(send_ceo_decision_notification(cfo_id, req_id, amount, currency, True))
        
    if tasks:
        await asyncio.gather(*tasks)

@router.callback_query(F.data.startswith("reject_ceo_"))
async def handle_reject_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_ceo_")
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == callback.from_user.id).first()
        if not user or user.position != "ceo":
            await callback.answer("У вас нет прав для этого действия (Только CEO)", show_alert=True)
            return

        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Ошибка: Заявка не найдена")
            return
            
        update = schemas.ExpenseStatusUpdate(status="rejected_ceo", comment="Отклонено CEO")
        crud.update_expense_status(db, expense_id, update, user_name=f"{user.last_name} {user.first_name} (CEO)")
        
        # Сохраняем данные для уведомлений ДО выхода из сессии
        req_id = expense.request_id
        from decimal import Decimal
        amount = Decimal(str(expense.total_amount))
        currency = expense.currency

    await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CEO*", parse_mode="Markdown")
    await callback.answer("Инвестиция отклонена CEO!")

    admin_id = get_admin_chat_id()
    cfo_ids = get_senior_financier_chat_ids()
    
    tasks = []
    if admin_id:
        tasks.append(send_ceo_decision_notification(admin_id, req_id, amount, currency, False))
        
    for cfo_id in cfo_ids:
        tasks.append(send_ceo_decision_notification(cfo_id, req_id, amount, currency, False))
        
    if tasks:
        await asyncio.gather(*tasks)

@router.callback_query(F.data.startswith("download_smeta_"))
async def handle_download_smeta(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_smeta_")
    from app.services.docx.service import docx_service
    
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
            
        try:
            stream = docx_service.generate_expense_docx(expense)
            fname = f"smeta_{expense.request_id}.docx"
            input_file = types.BufferedInputFile(stream.getvalue(), filename=fname)
            await callback.message.answer_document(input_file)
            await callback.answer()
        except Exception as e:
            await callback.answer(f"Ошибка генерации: {e}")

@router.callback_query(F.data.startswith("download_excel_"))
async def handle_download_excel(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_excel_")
    from app.services.analytics import export as export_service
    
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
            
        try:
            # For a single expense, we still use the export service but with a list of one
            stream = export_service.generate_expenses_xlsx([expense])
            fname = f"report_{expense.request_id}.xlsx"
            input_file = types.BufferedInputFile(stream.getvalue(), filename=fname)
            await callback.message.answer_document(input_file)
            await callback.answer()
        except Exception as e:
            await callback.answer(f"Ошибка генерации: {e}")
