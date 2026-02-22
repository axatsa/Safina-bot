from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

async def send_status_notification(chat_id: int, request_id: str, raw_status: str, amount: float, currency: str, comment: str = None):
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    status_map = {
        "request": ("Запрос", "⏳"),
        "review": ("На рассмотрении", "⏳"),
        "confirmed": ("Подтверждено", "✅"),
        "declined": ("Отклонено", "❌"),
        "revision": ("Возврат на доработку", "🔄"),
        "archived": ("Архивировано", "📦")
    }
    
    status_text, status_emoji = status_map.get(raw_status, (raw_status, "📌"))
    
    text = (
        f"{status_emoji} Заявка {request_id}\n"
        f"📌 Статус: {status_text}\n"
        f"💰 Сумма: {amount} {currency}\n"
    )
    
    if comment:
        text += f"\n💬 Комментарий: {comment}"
        
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Failed to send notification: {e}")
    finally:
        await bot.session.close()
