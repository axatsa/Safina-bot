import asyncio
import os
from aiogram import Router, types, F

from app.core import database
from app.db import models, schemas
from app.services.core.expense_service import expense_service
from ..notifications import send_ceo_decision_notification, get_admin_chat_id, get_senior_financier_chat_ids
from app.services.notifications.sse import publish_notification
from ..utils import run_sync

router = Router()

@router.callback_query(F.data.startswith("approve_senior_"))
async def handle_approve_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_senior_")
    
    def approve_senior_task(e_id, tg_id):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.telegram_chat_id == tg_id).first()
            if not user or user.position not in ["senior_financier", "admin"]:
                return "no_permission", None

            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return "not_found", None
                
            if expense.status != "pending_senior":
                return f"already_processed:{expense.status}", None

            update = schemas.ExpenseStatusUpdate(status="approved_senior", comment="Утверждено CFO")
            expense_service.update_status(db, e_id, update, user_id=user.id, user_name=f"{user.last_name} {user.first_name} (CFO)")
            return "ok", expense.request_id

    status, req_id = await run_sync(approve_senior_task, expense_id, callback.from_user.id)
    
    if status == "no_permission":
        await callback.answer("У вас нет прав для этого действия", show_alert=True)
    elif status == "not_found":
        await callback.answer("Ошибка: Заявка не найдена", show_alert=True)
    elif status.startswith("already_processed"):
        curr_status = status.split(":")[1]
        await callback.answer(f"Заявка уже обработана (статус: {curr_status})", show_alert=True)
    else:
        await publish_notification(
            "notifications:admin",
            {"title": "Статус обновлен", "message": f"Заявка {req_id}: Одобрено CFO"}
        )
        await callback.message.edit_text(callback.message.text + "\n\n✅ *Утверждено CFO*", parse_mode="Markdown")
        await callback.answer("Инвестиция утверждена!")

@router.callback_query(F.data.startswith("reject_senior_"))
async def handle_reject_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_senior_")
    
    def reject_senior_task(e_id, tg_id):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.telegram_chat_id == tg_id).first()
            if not user or user.position not in ["senior_financier", "admin"]:
                return "no_permission", None

            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return "not_found", None
                
            if expense.status != "pending_senior":
                return f"already_processed:{expense.status}", None

            update = schemas.ExpenseStatusUpdate(status="rejected_senior", comment="Отклонено CFO")
            expense_service.update_status(db, e_id, update, user_id=user.id, user_name=f"{user.last_name} {user.first_name} (CFO)")
            return "ok", expense.request_id

    status, req_id = await run_sync(reject_senior_task, expense_id, callback.from_user.id)
    
    if status == "no_permission":
        await callback.answer("У вас нет прав для этого действия", show_alert=True)
    elif status == "not_found":
        await callback.answer("Ошибка: Заявка не найдена", show_alert=True)
    elif status.startswith("already_processed"):
        curr_status = status.split(":")[1]
        await callback.answer(f"Заявка уже обработана (статус: {curr_status})", show_alert=True)
    else:
        await publish_notification(
            "notifications:admin",
            {"title": "Статус обновлен", "message": f"Заявка {req_id}: Отклонено CFO"}
        )
        await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CFO*", parse_mode="Markdown")
        await callback.answer("Инвестиция отклонена!")

@router.callback_query(F.data.startswith("approve_ceo_"))
async def handle_approve_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_ceo_")
    
    def approve_ceo_task(e_id, tg_id):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.telegram_chat_id == tg_id).first()
            if not user or user.position != "ceo":
                return "no_permission", None, None, None

            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return "not_found", None, None, None
                
            if expense.status != "pending_ceo":
                return f"already_processed:{expense.status}", None, None, None
                
            update = schemas.ExpenseStatusUpdate(status="approved_ceo", comment="Одобрено CEO")
            expense_service.update_status(db, e_id, update, user_id=user.id, user_name=f"{user.last_name} {user.first_name} (CEO)")
            
            return "ok", expense.request_id, expense.total_amount, expense.currency

    status, req_id, amount, currency = await run_sync(approve_ceo_task, expense_id, callback.from_user.id)
    
    if status == "no_permission":
        await callback.answer("У вас нет прав для этого действия (Только CEO)", show_alert=True)
    elif status == "not_found":
        await callback.answer("Ошибка: Заявка не найдена", show_alert=True)
    elif status.startswith("already_processed"):
        curr_status = status.split(":")[1]
        await callback.answer(f"Заявка уже обработана (статус: {curr_status})", show_alert=True)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n✅ *Одобрено CEO*", parse_mode="Markdown")
        await callback.answer("Инвестиция одобрена CEO!")

        await publish_notification(
            "notifications:admin",
            {"title": "Статус одобрен CEO", "message": f"Заявка {req_id} одобрена Г-ном Ганиевым."}
        )

        admin_id = await run_sync(get_admin_chat_id)
        cfo_ids = await run_sync(get_senior_financier_chat_ids)
        
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
    
    def reject_ceo_task(e_id, tg_id):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.telegram_chat_id == tg_id).first()
            if not user or user.position != "ceo":
                return "no_permission", None, None, None

            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return "not_found", None, None, None
                
            if expense.status != "pending_ceo":
                return f"already_processed:{expense.status}", None, None, None
                
            update = schemas.ExpenseStatusUpdate(status="rejected_ceo", comment="Отклонено CEO")
            expense_service.update_status(db, e_id, update, user_id=user.id, user_name=f"{user.last_name} {user.first_name} (CEO)")
            
            return "ok", expense.request_id, expense.total_amount, expense.currency

    status, req_id, amount, currency = await run_sync(reject_ceo_task, expense_id, callback.from_user.id)
    
    if status == "no_permission":
        await callback.answer("У вас нет прав для этого действия (Только CEO)", show_alert=True)
    elif status == "not_found":
        await callback.answer("Ошибка: Заявка не найдена", show_alert=True)
    elif status.startswith("already_processed"):
        curr_status = status.split(":")[1]
        await callback.answer(f"Заявка уже обработана (статус: {curr_status})", show_alert=True)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n❌ *Отклонено CEO*", parse_mode="Markdown")
        await callback.answer("Инвестиция отклонена CEO!")

        await publish_notification(
            "notifications:admin",
            {"title": "Статус отклонен CEO", "message": f"Заявка {req_id} отклонена CEO."}
        )

        admin_id = await run_sync(get_admin_chat_id)
        cfo_ids = await run_sync(get_senior_financier_chat_ids)
        
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
    
    def generate_docx_task(e_id):
        from app.services.docx.service import docx_service
        with database.database_session() as db:
            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return None, None
            stream = docx_service.generate_expense_docx(expense)
            return f"smeta_{expense.request_id}.docx", stream.getvalue()

    try:
        filename, content = await run_sync(generate_docx_task, expense_id)
        if not content:
            await callback.answer("Заявка не найдена")
            return
            
        input_file = types.BufferedInputFile(content, filename=filename)
        await callback.message.answer_document(input_file)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Ошибка генерации: {e}")

@router.callback_query(F.data.startswith("download_excel_"))
async def handle_download_excel(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_excel_")
    
    def generate_excel_task(e_id):
        from app.services.analytics import export as export_service
        with database.database_session() as db:
            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return None, None
            stream = export_service.generate_expenses_xlsx([expense])
            return f"report_{expense.request_id}.xlsx", stream.getvalue()

    try:
        filename, content = await run_sync(generate_excel_task, expense_id)
        if not content:
            await callback.answer("Заявка не найдена")
            return
            
        input_file = types.BufferedInputFile(content, filename=filename)
        await callback.message.answer_document(input_file)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Ошибка генерации: {e}")
