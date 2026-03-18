"""
Bot notification helpers.

All functions that send Telegram messages are async and create a fresh Bot
instance per call so they are safe to run from background tasks.

For scalability: to add a new role's notifications, add a helper function
following the pattern of send_senior_notification / send_ceo_notification.
"""

import datetime
import os
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

from app.core.logging_config import get_logger
from decimal import Decimal

logger = get_logger(__name__)
TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

# Persistent bot instance
bot = Bot(token=os.getenv("BOT_TOKEN"))

# ---------------------------------------------------------------------------
# Generic send helper
# ---------------------------------------------------------------------------

async def _send_message(chat_id: int, text: str, reply_markup=None, parse_mode: str = "Markdown") -> None:
    """Send a single Telegram message using the shared bot instance."""
    try:
        await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")


def _format_expense_dt(expense_date: datetime.datetime) -> str:
    """Return expense datetime formatted in Tashkent time."""
    if expense_date.tzinfo is None:
        from datetime import timezone as dt_timezone
        expense_date = expense_date.replace(tzinfo=dt_timezone.utc).astimezone(TASHKENT_TZ)
    else:
        expense_date = expense_date.astimezone(TASHKENT_TZ)
    return expense_date.strftime("%H:%M:%S %d.%m.%Y")


# ---------------------------------------------------------------------------
# Status notifications (to the request creator via Telegram)
# ---------------------------------------------------------------------------

async def send_status_notification(
    chat_id: int,
    request_id: str,
    raw_status: str,
    amount: Decimal,
    currency: str,
    comment: str | None = None,
) -> None:
    """Notify the submitter about a status change."""
    status_map = {
        "request":       ("Запрос", "⏳"),
        "review":        ("На рассмотрении", "⏳"),
        "confirmed":     ("Подтверждено", "✅"),
        "declined":      ("Отклонено", "❌"),
        "revision":      ("Возврат на доработку", "🔄"),
        "archived":      ("Архивировано", "📦"),
        "pending_senior":("Отправлено CFO", "📨"),
        "approved_senior":("Одобрено CFO", "✅"),
        "rejected_senior":("Отклонено CFO", "❌"),
        "pending_ceo":   ("Отправлено CEO", "📨"),
        "approved_ceo":  ("Одобрено CEO", "✅"),
        "rejected_ceo":  ("Отклонено CEO", "❌"),
    }
    status_text, status_emoji = status_map.get(raw_status, (raw_status, "📌"))
    text = (
        f"{status_emoji} Инвестиция {request_id}\n"
        f"📌 Статус: {status_text}\n"
        f"💰 Сумма: {amount} {currency}\n"
    )
    if comment:
        text += f"\n💬 Комментарий: {comment}"
    await _send_message(chat_id, text)


# ---------------------------------------------------------------------------
# Admin (Safina) notification — new request arrived
# ---------------------------------------------------------------------------

async def send_admin_notification(expense_id: str, admin_chat_id: int) -> None:
    """Notify Safina (web-admin) about a newly created expense."""
    from app.core import database
    from app.db import models

    db = next(database.get_db())
    try:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            print(f"[TG] Expense {expense_id} not found for admin notification")
            return

        base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
        dt_str = _format_expense_dt(expense.date)

        header = "🔴 *Safina Expense Tracker*"
        type_label = "Инвестиция"
        if expense.request_type == "blank":
            header = "📋 *Safina: Новая заявка на БЛАНК*"
            type_label = "Бланк"
        elif expense.request_type == "blank_refund":
            header = "🧾 *Safina: Заявление на ВОЗВРАТ*"
            type_label = "Возврат"
        elif expense.request_type == "refund":
            header = "🧾 *Safina: Заявление на ВОЗВРАТ*"
            type_label = "Возврат"

        text = (
            f"{header}\n"
            f"🟢 {expense.project_name} ({expense.project_code})\n"
            f"➡️ Параметры {type_label.lower()}а:\n"
            f"🔸 {expense.created_by}\n"
            f"🔸 {expense.purpose}\n"
            f"🆔 {expense.request_id}\n"
            f"💵 {expense.total_amount:,.2f} {expense.currency}\n"
        )
        
        if expense.usd_rate:
            text += f"📉 Курс: {Decimal(str(expense.usd_rate)):,.2f} UZS/USD\n"
            
        text += (
            f"🕒 {dt_str} (Ташкент)\n"
            f"✅ Ожидает рассмотрения"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="📄 Скачать смету", callback_data=f"download_smeta_{expense.id}")
        builder.button(text="🖥 Открыть в системе", url=f"{base_url}/dashboard")
        builder.adjust(1)

        await _send_message(admin_chat_id, text, reply_markup=builder.as_markup())
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Senior Financier (CFO / Farrukh) notification
# ---------------------------------------------------------------------------

async def send_senior_notification(expense_id: str, senior_chat_id: int) -> None:
    """Send approval-request notification to CFO."""
    from app.core import database
    from app.db import models

    db = next(database.get_db())
    try:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            print(f"[TG] Expense {expense_id} not found for senior notification")
            return

        text = (
            f"🔵 *Safina | На согласование CFO*\n"
            f"🟢 {expense.project_name} ({expense.project_code})\n"
            f"🔸 Инициатор: {expense.created_by}\n"
            f"🔸 Цель: {expense.purpose}\n"
            f"🆔 {expense.request_id}\n"
            f"💵 {expense.total_amount:,.2f} {expense.currency}\n"
        )
        if expense.usd_rate:
            text += f"📉 Курс: {Decimal(str(expense.usd_rate)):,.2f} UZS/USD\n"
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Утвердить", callback_data=f"approve_senior_{expense.id}")
        builder.button(text="❌ Отклонить", callback_data=f"reject_senior_{expense.id}")
        builder.button(text="📄 Скачать Excel смету", callback_data=f"download_excel_{expense.id}")
        builder.adjust(2, 1)

        await _send_message(senior_chat_id, text, reply_markup=builder.as_markup())
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CEO (Ganiev) notification
# ---------------------------------------------------------------------------

async def send_ceo_notification(expense_id: str, ceo_chat_id: int) -> None:
    """Send approval-request notification to CEO with 3 action buttons."""
    from app.core import database
    from app.db import models

    db = next(database.get_db())
    try:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            print(f"[TG] Expense {expense_id} not found for CEO notification")
            return

        text = (
            f"🟣 *Safina | На согласование CEO*\n"
            f"🟢 {expense.project_name} ({expense.project_code})\n"
            f"🔸 Инициатор: {expense.created_by}\n"
            f"🔸 Цель: {expense.purpose}\n"
            f"🆔 {expense.request_id}\n"
            f"💵 {expense.total_amount:,.2f} {expense.currency}\n"
        )
        if expense.usd_rate:
            text += f"📉 Курс: {Decimal(str(expense.usd_rate)):,.2f} UZS/USD\n"
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Одобрить",  callback_data=f"approve_ceo_{expense.id}")
        builder.button(text="❌ Отклонить", callback_data=f"reject_ceo_{expense.id}")
        builder.button(text="📄 Скачать инвестицию", callback_data=f"download_excel_{expense.id}")
        builder.adjust(2, 1)

        await _send_message(ceo_chat_id, text, reply_markup=builder.as_markup())
    finally:
        db.close()


async def send_ceo_decision_notification(
    chat_id: int,
    request_id: str,
    total_amount: Decimal,
    currency: str,
    approved: bool,
    comment: str | None = None,
) -> None:
    """Notify Safina AND CFO about CEO's final decision."""
    emoji = "✅" if approved else "❌"
    decision = "Одобрено CEO" if approved else "Отклонено CEO"
    text = (
        f"{emoji} *Решение CEO по инвестиции {request_id}*\n"
        f"📌 Статус: {decision}\n"
        f"💰 Сумма: {total_amount:,.2f} {currency}\n"
    )
    if comment:
        text += f"\n💬 Комментарий: {comment}"
    await _send_message(chat_id, text)


# ---------------------------------------------------------------------------
# DB helpers  (sync — safe to call from sync routes)
# ---------------------------------------------------------------------------

def _get_chat_id_by_position(position: str) -> list[int]:
    """Return list of telegram_chat_ids for members with the given position."""
    from app.core import database
    from app.db import models

    with next(database.get_db()) as db:
        users = db.query(models.TeamMember).filter(
            models.TeamMember.position == position,
            models.TeamMember.telegram_chat_id.isnot(None),
        ).all()
        return [u.telegram_chat_id for u in users]


def get_admin_chat_id() -> int | None:
    """Return Safina's linked Telegram chat_id from Settings table."""
    from app.core import database
    from app.db import models

    with next(database.get_db()) as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting:
            return int(setting.value)
    return None


def set_admin_chat_id(chat_id: int) -> None:
    """Persist Safina's Telegram chat_id in Settings."""
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


def get_senior_financier_chat_ids() -> list[int]:
    """Return all CFO (senior_financier) Telegram chat IDs."""
    return _get_chat_id_by_position("senior_financier")


def get_ceo_chat_id() -> int | None:
    """Return CEO Telegram chat_id (first linked CEO found)."""
    ids = _get_chat_id_by_position("ceo")
    return ids[0] if ids else None
