import os
import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core import database
from app.db import models, schemas, crud
from ..states import ExpenseWizard
from ..keyboards import get_confirm_kb, get_date_kb, get_currency_kb, get_projects_kb, get_main_kb
from ..utils import tashkent_now

router = Router()

@router.message(F.text == "Создать инвестицию (в боте)")
async def start_wizard_selection(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Сначала авторизуйтесь: /start")
            return
        if len(user.projects) > 1:
            await state.update_data(user_id=user.id)
            await message.answer("Выберите проект:", reply_markup=get_projects_kb(user.projects))
            await state.set_state(ExpenseWizard.project_selection)
        elif len(user.projects) == 1:
            await state.update_data(project_id=user.projects[0].id, user_id=user.id)
            await message.answer("Введите дату или «Сейчас»:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Проекты не привязаны.")

@router.message(ExpenseWizard.project_selection)
async def process_project_selection(message: types.Message, state: FSMContext):
    # Simplified logic from original handlers.py
    with next(database.get_db()) as db:
        projects = db.query(models.Project).all()
        selected = next((p for p in projects if f"{p.name} ({p.code})" == message.text), None)
        if selected:
            await state.update_data(project_id=selected.id)
            await message.answer(f"Проект выбран. Введите дату:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Выберите из списка.")

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    val = message.text.lower()
    if val == "сейчас":
        d = tashkent_now().isoformat()
    else:
        try:
            d = datetime.datetime.strptime(val, "%Y-%m-%d").isoformat()
        except ValueError:
            await message.answer("Формат ГГГГ-ММ-ДД или «Сейчас»:", reply_markup=get_date_kb())
            return
    await state.update_data(date=d)
    await message.answer("Введите назначение расхода:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.purpose)

@router.message(ExpenseWizard.purpose)
async def process_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text, items=[])
    await message.answer("Введите наименование товара:")
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
        await message.answer("Сумма за 1 ед:")
        await state.set_state(ExpenseWizard.item_amount)
    except ValueError:
        await message.answer("Введите число.")

@router.message(ExpenseWizard.item_amount)
async def process_item_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(current_item_amount=amount)
        await message.answer("Валюта:", reply_markup=get_currency_kb())
        await state.set_state(ExpenseWizard.item_currency)
    except ValueError:
        await message.answer("Введите число.")

@router.message(ExpenseWizard.item_currency)
async def process_item_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    if currency not in ("UZS", "USD"):
        await message.answer("UZS или USD:", reply_markup=get_currency_kb())
        return
    data = await state.get_data()
    items = data.get("items", [])
    if items and items[0]["currency"] != currency:
        await message.answer(f"Ошибка валюты. Текущая: {items[0]['currency']}")
        return
    items.append({
        "name": data["current_item_name"],
        "quantity": data["current_item_qty"],
        "amount": data["current_item_amount"],
        "currency": currency
    })
    await state.update_data(items=items)
    await message.answer("Позиция добавлена. Еще?", reply_markup=get_confirm_kb())
    await state.set_state(ExpenseWizard.confirm)

@router.message(ExpenseWizard.confirm, F.text == "Добавить ещё позицию")
async def process_add_more(message: types.Message, state: FSMContext):
    await message.answer("Наименование товара:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.confirm, F.text == "Готово")
async def process_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    with next(database.get_db()) as db:
        try:
            total = sum(i["amount"] * i["quantity"] for i in data["items"])
            currency = data["items"][0]["currency"] if data["items"] else "UZS"
            expense_create = schemas.ExpenseRequestCreate(
                purpose=data["purpose"],
                items=[schemas.ExpenseItemSchema(**i) for i in data["items"]],
                total_amount=total,
                currency=currency,
                project_id=data["project_id"],
                date=datetime.datetime.fromisoformat(data["date"]),
            )
            db_expense = crud.create_expense_request(db, expense_create, user_id=data["user_id"])
            await message.answer(f"✅ Заявка {db_expense.request_id} создана!", reply_markup=get_main_kb())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

@router.message(F.text == "Создать заявку (Web-App)")
@router.message(Command("form"))
async def show_form_link(message: types.Message):
    base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}&type=expense"
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Открыть форму заявки", url=url)
    await message.answer("Откройте форму по кнопке ниже:", reply_markup=builder.as_markup())
