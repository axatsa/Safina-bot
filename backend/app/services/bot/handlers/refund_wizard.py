from aiogram import Router, types, F
import os
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from ..states import RefundWizard
from ..keyboards import get_reason_kb, get_back_kb, get_refund_confirm_markup, get_main_kb, get_currency_kb
from ..utils import _BACK, tashkent_now
import re

router = Router()

@router.message(F.text == "Оформить возврат (в боте)")
async def start_refund_wizard(message: types.Message, state: FSMContext):
    with database.database_session() as db:
        from app.db import models
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Авторизуйтесь: /start")
            return
        await state.update_data(user_id=user.id, branch=user.branch, team=user.team)
    await message.answer("Шаг 1/4 — ID ученика:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RefundWizard.student_id)

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
    await message.answer("Шаг 3/4 — Сумма:", reply_markup=get_back_kb())
    await state.set_state(RefundWizard.amount)

@router.message(RefundWizard.amount)
async def process_refund_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
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
    text = (
        "✅ Проверьте данные:\n"
        f"👤 ID: {data['student_id']}\n"
        f"📝 Причина: {data['reason']}\n"
        f"💰 Сумма: {data['amount']:,.0f} UZS\n"
        f"💳 Карта: {digits}\n"
    )
    await message.answer(text, reply_markup=get_refund_confirm_markup(""))
    await state.set_state(RefundWizard.confirm)

@router.callback_query(RefundWizard.confirm, F.data == "refund_submit")
async def handle_refund_submit(callback: types.CallbackQuery, state: FSMContext):
    from app.services.refund.service import create_refund
    from ..notifications import send_admin_notification, get_admin_chat_id
    data = await state.get_data()
    # Placeholder variables for attributes fetched inside the session
    request_id = None
    expense_id = None

    try:
        with database.database_session() as db:
            expense_req = await create_refund(
                db,
                student_id=data["student_id"],
                reason=data["reason"],
                amount=data["amount"],
                card_number=data["card_number"],
                user_id=data["user_id"],
                branch=data.get("branch"),
                team=data.get("team"),
            )
            # Store necessary attributes before session closes
            expense_id = expense_req.id
            request_id = expense_req.request_id

        # Notify Safina
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            await send_admin_notification(expense_id, admin_chat_id)

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
