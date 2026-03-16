from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from app.db import models, schemas
from ..states import BlankWizard
from ..keyboards import get_main_kb, get_fill_method_kb, get_currency_kb, get_confirm_kb, get_back_kb
from ..utils import _BACK, get_user_templates
import httpx
import os
import datetime

router = Router()

BLANK_TYPES = {
    "📋 Заполнить бланк LAND": "land",
    "📋 Заполнить бланк ЛС": "drujba",
    "📋 Заполнить бланк Management": "management",
    "📋 Заполнить бланк School": "school"
}

@router.message(F.text.in_(BLANK_TYPES.keys()))
async def start_blank_wizard(message: types.Message, state: FSMContext):
    template = BLANK_TYPES[message.text]
    await state.update_data(template=template, items=[])
    await state.set_state(BlankWizard.filling_method)
    await message.answer("Как хотите заполнить бланк?", reply_markup=get_fill_method_kb())

@router.message(BlankWizard.filling_method)
async def handle_filling_method(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        with next(database.get_db()) as db:
            user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
            templates = get_user_templates(user) if user else None
            await message.answer("Главное меню", reply_markup=get_main_kb(templates=templates))
        return

    if message.text == "🌐 Открыть Web форму":
        data = await state.get_data()
        template = data.get("template")
        base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
        url = f"{base_url}/blank?type={template}&chat_id={message.from_user.id}"
        builder = ReplyKeyboardBuilder()
        builder.button(text="Открыть форму", web_app=types.WebAppInfo(url=url))
        builder.button(text=_BACK)
        builder.adjust(1)
        await message.answer(f"Откройте форму для заполнения бланка {template.upper()}:", reply_markup=builder.as_markup(resize_keyboard=True))
        return

    if message.text == "📱 Заполнить в боте":
        await state.set_state(BlankWizard.purpose)
        await message.answer("Введите цель расхода:", reply_markup=get_back_kb())

@router.message(BlankWizard.purpose)
async def handle_purpose(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.filling_method)
        await message.answer("Как хотите заполнить бланк?", reply_markup=get_fill_method_kb())
        return
    
    await state.update_data(purpose=message.text)
    await state.set_state(BlankWizard.item_name)
    data = await state.get_data()
    item_num = len(data.get("items", [])) + 1
    await message.answer(f"Позиция {item_num}. Наименование:", reply_markup=get_back_kb())

@router.message(BlankWizard.item_name)
async def handle_item_name(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.purpose)
        await message.answer("Введите цель расхода:", reply_markup=get_back_kb())
        return
    
    await state.update_data(current_item_name=message.text)
    await state.set_state(BlankWizard.item_qty)
    await message.answer("Количество:", reply_markup=get_back_kb())

@router.message(BlankWizard.item_qty)
async def handle_item_qty(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_name)
        data = await state.get_data()
        item_num = len(data.get("items", [])) + 1
        await message.answer(f"Позиция {item_num}. Наименование:", reply_markup=get_back_kb())
        return

    try:
        qty = float(message.text.replace(",", "."))
        await state.update_data(current_item_qty=qty)
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за 1 ед.:", reply_markup=get_back_kb())
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(BlankWizard.item_amount)
async def handle_item_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_qty)
        await message.answer("Количество:", reply_markup=get_back_kb())
        return

    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(current_item_amount=amount)
        await state.set_state(BlankWizard.item_currency)
        await message.answer("Валюта:", reply_markup=get_currency_kb())
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(BlankWizard.item_currency)
async def handle_item_currency(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за 1 ед.:", reply_markup=get_back_kb())
        return

    if message.text not in ["UZS", "USD"]:
        await message.answer("Выберите валюту из кнопок.")
        return

    data = await state.get_data()
    item = {
        "name": data["current_item_name"],
        "qty": data["current_item_qty"],
        "amount": data["current_item_amount"],
        "currency": message.text
    }
    items = data.get("items", [])
    items.append(item)
    await state.update_data(items=items)
    
    if len(items) >= 5:
        await finish_items(message, state)
    else:
        await state.set_state(BlankWizard.confirm)
        await message.answer("Позиция сохранена. Добавить ещё или завершить?", reply_markup=get_confirm_kb())

@router.message(BlankWizard.confirm)
async def handle_confirm_items(message: types.Message, state: FSMContext):
    if message.text == "Добавить ещё позицию":
        await state.set_state(BlankWizard.item_name)
        data = await state.get_data()
        item_num = len(data.get("items", [])) + 1
        await message.answer(f"Позиция {item_num}. Наименование:", reply_markup=get_back_kb())
    elif message.text == "Готово":
        await finish_items(message, state)
    elif message.text == _BACK:
        # Remove last item and go back to currency
        data = await state.get_data()
        items = data.get("items", [])
        if items:
            last_item = items.pop()
            await state.update_data(items=items, current_item_name=last_item["name"], current_item_qty=last_item["qty"], current_item_amount=last_item["amount"])
        await state.set_state(BlankWizard.item_currency)
        await message.answer("Валюта:", reply_markup=get_currency_kb())

async def finish_items(message: types.Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    total = sum(i["qty"] * i["amount"] for i in items)
    currency = items[0]["currency"] if items else "UZS"
    
    summary = (
        f"📋 Бланк: *{data['template'].upper()}*\n"
        f"🎯 Цель: {data['purpose']}\n\n"
        f"📦 Позиции:\n"
    )
    for idx, i in enumerate(items):
        summary += f"  {idx+1}. {i['name']} — {i['qty']} шт. × {i['amount']:,} {i['currency']}\n"
    
    summary += f"\n💰 Итого: *{total:,} {currency}*"
    
    await state.update_data(total_amount=total, currency=currency)
    
    # We use a simple confirm for now, but in reality we'd provide edit buttons
    builder = ReplyKeyboardBuilder()
    builder.button(text="📥 Скачать бланк")
    builder.button(text=_BACK)
    builder.adjust(1)
    
    await message.answer(summary, parse_mode="Markdown", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text == "📥 Скачать бланк", BlankWizard.confirm)
async def download_blank(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Call our new API internally or via HTTP
    # For now, let's use the API logic but directly
    from app.api.blanks import BlankGenerateRequest
    from app.services.docx.generator import generate_docx
    from app.core import database
    from app.db import models
    
    # Get user for prefill
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Пользователь не найден")
            return
            
        template_filename = {
            "land": "LAND.docx",
            "drujba": "Drujba.docx",
            "management": "Management.docx",
            "school": "School.docx"
        }.get(data["template"])
        
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docx", "templates")
        template_path = os.path.join(templates_dir, template_filename)
        
        # Prepare data matches the API schema
        payload = {
            "template": data["template"],
            "sender_name": f"{user.last_name} {user.first_name}",
            "sender_position": user.position or "Сотрудник",
            "purpose": data["purpose"],
            "items": data["items"],
            "total_amount": data["total_amount"],
            "currency": data["currency"],
            "date": datetime.datetime.now().strftime("%d.%m.%Y")
        }
        
        # Add short name
        parts = payload["sender_name"].split()
        if len(parts) >= 2:
            payload["sender_name_short"] = f"{parts[0]} {parts[1][0]}."
        else:
            payload["sender_name_short"] = payload["sender_name"]
            
        try:
            stream = generate_docx(template_path, payload)
            fname = f"blank_{data['template']}_{datetime.datetime.now().strftime('%d%m%Y')}.docx"
            input_file = types.BufferedInputFile(stream.getvalue(), filename=fname)
            await message.answer_document(input_file)
            await state.clear()
            templates = get_user_templates(user)
            await message.answer("Бланк готов!", reply_markup=get_main_kb(templates=templates))
        except Exception as e:
            await message.answer(f"Ошибка генерации: {e}")
