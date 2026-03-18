from aiogram import Router, types, F
from app.core import database
from app.db import models
from ..notifications import send_ceo_notification

router = Router()

@router.message(F.text == "🔄 Проверить новые заявки")
async def handle_ceo_update(message: types.Message):
    tg_id = message.from_user.id
    
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == tg_id).first()
        if not user or user.position != "ceo":
            return

        # Находим все заявки со статусом pending_ceo
        pending_requests = db.query(models.ExpenseRequest).filter(
            models.ExpenseRequest.status == "pending_ceo"
        ).all()
        
        if not pending_requests:
            await message.answer("✅ Новых заявок для согласования нет.")
            return
            
        await message.answer(f"🔍 Найдено {len(pending_requests)} заявок, ожидающих вашего решения:")
        
        for req in pending_requests:
            await send_ceo_notification(req.id, tg_id)
