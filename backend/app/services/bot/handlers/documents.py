import os
from aiogram import Router, types, F

from app.core import database
from app.db import models
from app.services.docx.service import docx_service
from ..utils import run_sync

router = Router()

@router.callback_query(F.data.startswith("download_smeta_") | F.data.startswith("download_excel_"))
async def handle_download_document(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_smeta_").removeprefix("download_excel_")
    
    def generate_doc_task(e_id):
        with database.database_session() as db:
            expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == e_id).first()
            if not expense:
                return None, None
            
            # Use Buffered reader to get contents while session is open if needed, 
            # though docx_service usually returns a BytesIO
            stream = docx_service.generate_expense_docx(expense)
            content = stream.getvalue()
            
            tpl_label = expense.template_key.upper() if getattr(expense, 'template_key', None) else "BLANK"
            filename = f"{tpl_label}_{expense.request_id}.docx"
            return filename, content

    await callback.answer("Генерирую документ...")
    
    try:
        filename, content = await run_sync(generate_doc_task, expense_id)
        if not content:
            await callback.message.answer("❌ Заявка не найдена.")
            return
            
        doc = types.BufferedInputFile(content, filename=filename)
        await callback.message.answer_document(doc)
    except Exception as e:
        import logging
        logging.error(f"Error generating document for bot: {e}")
        await callback.message.answer("❌ Ошибка при генерации документа.")
