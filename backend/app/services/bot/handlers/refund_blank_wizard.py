from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from app.db import models
from ..states import RefundBlankWizard
from ..keyboards import get_main_kb, get_fill_method_kb, get_back_kb
from ..utils import _BACK
import os
import datetime

router = Router()

# Removed manual start, now started from BlankWizard

@router.message(RefundBlankWizard.filling_method)
async def handle_filling_method(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    if message.text == "🌐 Открыть Web форму":
        base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
        url = f"{base_url}/blank?type=refund&chat_id={message.from_user.id}"
        builder = ReplyKeyboardBuilder()
        builder.button(text="Открыть форму", web_app=types.WebAppInfo(url=url))
        builder.button(text=_BACK)
        builder.adjust(1)
        await message.answer("Откройте форму для заполнения заявления на возврат:", reply_markup=builder.as_markup(resize_keyboard=True))
        return

    if message.text == "📱 Заполнить в боте":
        await state.set_state(RefundBlankWizard.client_name)
        await message.answer("ФИО клиента (родителя):", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.client_name)
async def handle_client_name(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.filling_method)
        await message.answer("Как хотите заполнить заявление?", reply_markup=get_fill_method_kb())
        return
    await state.update_data(client_name=message.text)
    await state.set_state(RefundBlankWizard.passport_series)
    await message.answer("Серия паспорта:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.passport_series)
async def handle_passport_series(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.client_name)
        await message.answer("ФИО клиента (родителя):", reply_markup=get_back_kb())
        return
    await state.update_data(passport_series=message.text)
    await state.set_state(RefundBlankWizard.passport_number)
    await message.answer("Номер паспорта:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.passport_number)
async def handle_passport_number(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.passport_series)
        await message.answer("Серия паспорта:", reply_markup=get_back_kb())
        return
    await state.update_data(passport_number=message.text)
    await state.set_state(RefundBlankWizard.passport_issued_by)
    await message.answer("Кем выдан паспорт:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.passport_issued_by)
async def handle_passport_issued_by(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.passport_number)
        await message.answer("Номер паспорта:", reply_markup=get_back_kb())
        return
    await state.update_data(passport_issued_by=message.text)
    await state.set_state(RefundBlankWizard.passport_date)
    await message.answer("Дата выдачи паспорта:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.passport_date)
async def handle_passport_date(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.passport_issued_by)
        await message.answer("Кем выдан паспорт:", reply_markup=get_back_kb())
        return
    await state.update_data(passport_date=message.text)
    await state.set_state(RefundBlankWizard.phone)
    await message.answer("Номер телефона:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.phone)
async def handle_phone(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.passport_date)
        await message.answer("Дата выдачи паспорта:", reply_markup=get_back_kb())
        return
    await state.update_data(phone=message.text)
    await state.set_state(RefundBlankWizard.contract_number)
    await message.answer("Номер оферты/договора:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.contract_number)
async def handle_contract_number(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.phone)
        await message.answer("Номер телефона:", reply_markup=get_back_kb())
        return
    await state.update_data(contract_number=message.text)
    await state.set_state(RefundBlankWizard.contract_date)
    await message.answer("Дата оферты/договора:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.contract_date)
async def handle_contract_date(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.contract_number)
        await message.answer("Номер оферты/договора:", reply_markup=get_back_kb())
        return
    await state.update_data(contract_date=message.text)
    await state.set_state(RefundBlankWizard.reason)
    reasons = ["Переезд", "Изменение графика", "Несоответствие", "Материальные трудности", "По личным причинам", "Другое"]
    kb = ReplyKeyboardBuilder()
    for r in reasons:
        kb.button(text=r)
    kb.button(text=_BACK)
    kb.adjust(2)
    await message.answer("Причина возврата:", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(RefundBlankWizard.reason)
async def handle_reason(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.contract_date)
        await message.answer("Дата оферты/договора:", reply_markup=get_back_kb())
        return
    await state.update_data(reason=message.text)
    if message.text == "Другое":
        await state.set_state(RefundBlankWizard.reason_other)
        await message.answer("Укажите причину:", reply_markup=get_back_kb())
    else:
        await state.update_data(reason_other="")
        await state.set_state(RefundBlankWizard.amount)
        await message.answer("Сумма возврата (числом):", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.reason_other)
async def handle_reason_other(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.reason)
        reasons = ["Переезд", "Изменение графика", "Несоответствие", "Материальные трудности", "По личным причинам", "Другое"]
        kb = ReplyKeyboardBuilder()
        for r in reasons:
            kb.button(text=r)
        kb.button(text=_BACK)
        kb.adjust(2)
        await message.answer("Причина возврата:", reply_markup=kb.as_markup(resize_keyboard=True))
        return
    await state.update_data(reason_other=message.text)
    await state.set_state(RefundBlankWizard.amount)
    await message.answer("Сумма возврата (числом):", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.amount)
async def handle_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        if data.get("reason") == "Другое":
            await state.set_state(RefundBlankWizard.reason_other)
            await message.answer("Укажите причину:", reply_markup=get_back_kb())
        else:
            await state.set_state(RefundBlankWizard.reason)
            reasons = ["Переезд", "Изменение графика", "Несоответствие", "Материальные трудности", "По личным причинам", "Другое"]
            kb = ReplyKeyboardBuilder()
            for r in reasons:
                kb.button(text=r)
            kb.button(text=_BACK)
            kb.adjust(2)
            await message.answer("Причина возврата:", reply_markup=kb.as_markup(resize_keyboard=True))
        return
    try:
        val = float(message.text.replace(",", "."))
        await state.update_data(amount=val)
        await state.set_state(RefundBlankWizard.amount_words)
        await message.answer("Сумма прописью:", reply_markup=get_back_kb())
    except ValueError:
        await message.answer("Введите число.")

@router.message(RefundBlankWizard.amount_words)
async def handle_amount_words(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.amount)
        await message.answer("Сумма возврата (числом):", reply_markup=get_back_kb())
        return
    await state.update_data(amount_words=message.text)
    await state.set_state(RefundBlankWizard.card_holder)
    await message.answer("ФИО владельца карты:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.card_holder)
async def handle_card_holder(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.amount_words)
        await message.answer("Сумма прописью:", reply_markup=get_back_kb())
        return
    await state.update_data(card_holder=message.text)
    await state.set_state(RefundBlankWizard.card_number)
    await message.answer("Номер карты:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.card_number)
async def handle_card_number(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.card_holder)
        await message.answer("ФИО владельца карты:", reply_markup=get_back_kb())
        return
    await state.update_data(card_number=message.text)
    await state.set_state(RefundBlankWizard.transit_account)
    await message.answer("Транзитный счет банка (если есть):", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.transit_account)
async def handle_transit(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.card_number)
        await message.answer("Номер карты:", reply_markup=get_back_kb())
        return
    await state.update_data(transit_account=message.text)
    await state.set_state(RefundBlankWizard.bank_name)
    await message.answer("Название банка и филиал:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.bank_name)
async def handle_bank(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.transit_account)
        await message.answer("Транзитный счет банка (если есть):", reply_markup=get_back_kb())
        return
    await state.update_data(bank_name=message.text)
    await state.set_state(RefundBlankWizard.confirm)
    
    data = await state.get_data()
    summary = (
        "🧾 *Заявление на возврат*\n\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"📞 Тел: {data['phone']}\n"
        f"📝 Причина: {data['reason']}\n"
        f"💰 Сумма: {data['amount']:,} UZS\n"
        f"💳 Карта: {data['card_number']}\n"
    )
    
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ Отправить Сафине")
    kb.button(text=_BACK)
    kb.adjust(1)
    await message.answer(summary, parse_mode="Markdown", reply_markup=kb.as_markup(resize_keyboard=True))

from app.core import database, auth
from app.db import models, schemas, crud
from ..notifications import send_admin_notification, get_admin_chat_id
from ...currency.service import currency_service

@router.message(F.text == "✅ Отправить Сафине", RefundBlankWizard.confirm)
async def handle_refund_final_submit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        
        # 1. Создаем ExpenseRequest в базе
        # Для возврата сохраняем все доп. поля в поле refund_data (JSON)
        # Но в ExpenseRequest мы можем сохранить как общие поля
        
        expense_create = schemas.ExpenseRequestCreate(
            project_id=data.get("project_id"),
            purpose=f"Возврат: {data['client_name']}",
            items=[], # Пусто для возврата, используем refund_data
            currency="UZS",
            request_type="blank_refund",
            template_key="refund",
            refund_data=data # Сохраняем все собранные данные (client_name, passport, и т.д.)
        )
        
        usd_rate = await currency_service.get_usd_rate()
        expense_req = crud.create_expense_request(db=db, expense=expense_create, user_id=user.id, usd_rate=usd_rate)
        
        # 2. Уведомляем админа
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            await send_admin_notification(expense_req.id, admin_chat_id)
            
        await state.clear()
        await message.answer(
            f"✅ Заявление на возврат ({expense_req.request_id}) отправлено Сафине.\n\n"
            f"Когда бланк будет утвержден, вы получите уведомление.",
            reply_markup=get_main_kb()
        )

# Manual download removed from bot flow, handled via Safina export
