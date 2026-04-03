import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.core import database
from app.db import models, schemas, crud
from app.services.bot.states import ExpenseWizard
from app.services.bot.keyboards import get_confirm_kb, get_date_kb, get_currency_kb, get_projects_kb, get_main_kb, get_back_kb
from app.services.bot.utils import tashkent_now, _BACK
from decimal import Decimal
from app.services.currency.service import currency_service
from app.services.bot.notifications import send_admin_notification, get_admin_chat_id

router = Router()

@router.message(F.text == "Создать инвестицию (в боте)")
async def start_wizard_selection(message: types.Message, state: FSMContext):
    user_not_found = False
    no_projects = False
    projects = []
    user_id = None
    
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            user_not_found = True
        else:
            user_id = user.id
            projects = list(user.projects or [])
            if not projects:
                no_projects = True

    if user_not_found:
        await message.answer("Сначала авторизуйтесь: /start")
        return
    
    if no_projects:
        await message.answer("Проекты не привязаны.")
        return

    if len(projects) > 1:
        await state.update_data(user_id=user_id)
        await message.answer("Выберите проект:", reply_markup=get_projects_kb(projects))
        await state.set_state(ExpenseWizard.project_selection)
    else:
        # Exactly one project
        await state.update_data(project_id=projects[0].id, user_id=user_id)
        await message.answer("Введите дату или «Сейчас»:", reply_markup=get_date_kb())
        await state.set_state(ExpenseWizard.date)

@router.message(ExpenseWizard.project_selection)
async def process_project_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_kb())
        return
        
    with database.database_session() as db:
        projects = db.query(models.Project).all()
        selected = next((p for p in projects if f"{p.name} ({p.code})" == message.text), None)
        if selected:
            await state.update_data(project_id=selected.id)
            await message.answer(f"Проект выбран. Введите дату:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Выберите из списка или отмените.", reply_markup=get_projects_kb(projects))

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        user_id = data.get("user_id")
        with database.database_session() as db:
            user = db.query(models.TeamMember).filter(models.TeamMember.id == user_id).first()
            if user and len(user.projects) > 1:
                await message.answer("Выберите проект:", reply_markup=get_projects_kb(user.projects))
                await state.set_state(ExpenseWizard.project_selection)
            else:
                await state.clear()
                await message.answer("Отменено.", reply_markup=get_main_kb())
        return

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
    await message.answer("Введите назначение расхода:", reply_markup=get_back_kb())
    await state.set_state(ExpenseWizard.purpose)

@router.message(ExpenseWizard.purpose)
async def process_purpose(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Введите дату или «Сейчас»:", reply_markup=get_date_kb())
        await state.set_state(ExpenseWizard.date)
        return
        
    await state.update_data(purpose=message.text, items=[])
    await message.answer("Введите наименование товара:", reply_markup=get_back_kb())
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.item_name)
async def process_item_name(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        items = data.get("items", [])
        if items:
            await message.answer("Добавить еще одну позицию?", reply_markup=get_confirm_kb())
            await state.set_state(ExpenseWizard.confirm)
        else:
            await message.answer("Введите назначение расхода:", reply_markup=get_back_kb())
            await state.set_state(ExpenseWizard.purpose)
        return
        
    await state.update_data(current_item_name=message.text)
    await message.answer("Количество:", reply_markup=get_back_kb())
    await state.set_state(ExpenseWizard.item_qty)

@router.message(ExpenseWizard.item_qty)
async def process_item_qty(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Введите наименование товара:", reply_markup=get_back_kb())
        await state.set_state(ExpenseWizard.item_name)
        return
        
    try:
        qty = Decimal(message.text.replace(",", "."))
        await state.update_data(current_item_qty=str(qty))
        await message.answer("Сумма за 1 ед:", reply_markup=get_back_kb())
        await state.set_state(ExpenseWizard.item_amount)
    except Exception:
        await message.answer("Введите число.")

@router.message(ExpenseWizard.item_amount)
async def process_item_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Количество:", reply_markup=get_back_kb())
        await state.set_state(ExpenseWizard.item_qty)
        return
        
    try:
        amount = Decimal(message.text.replace(",", "."))
        await state.update_data(current_item_amount=str(amount))
        await message.answer("Валюта:", reply_markup=get_currency_kb())
        await state.set_state(ExpenseWizard.item_currency)
    except Exception:
        await message.answer("Введите число.")

@router.message(ExpenseWizard.item_currency)
async def process_item_currency(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Сумма за 1 ед:", reply_markup=get_back_kb())
        await state.set_state(ExpenseWizard.item_amount)
        return
        
    currency = message.text.upper()
    if currency not in ("UZS", "USD"):
        await message.answer("UZS или USD:", reply_markup=get_currency_kb())
        return
    data = await state.get_data()
    items = data.get("items", [])
    if items and items[0].get("currency") != currency:
        await message.answer(f"Ошибка: в одной заявке может быть только одна валюта. Текущая: {items[0]['currency']}")
        return
    
    items.append({
        "name": data.get("current_item_name"),
        "quantity": data.get("current_item_qty"),
        "amount": data.get("current_item_amount"),
        "currency": currency
    })
    MAX_ITEMS = 50
    if len(items) >= MAX_ITEMS:
        await message.answer(
            f"✅ Позиция добавлена. Достигнут максимум ({MAX_ITEMS} позиций).\n"
            "Переходим к подтверждению.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(ExpenseWizard.confirm)
    else:
        await message.answer(
            f"✅ Позиция добавлена ({len(items)}/{MAX_ITEMS}). Добавить еще?",
            reply_markup=get_confirm_kb()
        )
        await state.set_state(ExpenseWizard.confirm)

@router.message(ExpenseWizard.confirm, F.text == "Добавить ещё позицию")
async def process_add_more(message: types.Message, state: FSMContext):
    await message.answer("Наименование товара:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.confirm, F.text == "Готово")
async def process_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    if not items:
        await message.answer("Нет добавленных позиций. Начните заново.")
        await state.clear()
        return

    currency = items[0]["currency"]
    usd_rate = await currency_service.get_usd_rate() if currency == "USD" else None
    
    # Placeholder variables for attributes fetched inside the session
    expense_id = None
    req_id = None

    try:
        with database.database_session() as db:
            total = sum(Decimal(str(i["amount"])) * Decimal(str(i["quantity"])) for i in items)
            expense_create = schemas.ExpenseRequestCreate(
                purpose=data.get("purpose"),
                items=[schemas.ExpenseItemSchema(**i) for i in items],
                total_amount=total,
                currency=currency,
                project_id=data.get("project_id"),
                date=datetime.datetime.fromisoformat(data.get("date")),
            )
            db_expense = crud.create_expense_request(db, expense_create, user_id=data.get("user_id"), usd_rate=usd_rate)
            # Store necessary attributes before session closes
            expense_id = db_expense.id
            req_id = db_expense.request_id
        
        # Notify Safina
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            await send_admin_notification(expense_id, admin_chat_id)
            
        await message.answer(f"✅ Заявка {req_id} создана!", reply_markup=get_main_kb())
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating expense via bot: {e}")
        await message.answer(f"❌ Ошибка: {e}", reply_markup=get_main_kb())
    
    await state.clear()

@router.message(F.text == "Создать инвестицию (Web-App)")
@router.message(Command("form"))
async def open_expense_webapp(message: types.Message):
    base_url = os.getenv("WEB_APP_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}&type=expense"
    builder = ReplyKeyboardBuilder()
    builder.button(
        text="📝 Открыть форму заявки",
        web_app=WebAppInfo(url=url)
    )
    builder.button(text="◀️ Назад")
    builder.adjust(1)
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть форму заявки:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
@router.message(F.text == "◀️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_kb())
