from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import json
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
async def send_admin_notification(expense, admin_chat_id: int):
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    # Clickuz style formatting
    text = (
        f"🔴 **Safina Expense Tracker**\n"
        f"🟢 {expense.project_name} ({expense.project_code})\n"
        f"➡️ Параметры заявки:\n"
        f"🔸 {expense.created_by}\n"
        f"🔸 {expense.purpose}\n"
        f"🆔 {expense.request_id}\n"
        f"💵 {expense.total_amount:,.2f} {expense.currency}\n"
        f"🕒 {expense.date.strftime('%H:%M:%S %d.%m.%Y')}\n"
        f"✅ Ожидает рассмотрения"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Скачать смету", callback_data=f"download_smeta_{expense.id}")
    
    try:
        await bot.send_message(admin_chat_id, text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
    finally:
        await bot.session.close()

def get_admin_chat_id():
    path = "admin_config.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f).get("admin_chat_id")
    return None

def set_admin_chat_id(chat_id: int):
    path = "admin_config.json"
    with open(path, "w") as f:
        json.dump({"admin_chat_id": chat_id}, f)
