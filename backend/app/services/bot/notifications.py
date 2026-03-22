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

_bot: Bot | None = None

def get_bot() -> Bot | None:
    global _bot
    token = os.getenv("BOT_TOKEN")
    if not token:
        return None
    if _bot is None:
        _bot = Bot(token=token)
    return _bot

# ---------------------------------------------------------------------------
# Generic send helper
# ---------------------------------------------------------------------------

async def _send_message(chat_id: int, text: str, reply_markup=None, parse_mode: str = "Markdown") -> None:
    """Send a single Telegram message using the shared bot instance."""
    bot = get_bot()
    if not bot:
        logger.warning(f"BOT_TOKEN not set, cannot send message to {chat_id}")
        return
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

async def send_admin_notification(expense: dict, admin_chat_id: int) -> None:
    base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
    dt_str = _format_expense_dt(expense["date"])

    project_name = expense.get("project_name") or "—"
    project_code = expense.get("project_code") or "—"
    created_by = expense["created_by"]
    purpose = expense["purpose"]
    request_id = expense["request_id"]
    total_amount = expense["total_amount"]
    currency = expense["currency"]
    usd_rate = expense.get("usd_rate")
    expense_id_db = expense["id"]
    request_type = expense.get("request_type")

    header = "🔴 *Safina Expense Tracker*"
    type_label = "Инвестиция"
    if request_type == "blank":
        header = "📋 *Safina: Новая заявка на БЛАНК*"
        type_label = "Бланк"
    elif request_type in ("blank_refund", "refund"):
        header = "🧾 *Safina: Заявление на ВОЗВРАТ*"
        type_label = "Возврат"

    text = (
        f"{header}\n"
        f"🟢 {project_name} ({project_code})\n"
        f"➡️ Параметры {type_label.lower()}а:\n"
        f"🔸 {created_by}\n"
        f"🔸 {purpose}\n"
        f"🆔 {request_id}\n"
        f"💵 {total_amount:,.2f} {currency}\n"
    )
    if usd_rate:
        text += f"📉 Курс: {float(usd_rate):,.2f} UZS/USD\n"
    text += f"🕒 {dt_str} (Ташкент)\n✅ Ожидает рассмотрения"

    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Скачать смету", callback_data=f"download_smeta_{expense_id_db}")
    builder.button(text="🖥 Открыть в системе", url=f"{base_url}/dashboard")
    builder.adjust(1)

    await _send_message(admin_chat_id, text, reply_markup=builder.as_markup())


# ---------------------------------------------------------------------------
# Senior Financier (CFO / Farrukh) notification
# ---------------------------------------------------------------------------

async def send_senior_notification(expense: dict, senior_chat_id: int) -> None:
    project_name = expense.get("project_name") or "—"
    project_code = expense.get("project_code") or "—"
    created_by = expense["created_by"]
    purpose = expense["purpose"]
    request_id_str = expense["request_id"]
    total_amount = expense["total_amount"]
    currency = expense["currency"]
    usd_rate = expense.get("usd_rate")
    expense_id_db = expense["id"]

    text = (
        f"🔵 *Safina | На согласование CFO*\n"
        f"🟢 {project_name} ({project_code})\n"
        f"🔸 Инициатор: {created_by}\n"
        f"🔸 Цель: {purpose}\n"
        f"🆔 {request_id_str}\n"
        f"💵 {total_amount:,.2f} {currency}\n"
    )
    if usd_rate:
        text += f"📉 Курс: {float(usd_rate):,.2f} UZS/USD\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Утвердить", callback_data=f"approve_senior_{expense_id_db}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_senior_{expense_id_db}")
    builder.button(text="📄 Скачать Excel смету", callback_data=f"download_excel_{expense_id_db}")
    builder.adjust(2, 1)

    await _send_message(senior_chat_id, text, reply_markup=builder.as_markup())


# ---------------------------------------------------------------------------
# CEO (Ganiev) notification
# ---------------------------------------------------------------------------

async def send_ceo_notification(expense: dict, ceo_chat_id: int) -> None:
    project_name = expense.get("project_name") or "—"
    project_code = expense.get("project_code") or "—"
    created_by = expense["created_by"]
    purpose = expense["purpose"]
    request_id_str = expense["request_id"]
    total_amount = expense["total_amount"]
    currency = expense["currency"]
    usd_rate = expense.get("usd_rate")
    expense_id_db = expense["id"]

    text = (
        f"🟣 *Safina | На согласование CEO*\n"
        f"🟢 {project_name} ({project_code})\n"
        f"🔸 Инициатор: {created_by}\n"
        f"🔸 Цель: {purpose}\n"
        f"🆔 {request_id_str}\n"
        f"💵 {total_amount:,.2f} {currency}\n"
    )
    if usd_rate:
        text += f"📉 Курс: {float(usd_rate):,.2f} UZS/USD\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"approve_ceo_{expense_id_db}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_ceo_{expense_id_db}")
    builder.button(text="📄 Скачать инвестицию", callback_data=f"download_excel_{expense_id_db}")
    builder.adjust(2, 1)

    await _send_message(ceo_chat_id, text, reply_markup=builder.as_markup())


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
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        users = db.query(models.TeamMember).filter(
            models.TeamMember.position == position,
            models.TeamMember.telegram_chat_id.isnot(None),
        ).all()
        return [u.telegram_chat_id for u in users]


def get_admin_chat_id() -> int | None:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting:
            return int(setting.value)
        return None


def set_admin_chat_id(chat_id: int) -> None:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting:
            setting.value = str(chat_id)
        else:
            setting = models.Setting(key="admin_chat_id", value=str(chat_id))
            db.add(setting)
        # Note: the commit is handled automatically by database_session


def get_senior_financier_chat_ids() -> list[int]:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        users = db.query(models.TeamMember).filter(
            models.TeamMember.position == "senior_financier",
            models.TeamMember.telegram_chat_id.isnot(None),
        ).all()
        return [u.telegram_chat_id for u in users]


def get_ceo_chat_id() -> int | None:
    """Return CEO Telegram chat_id (first linked CEO found)."""
    ids = _get_chat_id_by_position("ceo")
    return ids[0] if ids else None
