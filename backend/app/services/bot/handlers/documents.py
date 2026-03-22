import os
from aiogram import Router, types, F

from app.core import database
from app.db import models
from app.services.docx.service import docx_service

router = Router()

@router.callback_query(F.data.startswith("download_smeta_") | F.data.startswith("download_excel_"))
async def handle_download_document(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_smeta_").removeprefix("download_excel_")
    with database.database_session() as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Не найдено")
            return
        await callback.answer("Генерирую документ...")
        
        try:
            file_stream = docx_service.generate_expense_docx(expense)
            
            # Choose filename based on template or request_id
            tpl_label = expense.template_key.upper() if getattr(expense, 'template_key', None) else "BLANK"
            filename = f"{tpl_label}_{expense.request_id}.docx"
            
            doc = types.BufferedInputFile(file_stream.read(), filename=filename)
            await callback.message.answer_document(doc)
        except Exception as e:
            import logging
            logging.error(f"Error generating document for bot: {e}")
            await callback.message.answer("❌ Ошибка при генерации документа.")
