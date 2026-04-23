from aiogram import Router, types, F
import os
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from ..states import RefundWizard
from ..keyboards import get_reason_kb, get_back_kb, get_refund_confirm_markup, get_main_kb, get_currency_kb, get_retention_kb
from ..utils import _BACK, tashkent_now
import re
from sqlalchemy.orm import joinedload

router = Router()

@router.message(F.text == "Оформить возврат (в боте)")
async def start_refund_wizard(message: types.Message, state: FSMContext):
    user_branches = []
    user_id = None
    user_team = None
    with database.database_session() as db:
        from app.db import models
        user = db.query(models.User).options(joinedload(models.User.branches)).filter(models.User.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Авторизуйтесь: /start")
            return
        user_id = user.id
        user_team = user.team
        user_branches = [{"id": b.id, "name": b.name} for b in user.branches]

    await state.update_data(user_id=user_id, team=user_team, branches_data=user_branches)
    
    if len(user_branches) != 1:
        from ..keyboards import get_branches_kb
        await message.answer("Выберите филиал:", reply_markup=get_branches_kb(user_branches))
        await state.set_state(RefundWizard.branch_selection)
    else:
        # Exactly one branch - auto-select
        await state.update_data(branch=user_branches[0]["name"], branch_id=user_branches[0]["id"])
        await message.answer("Шаг 1/4 — ID ученика:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RefundWizard.student_id)

@router.message(RefundWizard.branch_selection)
async def process_refund_branch_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    branches = data.get("branches_data", [])
    selected = next((b for b in branches if b["name"] == message.text), None)
    if selected:
        await state.update_data(branch=selected["name"], branch_id=selected["id"])
        await message.answer("Шаг 1/4 — ID ученика:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RefundWizard.student_id)
    elif message.text == "Нет филиала":
        await state.update_data(branch=None, branch_id=None)
        await message.answer("Продолжаем без филиала.\nШаг 1/4 — ID ученика:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RefundWizard.student_id)
    else:
        from ..keyboards import get_branches_kb
        await message.answer("Выберите филиал из списка кнопок.", reply_markup=get_branches_kb(branches))

@router.message(RefundWizard.student_id)
async def process_refund_student_id(message: types.Message, state: FSMContext):
    await state.update_data(student_id=message.text)
    await message.answer("Шаг 2/4 — Причина возврата:", reply_markup=get_reason_kb())
    await state.set_state(RefundWizard.reason)

@router.message(RefundWizard.reason)
async def process_refund_reason(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 1/4 — ID ученика:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RefundWizard.student_id)
        return
    await state.update_data(reason=message.text)
    if message.text == "Другое":
        await message.answer("Укажите причину подробнее:", reply_markup=get_back_kb())
        await state.set_state(RefundWizard.reason_other)
    else:
        await message.answer("Шаг 3/4 — Сумма:", reply_markup=get_back_kb())
        await state.set_state(RefundWizard.amount)

@router.message(RefundWizard.reason_other)
async def process_refund_reason_other(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 2/4 — Причина возврата:", reply_markup=get_reason_kb())
        await state.set_state(RefundWizard.reason)
        return
    await state.update_data(reason_other=message.text)
    await message.answer("Шаг 3/4 — Сумма:", reply_markup=get_back_kb())
    await state.set_state(RefundWizard.amount)

@router.message(RefundWizard.amount)
async def process_refund_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        if data.get("reason") == "Другое":
            await message.answer("Укажите причину подробнее:", reply_markup=get_back_kb())
            await state.set_state(RefundWizard.reason_other)
        else:
            await message.answer("Шаг 2/4 — Причина:", reply_markup=get_reason_kb())
            await state.set_state(RefundWizard.reason)
        return
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
        await state.update_data(amount=amount)
        await message.answer("Шаг 4/4 — Номер карты (16 цифр):", reply_markup=get_back_kb())
        await state.set_state(RefundWizard.card_number)
    except ValueError:
        await message.answer("Введите число.")

@router.message(RefundWizard.card_number)
async def process_refund_card(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 3/4 — Сумма:", reply_markup=get_back_kb())
        await state.set_state(RefundWizard.amount)
        return
    digits = re.sub(r"\D", "", message.text)
    if len(digits) != 16:
        await message.answer(f"Нужно 16 цифр (введено {len(digits)}).")
        return
    await state.update_data(card_number=digits)
    data = await state.get_data()
    reason_display = data['reason']
    if data['reason'] == 'Другое' and data.get('reason_other'):
        reason_display = f"Другое: {data['reason_other']}"
    await message.answer(
        f"Есть ли удержание при возврате?\n\n"
        f"👤 ID: {data['student_id']}\n"
        f"📝 Причина: {reason_display}\n"
        f"💰 Сумма: {data['amount']:,.0f} UZS\n"
        f"💳 Карта: {digits}",
        reply_markup=get_retention_kb()
    )
    await state.set_state(RefundWizard.retention)

@router.message(RefundWizard.retention)
async def process_refund_retention(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 4/4 — Номер карты (16 цифр):", reply_markup=get_back_kb())
        await state.set_state(RefundWizard.card_number)
        return
    is_yes = message.text in ("Да", "ДА", "Есть", "yes", "+")
    await state.update_data(retention=is_yes)
    data = await state.get_data()
    reason_display = data['reason']
    if data['reason'] == 'Другое' and data.get('reason_other'):
        reason_display = f"Другое: {data['reason_other']}"
    text = (
        "✅ Проверьте данные:\n"
        f"👤 ID: {data['student_id']}\n"
        f"📝 Причина: {reason_display}\n"
        f"💰 Сумма: {data['amount']:,.0f} UZS\n"
        f"💳 Карта: {data['card_number']}\n"
        f"🔁 Удержание: {'ДА ✅' if is_yes else 'НЕТ ❌'}\n"
    )
    await message.answer(text, reply_markup=get_refund_confirm_markup(""))
    await state.set_state(RefundWizard.confirm)

@router.callback_query(RefundWizard.confirm, F.data == "refund_submit")
async def handle_refund_submit(callback: types.CallbackQuery, state: FSMContext):
    from app.services.refund.service import create_refund
    from ..notifications import send_admin_notification, get_admin_chat_id
    data = await state.get_data()
    
    user_id = data.get("user_id")
    if not user_id:
        await callback.message.answer(
            "❌ Сессия устарела. Пожалуйста, начните заново: /start",
            reply_markup=get_main_kb()
        )
        await state.clear()
        await callback.answer()
        return

    # Placeholder variables for attributes fetched inside the session
    request_id = None
    expense_id = None

    try:
        with database.database_session() as db:
            reason = data["reason"]
            if reason == "Другое" and data.get("reason_other"):
                reason = f"Другое: {data['reason_other']}"
            expense_req = await create_refund(
                db,
                student_id=data["student_id"],
                reason=reason,
                amount=data["amount"],
                card_number=data["card_number"],
                retention=data.get("retention", False),
                user_id=data["user_id"],
                branch=data.get("branch"),
                team=data.get("team"),
            )
            # Store necessary attributes before session closes
            expense_id = expense_req.id
            request_id = expense_req.request_id
            expense_dict = expense_service.get_expense_dict(expense_req)

        # Notify Safina
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            await send_admin_notification(expense_dict, admin_chat_id)

        await callback.message.answer(
            f"✅ Заявка {request_id} отправлена Сафине!",
            reply_markup=get_main_kb()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Refund submit error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}", reply_markup=get_main_kb())

    await state.clear()
    await callback.answer()

@router.message(F.text == "Создать возврат (Web-App)")
async def open_refund_webapp(message: types.Message):
    base_url = os.getenv("WEB_APP_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}&type=refund"
    builder = ReplyKeyboardBuilder()
    builder.button(
        text="💸 Открыть форму возврата",
        web_app=WebAppInfo(url=url)
    )
    builder.button(text="◀️ Назад")
    builder.adjust(1)
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть форму возврата:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
