from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from app.db import models
from ..states import RefundBlankWizard
from ..keyboards import (
    get_main_kb, get_fill_method_kb, get_back_kb, 
    get_skip_back_kb, get_refund_reasons_kb
)
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
        base_url = os.getenv("WEB_APP_URL", "https://finance.thompson.uz")
        url = f"{base_url}/blank?template=refund&chat_id={message.from_user.id}"
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
    await message.answer("Причина возврата:", reply_markup=get_refund_reasons_kb())

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
        await message.answer("Сумма прописью:", reply_markup=get_skip_back_kb())
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
    value = "" if message.text in ("⏭ Пропустить", "Пропустить") else message.text
    await state.update_data(transit_account=value)
    await state.set_state(RefundBlankWizard.bank_iin)
    await message.answer("ИИН банка:", reply_markup=get_skip_back_kb())

@router.message(RefundBlankWizard.bank_iin)
async def handle_bank_iin(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.transit_account)
        await message.answer("Транзитный счет банка (если есть):", reply_markup=get_skip_back_kb())
        return
    
    value = "" if message.text in ("⏭ Пропустить", "Пропустить") else message.text
    await state.update_data(bank_iin=value)
    await state.set_state(RefundBlankWizard.bank_mfo)
    await message.answer("МФО банка:", reply_markup=get_skip_back_kb())

@router.message(RefundBlankWizard.bank_mfo)
async def handle_bank_mfo(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.bank_iin)
        await message.answer("ИИН банка:", reply_markup=get_skip_back_kb())
        return
    
    value = "" if message.text in ("⏭ Пропустить", "Пропустить") else message.text
    await state.update_data(bank_mfo=value)
    await state.set_state(RefundBlankWizard.bank_name)
    await message.answer("Название банка и филиал:", reply_markup=get_back_kb())

@router.message(RefundBlankWizard.bank_name)
async def handle_bank(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(RefundBlankWizard.bank_mfo)
        await message.answer("МФО банка:", reply_markup=get_skip_back_kb())
        return
    await state.update_data(bank_name=message.text)
    await show_refund_summary(message, state)

async def show_refund_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    summary = (
        "🧾 *Заявление на возврат — проверьте данные:*\n\n"
        f"👤 Клиент: {data.get('client_name', '—')}\n"
        f"📄 Паспорт: {data.get('passport_series', '')} {data.get('passport_number', '')}\n"
        f"   Выдан: {data.get('passport_issued_by', '—')}, {data.get('passport_date', '—')}\n"
        f"📞 Тел: {data.get('phone', '—')}\n"
        f"📋 Договор: № {data.get('contract_number', '—')} от {data.get('contract_date', '—')}\n"
        f"📝 Причина: {data.get('reason', '—')}"
    )
    if data.get('reason') == 'Другое':
        summary += f" ({data.get('reason_other', '')})"
    
    summary += (
        f"\n💰 Сумма: {data.get('amount', 0):,} UZS\n"
        f"   Прописью: {data.get('amount_words', '—')}\n"
        f"💳 Карта: {data.get('card_number', '—')}\n"
        f"   Владелец: {data.get('card_holder', '—')}\n"
        f"🏦 Банк: {data.get('bank_name', '—')}\n"
    )
    if data.get('transit_account'):
        summary += f"   Транзит: {data.get('transit_account')}\n"
    if data.get('bank_iin'):
        summary += f"   ИИН: {data.get('bank_iin')}\n"
    if data.get('bank_mfo'):
        summary += f"   МФО: {data.get('bank_mfo')}\n"
    
    await state.set_state(RefundBlankWizard.confirm)
    
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
    usd_rate = await currency_service.get_usd_rate()
    expense_req_id = None
    request_id = None

    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Ошибка: пользователь не найден.")
            return

        expense_create = schemas.ExpenseRequestCreate(
            project_id=data.get("project_id"),
            purpose=f"Возврат: {data['client_name']}",
            items=[],
            currency="UZS",
            request_type="blank_refund",
            template_key="refund",
            refund_data=schemas.RefundDataSchema(
                client_name=data.get("client_name"),
                passport_series=data.get("passport_series"),
                passport_number=data.get("passport_number"),
                passport_issued_by=data.get("passport_issued_by"),
                passport_date=data.get("passport_date"),
                phone=data.get("phone"),
                contract_number=data.get("contract_number"),
                contract_date=data.get("contract_date"),
                reason=data.get("reason"),
                reason_other=data.get("reason_other"),
                amount=float(data.get("amount", 0)),
                amount_words=data.get("amount_words", ""),
                card_holder=data.get("card_holder"),
                card_number=data.get("card_number"),
                transit_account=data.get("transit_account", ""),
                bank_iin=data.get("bank_iin", ""),
                bank_mfo=data.get("bank_mfo", ""),
                bank_name=data.get("bank_name"),
            )
        )


        expense_req = crud.create_expense_request(db=db, expense=expense_create, user_id=user.id, usd_rate=usd_rate)
        expense_req_id = expense_req.id
        request_id = expense_req.request_id

    # 2. Уведомляем админа (вне сессии)
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        await send_admin_notification(expense_req_id, admin_chat_id)

    await state.clear()
    await message.answer(
        f"✅ Заявление на возврат ({request_id}) отправлено Сафине.\n\n"
        f"Когда бланк будет утвержден, вы получите уведомление.",
        reply_markup=get_main_kb()
    )

# Manual download removed from bot flow, handled via Safina export
