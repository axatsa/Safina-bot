from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

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
async def send_admin_notification(expense_id: str, admin_chat_id: int):
    from app.core import database
    from app.db import models

    
    # Get a fresh DB session
    db = next(database.get_db())
    try:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            print(f"Expense {expense_id} not found for notification")
            return

        bot = Bot(token=os.getenv("BOT_TOKEN"))
        base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")

        # Convert expense date to Tashkent time for display
        if expense.date.tzinfo is None:
            # Treat stored date as UTC, convert to Tashkent (UTC+5)
            from datetime import timezone as dt_timezone
            expense_dt = expense.date.replace(tzinfo=dt_timezone.utc).astimezone(TASHKENT_TZ)
        else:
            expense_dt = expense.date.astimezone(TASHKENT_TZ)

        text = (
            f"🔴 *Safina Expense Tracker*\n"
            f"🟢 {expense.project_name} ({expense.project_code})\n"
            f"➡️ Параметры заявки:\n"
            f"🔸 {expense.created_by}\n"
            f"🔸 {expense.purpose}\n"
            f"🆔 {expense.request_id}\n"
            f"💵 {expense.total_amount:,.2f} {expense.currency}\n"
            f"🕒 {expense_dt.strftime('%H:%M:%S %d.%m.%Y')} (Ташкент)\n"
            f"✅ Ожидает рассмотрения"
        )

        dashboard_url = f"{base_url}/dashboard"

        builder = InlineKeyboardBuilder()
        builder.button(text="📄 Скачать смету", callback_data=f"download_smeta_{expense.id}")
        builder.button(text="🖥 Открыть в системе", url=dashboard_url)
        builder.adjust(1)

        try:
            await bot.send_message(admin_chat_id, text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
        finally:
            await bot.session.close()
    finally:
        db.close()

def get_admin_chat_id():
    from app.core import database
    from app.db import models
    with next(database.get_db()) as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting:
            return int(setting.value)
    return None

def set_admin_chat_id(chat_id: int):
    from app.core import database
    from app.db import models
    with next(database.get_db()) as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting:
            setting.value = str(chat_id)
        else:
            setting = models.Setting(key="admin_chat_id", value=str(chat_id))
            db.add(setting)
        db.commit()
