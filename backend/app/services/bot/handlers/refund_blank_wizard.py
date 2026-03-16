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

@router.message(F.text == "🧾 Заявление на возврат")
async def start_refund_blank_wizard(message: types.Message, state: FSMContext):
    await state.set_state(RefundBlankWizard.filling_method)
    await message.answer("Как хотите заполнить заявление?", reply_markup=get_fill_method_kb())

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
    kb.button(text="📥 Скачать заявление")
    kb.button(text=_BACK)
    kb.adjust(1)
    await message.answer(summary, parse_mode="Markdown", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(F.text == "📥 Скачать заявление", RefundBlankWizard.confirm)
async def download_refund_blank(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Internal logic to generate DOCX
    from app.services.docx.generator import generate_docx
    from app.core import database
    from app.db import models
    
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Пользователь не найден")
            return
            
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docx", "templates")
        template_path = os.path.join(templates_dir, "Заявление_на_возврат_денег.docx")
        
        payload = {
            "template": "refund",
            "sender_name": f"{user.last_name} {user.first_name}",
            "sender_position": user.position or "Сотрудник",
            "date": datetime.datetime.now().strftime("%d.%m.%Y"),
            **data
        }
        
        # Checkboxes for refund reason
        reasons = {
            "Переезд": "reason_pereezd",
            "Изменение графика": "reason_grafik",
            "Несоответствие": "reason_ozhidaniy",
            "Материальные трудности": "reason_trudnosti",
            "По личным причинам": "reason_lichnye",
            "Другое": "reason_drugoe"
        }
        for res_text, res_key in reasons.items():
            payload[res_key] = "☑" if data["reason"] == res_text else "□"
        
        if data["reason"] == "Другое":
            payload["reason_drugoe_text"] = data["reason_other"]
        else:
            payload["reason_drugoe_text"] = ""

        try:
            stream = generate_docx(template_path, payload)
            fname = f"refund_{data['client_name']}_{datetime.datetime.now().strftime('%d%m%Y')}.docx"
            input_file = types.BufferedInputFile(stream.getvalue(), filename=fname)
            await message.answer_document(input_file)
            await state.clear()
            await message.answer("Заявление готово!", reply_markup=get_main_kb())
        except Exception as e:
            await message.answer(f"Ошибка генерации: {e}")
