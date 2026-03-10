"""
Telegram bot handlers.

Hierarchy:
  Zarina (employee)  → creates requests
  Safina (admin)     → receives all new request notifications
  CFO (Farrukh)      → receives forwarded requests, approves/rejects
  CEO (Ganiev)       → receives CFO-forwarded requests, final decision

Each role logs in via /start + login/password. The bot links telegram_chat_id
to the TeamMember row which is how future notifications are routed.
"""

import asyncio
import datetime
import os
import re

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from app.core import auth, database
from app.core.logging_config import get_logger
from app.db import models, schemas, crud
from app.services.docx.generator import generate_docx
from app.services.excel.generator import generate_smeta_excel
from .notifications import (
    set_admin_chat_id,
    get_admin_chat_id,
    send_admin_notification,
    send_ceo_decision_notification,
)
from .states import ExpenseWizard, RefundWizard

logger = get_logger(__name__)
router = Router()

TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def tashkent_now() -> datetime.datetime:
    return datetime.datetime.now(tz=TASHKENT_TZ)


def _get_user_position(login: str) -> str | None:
    """Sync DB lookup for a user's position."""
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()
        return user.position if user else None


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def get_confirm_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Добавить ещё позицию")
    b.button(text="Готово")
    return b.as_markup(resize_keyboard=True)

def get_date_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Сейчас")
    return b.as_markup(resize_keyboard=True)

def get_currency_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="UZS")
    b.button(text="USD")
    return b.as_markup(resize_keyboard=True)

def get_main_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Создать заявку (в боте)")
    b.button(text="Оформить возврат (в боте)")
    b.button(text="Создать заявку (Web-App)")
    b.button(text="Создать возврат (Web-App)")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_projects_kb(projects):
    b = ReplyKeyboardBuilder()
    for p in projects:
        b.button(text=f"{p.name} ({p.code})")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_retention_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Да")
    b.button(text="Нет")
    b.button(text="◀️ Назад")
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)


def get_back_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="◀️ Назад")
    return b.as_markup(resize_keyboard=True)


def get_reason_kb():
    """Пресет-клавиатура причин возврата с кнопкой Назад."""
    reasons = ["Переезд", "Отчисление", "Болезнь", "Другое"]
    b = ReplyKeyboardBuilder()
    for r in reasons:
        b.button(text=r)
    b.button(text="◀️ Назад")
    b.adjust(2, 2, 1)
    return b.as_markup(resize_keyboard=True)


def get_refund_confirm_markup(expense_id: str) -> InlineKeyboardMarkup:
    """Inline-кнопки редактирования полей на экране подтверждения."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ ID ученика",  callback_data="refund_edit_student_id"),
            InlineKeyboardButton(text="✏️ Причину",     callback_data="refund_edit_reason"),
        ],
        [
            InlineKeyboardButton(text="✏️ Сумму",       callback_data="refund_edit_amount"),
            InlineKeyboardButton(text="✏️ Карту",       callback_data="refund_edit_card_number"),
        ],
        [
            InlineKeyboardButton(text="✏️ Удержание",   callback_data="refund_edit_retention"),
            InlineKeyboardButton(text="✏️ Фото чека",   callback_data="refund_edit_receipt_photo"),
        ],
        [
            InlineKeyboardButton(text="✅ Отправить заявку Сафине", callback_data="refund_submit"),
        ],
    ])


# ---------------------------------------------------------------------------
# /start  — universal entry point for all roles
# ---------------------------------------------------------------------------

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id

    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == tg_id).first()
        if user:
            await state.update_data(user_id=user.id)
            if user.position == "ceo":
                await message.answer(
                    f"👋 С возвращением, {user.first_name} (CEO)!\n"
                    "Вы будете получать заявки для финального согласования.",
                    reply_markup=types.ReplyKeyboardRemove()
                )
            else:
                await message.answer(
                    f"С возвращением, {user.first_name}! Как хотите создать заявку?",
                    reply_markup=get_main_kb()
                )
            return

    # Also check if this is the Safina admin already registered
    admin_login = os.getenv("ADMIN_LOGIN", "safina")
    with next(database.get_db()) as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting and setting.value == str(tg_id):
            await message.answer("С возвращением, Сафина!", reply_markup=types.ReplyKeyboardRemove())
            return

    await message.answer(
        "Добро пожаловать в Thompson Finance Bot!\nПожалуйста, введите ваш логин:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ExpenseWizard.waiting_for_auth)


# ---------------------------------------------------------------------------
# Auth flow (shared by all roles)
# ---------------------------------------------------------------------------

@router.message(ExpenseWizard.waiting_for_auth)
async def process_login(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "login" not in data:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
        return

    login = data["login"]
    password = message.text
    tg_id = message.from_user.id

    # --- Safina (admin) ---
    admin_login = os.getenv("ADMIN_LOGIN", "safina")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    if login == admin_login and password == admin_password:
        set_admin_chat_id(tg_id)
        await message.answer(
            "✅ Вход выполнен (Администратор Сафина)!\n"
            "Вы будете получать уведомления о новых заявках.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        return

    # --- Team members (including CFO and CEO) ---
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()

        if not (user and auth.verify_password(password, user.password_hash)):
            await message.answer("❌ Неверный логин или пароль. Попробуйте снова:")
            await state.clear()
            await state.set_state(ExpenseWizard.waiting_for_auth)
            return

        if user.status != "active":
            await message.answer("❌ Ваш аккаунт заблокирован. Обратитесь к администратору.")
            await state.clear()
            return

        # Clear stale telegram_chat_id from another user if any
        db.query(models.TeamMember).filter(
            models.TeamMember.telegram_chat_id == tg_id,
            models.TeamMember.id != user.id
        ).update({models.TeamMember.telegram_chat_id: None})

        user.telegram_chat_id = tg_id
        db.commit()

        await state.update_data(user_id=user.id)

        # CEO — minimal menu
        if user.position == "ceo":
            await message.answer(
                f"✅ Авторизация успешна, {user.first_name} (CEO)!\n"
                "Вы будете получать заявки для финального согласования.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await state.clear()
            return

        # CFO (senior_financier) and regular employees — full create menu
        if len(user.projects) > 1:
            await message.answer("Авторизация успешна! Выберите проект:", reply_markup=get_projects_kb(user.projects))
            await state.set_state(ExpenseWizard.project_selection)
        elif len(user.projects) == 1:
            await state.update_data(project_id=user.projects[0].id)
            await message.answer(
                f"Авторизация успешна, {user.first_name}! Введите дату (ГГГГ-ММ-ДД) или «Сейчас»:",
                reply_markup=get_date_kb()
            )
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Авторизация успешна, но к вам не привязано ни одного проекта.")
            await state.clear()


# ---------------------------------------------------------------------------
# Admin /admin command (legacy support)
# ---------------------------------------------------------------------------

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    await message.answer("Введите логин администратора:")
    await state.set_state(ExpenseWizard.waiting_for_admin_login)

@router.message(ExpenseWizard.waiting_for_admin_login)
async def process_admin_login(message: types.Message, state: FSMContext):
    await state.update_data(admin_login=message.text)
    await message.answer("Введите пароль:")
    await state.set_state(ExpenseWizard.waiting_for_admin_password)

@router.message(ExpenseWizard.waiting_for_admin_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data["admin_login"] == os.getenv("ADMIN_LOGIN", "safina") and message.text == os.getenv("ADMIN_PASSWORD", "admin123"):
        set_admin_chat_id(message.from_user.id)
        await message.answer("✅ Вход выполнен! Уведомления будут приходить в этот чат.")
    else:
        await message.answer("❌ Неверный логин или пароль.")
    await state.clear()


# ---------------------------------------------------------------------------
# Web-App links
# ---------------------------------------------------------------------------

@router.message(F.text == "Создать заявку (Web-App)")
@router.message(Command("form"))
async def show_form_link(message: types.Message):
    base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}&type=expense"
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Открыть форму заявки", url=url)
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть форму заявки:\n_(Убедитесь, что вы авторизованы)_",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )

@router.message(F.text == "Создать возврат (Web-App)")
async def show_refund_form_webapplink(message: types.Message):
    """Открывает форму возврата как настоящий Telegram Mini-App overlay."""
    base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}&type=refund"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💸 Оформить возврат", web_app=WebAppInfo(url=url))
    ]])
    await message.answer(
        "Нажмите кнопку ниже — откроется форма возврата:",
        reply_markup=kb,
    )


# ---------------------------------------------------------------------------
# Expense creation wizard
# ---------------------------------------------------------------------------

@router.message(F.text == "Создать заявку (в боте)")
async def start_wizard_selection(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Пожалуйста, сначала авторизуйтесь с помощью /start")
            return
        if len(user.projects) > 1:
            await message.answer("Выберите проект:", reply_markup=get_projects_kb(user.projects))
            await state.set_state(ExpenseWizard.project_selection)
        elif len(user.projects) == 1:
            await state.update_data(project_id=user.projects[0].id)
            await message.answer("Введите дату (ГГГГ-ММ-ДД), или нажмите «Сейчас»:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("К вашему аккаунту не привязано ни одного проекта.")

@router.message(ExpenseWizard.project_selection)
async def process_project_selection(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        projects = db.query(models.Project).all()
        selected = next((p for p in projects if f"{p.name} ({p.code})" == message.text), None)
        if selected:
            await state.update_data(project_id=selected.id)
            await message.answer(f"Проект выбран: {selected.name}. Введите дату или «Сейчас»:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Пожалуйста, выберите проект из списка.")

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    val = message.text.lower()
    if val == "сейчас":
        d = tashkent_now().isoformat()
    else:
        try:
            d = datetime.datetime.strptime(val, "%Y-%m-%d").isoformat()
        except ValueError:
            await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД или «Сейчас»:", reply_markup=get_date_kb())
            return
    await state.update_data(date=d)
    await message.answer("Введите назначение расхода:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.purpose)

@router.message(ExpenseWizard.purpose)
async def process_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text, items=[])
    await message.answer("Добавление позиций сметы.\nВведите наименование товара/услуги:")
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.item_name)
async def process_item_name(message: types.Message, state: FSMContext):
    await state.update_data(current_item_name=message.text)
    await message.answer("Количество:")
    await state.set_state(ExpenseWizard.item_qty)

@router.message(ExpenseWizard.item_qty)
async def process_item_qty(message: types.Message, state: FSMContext):
    try:
        qty = float(message.text.replace(",", "."))
        await state.update_data(current_item_qty=qty)
        await message.answer("Сумма (за 1 единицу):")
        await state.set_state(ExpenseWizard.item_amount)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например: 10 или 10.5):")

@router.message(ExpenseWizard.item_amount)
async def process_item_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(current_item_amount=amount)
        await message.answer("Выберите валюту:", reply_markup=get_currency_kb())
        await state.set_state(ExpenseWizard.item_currency)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например: 1000 или 1500.50):")

@router.message(ExpenseWizard.item_currency)
async def process_item_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    if currency not in ("UZS", "USD"):
        await message.answer("Пожалуйста, выберите валюту (UZS или USD):", reply_markup=get_currency_kb())
        return
    data = await state.get_data()
    items = data.get("items", [])
    if items and items[0]["currency"] != currency:
        await message.answer(
            f"❌ В одной заявке должна быть одна валюта. Текущая: {items[0]['currency']}.\n"
            "Для другой валюты создайте новую заявку."
        )
        return
    items.append({
        "name": data["current_item_name"],
        "quantity": data["current_item_qty"],
        "amount": data["current_item_amount"],
        "currency": currency
    })
    await state.update_data(items=items)
    await message.answer("Позиция добавлена. Хотите добавить ещё?", reply_markup=get_confirm_kb())
    await state.set_state(ExpenseWizard.confirm)

@router.message(ExpenseWizard.confirm, F.text == "Добавить ещё позицию")
async def process_add_more(message: types.Message, state: FSMContext):
    await message.answer("Введите наименование товара/услуги:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.confirm, F.text == "Готово")
async def process_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    with next(database.get_db()) as db:
        try:
            total_amount = sum(i["amount"] * i["quantity"] for i in data["items"])
            currency = data["items"][0]["currency"] if data["items"] else "UZS"
            expense_create = schemas.ExpenseRequestCreate(
                purpose=data["purpose"],
                items=[schemas.ExpenseItemSchema(**i) for i in data["items"]],
                total_amount=total_amount,
                currency=currency,
                project_id=data["project_id"],
                date=datetime.datetime.fromisoformat(data["date"]),
            )
            db_expense = crud.create_expense_request(db, expense_create, user_id=data["user_id"])

            # Link telegram_chat_id if not yet done
            user = db.query(models.TeamMember).filter(models.TeamMember.id == data["user_id"]).first()
            if user and not user.telegram_chat_id:
                db.query(models.TeamMember).filter(
                    models.TeamMember.telegram_chat_id == message.from_user.id
                ).update({models.TeamMember.telegram_chat_id: None})
                user.telegram_chat_id = message.from_user.id
                db.commit()

            await message.answer(
                f"✅ Заявка {db_expense.request_id} успешно создана!\nСумма: {total_amount} {currency}",
                reply_markup=types.ReplyKeyboardRemove()
            )
        except Exception as e:
            logger.error(f"Error saving expense from bot: {e}", exc_info=True)
            await message.answer(f"❌ Ошибка при сохранении: {e}")
    await state.clear()


# ---------------------------------------------------------------------------
# Document download callbacks (shared across roles)
# ---------------------------------------------------------------------------

def _prepare_items_data(raw_items) -> list[dict]:
    """Parse raw JSON items from DB into a list of dicts for document generators."""
    import json
    if isinstance(raw_items, str):
        try:
            raw_items = json.loads(raw_items)
        except Exception:
            raw_items = []
    result = []
    if isinstance(raw_items, list):
        for idx, item in enumerate(raw_items):
            if isinstance(item, dict):
                try:
                    qty = float(item.get("quantity", 0))
                    price = float(item.get("amount", 0))
                    result.append({
                        "no": idx + 1,
                        "name": item.get("name", ""),
                        "quantity": qty,
                        "amount": price,
                        "price": price,
                        "unit_price": price,
                        "total": qty * price,
                    })
                except (ValueError, TypeError):
                    continue
    return result


@router.callback_query(F.data.startswith("download_smeta_"))
async def handle_download_smeta(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_smeta_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
        await callback.answer("Генерирую смету...")
        items_data = _prepare_items_data(expense.items)
        data = {
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": float(expense.total_amount),
            "currency": expense.currency,
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y"),
        }
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docx", "template.docx")
        try:
            file_stream = generate_docx(template_path, data)
            doc = types.BufferedInputFile(file_stream.read(), filename=f"smeta_{expense.request_id}.docx")
            await callback.message.answer_document(doc)
        except Exception as e:
            logger.error(f"Error generating smeta: {e}", exc_info=True)
            await callback.message.answer(f"❌ Ошибка генерации: {e}")


@router.callback_query(F.data.startswith("download_excel_"))
async def handle_download_excel(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("download_excel_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
        await callback.answer("Генерирую Excel смету...")
        raw = expense.items
        items_data = []
        import json
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    items_data.append({
                        "name": item.get("name", ""),
                        "quantity": float(item.get("quantity", 0)),
                        "price": float(item.get("amount", 0)),
                        "total": float(item.get("amount", 0)) * float(item.get("quantity", 0)),
                    })
        data = {
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y"),
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": float(expense.total_amount),
            "currency": expense.currency,
        }
        try:
            file_stream = generate_smeta_excel(data)
            doc = types.BufferedInputFile(file_stream.read(), filename=f"smeta_{expense.request_id}.xlsx")
            await callback.message.answer_document(doc)
        except Exception as e:
            logger.error(f"Error generating excel: {e}", exc_info=True)
            await callback.message.answer(f"❌ Ошибка генерации Excel: {e}")


# ---------------------------------------------------------------------------
# CFO (senior_financier) callbacks: approve / reject
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("approve_senior_"))
async def handle_approve_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_senior_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
        update = schemas.ExpenseStatusUpdate(status="approved_senior", comment="Утверждено CFO (Старшим финансистом)")
        crud.update_expense_status(db, expense_id, update)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ *Утверждено CFO*", parse_mode="Markdown"
        )
        await callback.answer("Заявка утверждена!")


@router.callback_query(F.data.startswith("reject_senior_"))
async def handle_reject_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_senior_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
        update = schemas.ExpenseStatusUpdate(status="rejected_senior", comment="Отклонено CFO (Старшим финансистом)")
        crud.update_expense_status(db, expense_id, update)
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ *Отклонено CFO*", parse_mode="Markdown"
        )
        await callback.answer("Заявка отклонена!")


# ---------------------------------------------------------------------------
# CEO (Ganiev) callbacks: approve / reject
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("approve_ceo_"))
async def handle_approve_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_ceo_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return

        update = schemas.ExpenseStatusUpdate(status="approved_ceo", comment="Одобрено CEO")
        crud.update_expense_status(db, expense_id, update)

        await callback.message.edit_text(
            callback.message.text + "\n\n✅ *Одобрено CEO*", parse_mode="Markdown"
        )
        await callback.answer("Заявка одобрена CEO!")

        # Notify Safina AND CFO about CEO's decision
        amount = float(expense.total_amount)
        currency = expense.currency
        request_id = expense.request_id

        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            asyncio.create_task(send_ceo_decision_notification(admin_chat_id, request_id, amount, currency, approved=True))

        from .notifications import get_senior_financier_chat_ids
        for cfo_chat_id in get_senior_financier_chat_ids():
            asyncio.create_task(send_ceo_decision_notification(cfo_chat_id, request_id, amount, currency, approved=True))


@router.callback_query(F.data.startswith("reject_ceo_"))
async def handle_reject_ceo(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("reject_ceo_")
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return

        update = schemas.ExpenseStatusUpdate(status="rejected_ceo", comment="Отклонено CEO")
        crud.update_expense_status(db, expense_id, update)

        await callback.message.edit_text(
            callback.message.text + "\n\n❌ *Отклонено CEO*", parse_mode="Markdown"
        )
        await callback.answer("Заявка отклонена CEO!")

        amount = float(expense.total_amount)
        currency = expense.currency
        request_id = expense.request_id

        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            asyncio.create_task(send_ceo_decision_notification(admin_chat_id, request_id, amount, currency, approved=False))

        from .notifications import get_senior_financier_chat_ids
        for cfo_chat_id in get_senior_financier_chat_ids():
            asyncio.create_task(send_ceo_decision_notification(cfo_chat_id, request_id, amount, currency, approved=False))


# ---------------------------------------------------------------------------
# Refund wizard
# ---------------------------------------------------------------------------

_BACK = "◀️ Назад"


@router.message(F.text == "Оформить возврат (в боте)")
async def start_refund_wizard(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(
            models.TeamMember.telegram_chat_id == message.from_user.id
        ).first()
        if not user:
            await message.answer("Пожалуйста, сначала авторизуйтесь с помощью /start")
            return
        await state.update_data(
            user_id=user.id,
            branch=user.branch,
            team=user.team,
        )
    await message.answer(
        "Шаг 1/6 — Введите ID ученика:",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(RefundWizard.student_id)


@router.message(RefundWizard.student_id)
async def process_refund_student_id(message: types.Message, state: FSMContext):
    await state.update_data(student_id=message.text)
    await message.answer(
        "Шаг 2/6 — Выберите или введите причину возврата:",
        reply_markup=get_reason_kb(),
    )
    await state.set_state(RefundWizard.reason)


@router.message(RefundWizard.reason)
async def process_refund_reason(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        hint = f" (текущий: {data.get('student_id', '—')})"
        await message.answer(
            f"Шаг 1/6 — Введите ID ученика{hint}:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.set_state(RefundWizard.student_id)
        return
    await state.update_data(reason=message.text)
    await message.answer(
        "Шаг 3/6 — Введите сумму возврата (только число):",
        reply_markup=get_back_kb(),
    )
    await state.set_state(RefundWizard.amount)


@router.message(RefundWizard.amount)
async def process_refund_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        hint = f" (текущая: {data.get('reason', '—')})"
        await message.answer(
            f"Шаг 2/6 — Выберите или введите причину возврата{hint}:",
            reply_markup=get_reason_kb(),
        )
        await state.set_state(RefundWizard.reason)
        return
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        await state.update_data(amount=amount)
        await message.answer(
            "Шаг 4/6 — Введите номер карты (16 цифр, без пробелов):",
            reply_markup=get_back_kb(),
        )
        await state.set_state(RefundWizard.card_number)
    except ValueError:
        await message.answer(
            "❌ Введите корректное число (например: 1500000):",
            reply_markup=get_back_kb(),
        )


@router.message(RefundWizard.card_number)
async def process_refund_card(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        hint = f" (текущая: {data.get('amount', '—')})"
        await message.answer(
            f"Шаг 3/6 — Введите сумму возврата{hint}:",
            reply_markup=get_back_kb(),
        )
        await state.set_state(RefundWizard.amount)
        return
    digits = re.sub(r"\D", "", message.text)
    if len(digits) != 16:
        await message.answer(
            f"❌ Номер карты должен содержать 16 цифр (введено {len(digits)}). Попробуйте ещё раз:",
            reply_markup=get_back_kb(),
        )
        return
    await state.update_data(card_number=digits)
    await message.answer(
        "Шаг 5/6 — Применяется ли удержание?",
        reply_markup=get_retention_kb(),
    )
    await state.set_state(RefundWizard.retention)


@router.message(RefundWizard.retention)
async def process_refund_retention(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        hint = f" (текущий: {data.get('card_number', '—')})"
        await message.answer(
            f"Шаг 4/6 — Введите номер карты (16 цифр){hint}:",
            reply_markup=get_back_kb(),
        )
        await state.set_state(RefundWizard.card_number)
        return
    val = message.text.lower()
    if val not in ("да", "нет"):
        await message.answer("Выберите Да или Нет.", reply_markup=get_retention_kb())
        return
    await state.update_data(retention=(val == "да"))
    await message.answer(
        "Шаг 6/6 — Отправьте фото чека:",
        reply_markup=get_back_kb(),
    )
    await state.set_state(RefundWizard.receipt_photo)


@router.message(RefundWizard.receipt_photo, F.photo)
async def process_refund_receipt(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(receipt_photo_file_id=photo_file_id)
    data = await state.get_data()
    retention_text = "Да" if data["retention"] else "Нет"
    text = (
        "✅ Проверьте данные возврата:\n\n"
        f"👤 ID ученика: {data['student_id']}\n"
        f"📝 Причина: {data['reason']}\n"
        f"💰 Сумма: {data['amount']:,.0f} UZS\n"
        f"💳 Карта: {data['card_number']}\n"
        f"✂️ Удержание: {retention_text}\n"
        f"🏢 Филиал: {data.get('branch') or '—'}\n"
        f"👥 Команда: {data.get('team') or '—'}\n\n"
        "Выберите действие:"
    )
    await message.answer_photo(
        photo_file_id,
        caption=text,
        reply_markup=get_refund_confirm_markup(expense_id=""),  # id ещё не создан
    )
    await message.answer(
        "Или нажмите ◀️ Назад:",
        reply_markup=get_back_kb(),
    )
    await state.set_state(RefundWizard.confirm)


@router.message(RefundWizard.receipt_photo, F.text == _BACK)
async def process_refund_receipt_back(message: types.Message, state: FSMContext):
    data = await state.get_data()
    retention_txt = "Да" if data.get("retention") else "Нет"
    await message.answer(
        f"Шаг 5/6 — Удержание было: {retention_txt}. Изменить?",
        reply_markup=get_retention_kb(),
    )
    await state.set_state(RefundWizard.retention)


@router.message(RefundWizard.receipt_photo)
async def process_refund_receipt_invalid(message: types.Message):
    await message.answer("Пожалуйста, отправьте именно ФОТО чека 📷")


# --- Confirm: Back (text button)

@router.message(RefundWizard.confirm, F.text == _BACK)
async def process_refund_confirm_back(message: types.Message, state: FSMContext):
    await message.answer(
        "Шаг 6/6 — Отправьте новое фото чека:",
        reply_markup=get_back_kb(),
    )
    await state.set_state(RefundWizard.receipt_photo)


# --- Confirm: inline field-edit callbacks

_FIELD_PROMPTS = {
    "student_id":    (RefundWizard.student_id,   "Шаг 1/6 — Введите ID ученика:",              None),
    "reason":        (RefundWizard.reason,        "Шаг 2/6 — Введите причину возврата:",       "reason_kb"),
    "amount":        (RefundWizard.amount,        "Шаг 3/6 — Введите сумму возврата:",         "back_kb"),
    "card_number":   (RefundWizard.card_number,   "Шаг 4/6 — Введите номер карты (16 цифр):", "back_kb"),
    "retention":     (RefundWizard.retention,     "Шаг 5/6 — Применяется ли удержание?",      "retention_kb"),
    "receipt_photo": (RefundWizard.receipt_photo, "Шаг 6/6 — Отправьте новое фото чека:",     "back_kb"),
}


@router.callback_query(F.data.startswith("refund_edit_"))
async def handle_refund_edit(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.removeprefix("refund_edit_")
    if field not in _FIELD_PROMPTS:
        await callback.answer("Неизвестное поле")
        return
    target_state, prompt, kb_type = _FIELD_PROMPTS[field]
    if kb_type == "reason_kb":
        kb = get_reason_kb()
    elif kb_type == "retention_kb":
        kb = get_retention_kb()
    elif kb_type == "back_kb":
        kb = get_back_kb()
    else:
        kb = types.ReplyKeyboardRemove()
    await callback.message.answer(prompt, reply_markup=kb)
    await state.set_state(target_state)
    await callback.answer()


@router.callback_query(F.data == "refund_submit")
async def handle_refund_submit_callback(callback: types.CallbackQuery, state: FSMContext):
    """Финальная отправка возврата через inline-кнопку на экране подтверждения."""
    data = await state.get_data()
    with next(database.get_db()) as db:
        try:
            from app.services.refund.service import create_refund
            db_expense = create_refund(
                db,
                student_id=data["student_id"],
                reason=data["reason"],
                amount=data["amount"],
                card_number=data["card_number"],
                retention=data["retention"],
                receipt_photo_ref=data["receipt_photo_file_id"],
                user_id=data.get("user_id"),
                branch=data.get("branch"),
                team=data.get("team"),
            )
            await callback.message.answer(
                f"✅ Возврат {db_expense.request_id} отправлен Сафине!\nОжидайте рассмотрения.",
                reply_markup=get_main_kb(),
            )
            admin_chat_id = get_admin_chat_id()
            if admin_chat_id:
                asyncio.create_task(send_admin_notification(db_expense.id, admin_chat_id))
        except ValueError as e:
            await callback.message.answer(f"❌ Ошибка: {e}")
        except Exception as e:
            logger.error("Error saving refund from bot: %s", e, exc_info=True)
            await callback.message.answer(f"❌ Ошибка при сохранении: {e}")
    await state.clear()
    await callback.answer()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_handlers(dp):
    dp.include_router(router)
