from aiogram import Router, types, F
from app.core import database
from app.db import models
from ..notifications import send_senior_notification

router = Router()

@router.message(F.text == "🔄 Проверить новые заявки")
async def handle_cfo_update(message: types.Message):
    tg_id = message.from_user.id
    
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == tg_id).first()
        if not user or user.position != "senior_financier":
            return

        # Находим все заявки со статусом pending_senior
        pending_requests = db.query(models.ExpenseRequest).filter(
            models.ExpenseRequest.status == "pending_senior"
        ).order_by(models.ExpenseRequest.date.asc()).limit(10).all()
        
        if not pending_requests:
            await message.answer("✅ Новых заявок для согласования нет.")
            return
            
        await message.answer(f"🔍 Найдено {len(pending_requests)} заявок (показаны 10 старейших):")
        
        for req in pending_requests:
            exp_dict = {
                "id": req.id,
                "project_name": req.project_name,
                "project_code": req.project_code,
                "created_by": req.created_by,
                "purpose": req.purpose,
                "request_id": req.request_id,
                "total_amount": req.total_amount,
                "currency": req.currency,
                "usd_rate": req.usd_rate,
            }
            await send_senior_notification(exp_dict, tg_id)
