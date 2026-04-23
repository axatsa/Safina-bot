import os
import datetime
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy.orm import joinedload

from app.core import database
from app.db import models, schemas
from app.services.core.expense_service import expense_service
from ..states import ExpenseWizard
from ..keyboards import get_confirm_kb, get_date_kb, get_currency_kb, get_projects_kb, get_main_kb, get_back_kb, get_branches_kb
from ..utils import tashkent_now, _BACK, run_sync
from decimal import Decimal
from app.services.currency.service import currency_service
from ..notifications import send_admin_notification, get_admin_chat_id

router = Router()

@router.message(F.text == "Создать инвестицию (в боте)")
async def start_wizard_selection(message: types.Message, state: FSMContext):
    def get_user_projects_data(chat_id):
        with database.database_session() as db:
            user = db.query(models.User).options(
                joinedload(models.User.projects).joinedload(models.Project.branches),
                joinedload(models.User.branches)
            ).filter(models.User.telegram_chat_id == chat_id).first()
            if not user:
                return None, None
            
            p_data_list = []
            user_id = user.id
            user_branch_ids = {b.id for b in user.branches}
            user_is_privileged = user.role in ["admin", "ceo", "senior_financier"]
            
            for p in user.projects:
                p_branches = p.branches
                if user_branch_ids:
                    filtered_branches = [b for b in p_branches if b.id in user_branch_ids]
                elif user_is_privileged:
                    filtered_branches = list(p_branches)
                else:
                    filtered_branches = []

                p_data_list.append({
                    "id": p.id,
                    "name": p.name,
                    "code": p.code,
                    "category": p.category,
                    "branches_data": [{"id": b.id, "name": b.name} for b in filtered_branches]
                })
            return user_id, p_data_list

    user_id, projects_data = await run_sync(get_user_projects_data, message.from_user.id)
    
    if user_id is None:
        await message.answer("Сначала авторизуйтесь: /start")
        return
    
    if not projects_data:
        await message.answer("Проекты не привязаны.")
        return

    if len(projects_data) > 1:
        await state.update_data(user_id=user_id, projects_data=projects_data)
        await message.answer("Выберите проект:", reply_markup=get_projects_kb(projects_data))
        await state.set_state(ExpenseWizard.project_selection)
    else:
        # Exactly one project
        proj = projects_data[0]
        await state.update_data(project_id=proj["id"], user_id=user_id, projects_data=projects_data)
        
        if proj["category"] == "corporate":
            await message.answer("Выберите филиал:", reply_markup=get_branches_kb(proj["branches_data"]))
            await state.set_state(ExpenseWizard.branch_selection)
            return

        await message.answer("Введите дату или «Сейчас»:", reply_markup=get_date_kb())
        await state.set_state(ExpenseWizard.date)

@router.message(ExpenseWizard.project_selection)
async def process_project_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_kb())
        return
        
    def get_selection_data(chat_id, selected_text):
        with database.database_session() as db:
            user = db.query(models.User).options(
                joinedload(models.User.projects).joinedload(models.Project.branches),
                joinedload(models.User.branches)
            ).filter(models.User.telegram_chat_id == chat_id).first()
            
            if not user:
                return None, None
            
            projects_data = []
            project_obj = None
            user_branch_ids = {b.id for b in user.branches}
            user_is_privileged = user.role in ["admin", "ceo", "senior_financier"]
            
            for p in user.projects:
                p_branches = p.branches
                if user_branch_ids:
                    filtered_branches = [b for b in p_branches if b.id in user_branch_ids]
                elif user_is_privileged:
                    filtered_branches = list(p_branches)
                else:
                    filtered_branches = []

                p_data = {
                    "id": p.id,
                    "name": p.name,
                    "code": p.code,
                    "category": p.category,
                    "branches_data": [{"id": b.id, "name": b.name} for b in filtered_branches]
                }
                projects_data.append(p_data)
                if f"{p.name} ({p.code})" == selected_text:
                    project_obj = p_data
            return projects_data, project_obj

    projects_data, project_obj = await run_sync(get_selection_data, message.from_user.id, message.text)

    if project_obj:
        await state.update_data(project_id=project_obj["id"], projects_data=projects_data)
        
        if project_obj["category"] == "corporate":
            await message.answer("Выберите филиал:", reply_markup=get_branches_kb(project_obj["branches_data"]))
            await state.set_state(ExpenseWizard.branch_selection)
            return

        await message.answer(f"Проект выбран. Введите дату:", reply_markup=get_date_kb())
        await state.set_state(ExpenseWizard.date)
    else:
        await message.answer("Выберите из списка или отмените.", reply_markup=get_projects_kb(projects_data))

@router.message(ExpenseWizard.branch_selection)
async def process_branch_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        user_id = data.get("user_id")
        
        def get_user_projects(uid):
            with database.database_session() as db:
                user = db.query(models.User).get(uid)
                return [p.name for p in user.projects] if user else []

        projects = await run_sync(get_user_projects, user_id)
        if len(projects) > 1:
            # Note: simplified for brevity, ideally we'd pass projects_data again
            data = await state.get_data()
            await message.answer("Выберите проект:", reply_markup=get_projects_kb(data.get("projects_data", [])))
            await state.set_state(ExpenseWizard.project_selection)
        else:
            await state.clear()
            await message.answer("Отменено.", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    projects_data = data.get("projects_data", [])
    project_id = data.get("project_id")
    project_obj = next((p for p in projects_data if p["id"] == project_id), None)
    
    if project_obj:
        branches = project_obj.get("branches_data", [])
        selected = next((b for b in branches if b["name"] == message.text), None)
        if selected:
            await state.update_data(branch_id=selected["id"])
            await message.answer("Филиал выбран. Введите дату:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        elif message.text == "Нет филиала":
            await state.update_data(branch_id=None)
            await message.answer("Продолжаем без филиала. Введите дату:", reply_markup=get_date_kb())
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Выберите из списка или отмените.", reply_markup=get_branches_kb(branches))
    else:
        await message.answer("Ошибка сессии. Начните заново.", reply_markup=get_main_kb())
        await state.clear()

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        user_id = data.get("user_id")
        
        def check_user_projects(uid):
            with database.database_session() as db:
                user = db.query(models.User).filter(models.User.id == uid).first()
                return user and len(user.projects) > 1
        
        has_many = await run_sync(check_user_projects, user_id)
        if has_many:
            await message.answer("Выберите проект:", reply_markup=get_projects_kb(data.get("projects_data", [])))
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
    
    def create_expense_task(data_in, items_in, usd_rate_in):
        with database.database_session() as db:
            total = sum(Decimal(str(i["amount"])) * Decimal(str(i["quantity"])) for i in items_in)
            expense_create = schemas.ExpenseRequestCreate(
                purpose=data_in.get("purpose"),
                items=[schemas.ExpenseItemSchema(**i) for i in items_in],
                total_amount=total,
                currency=data_in.get("items")[0]["currency"],
                project_id=data_in.get("project_id"),
                branch_id=data_in.get("branch_id"),
                date=datetime.datetime.fromisoformat(data_in.get("date")),
            )
            db_expense = expense_service.create_expense_request(db, expense_create, user_id=data_in.get("user_id"), usd_rate=usd_rate_in)
            # Prepare dict while session is open
            expense_dict = expense_service.get_expense_dict(db_expense)
            return db_expense.request_id, expense_dict

    try:
        request_id, expense_dict = await run_sync(create_expense_task, data, items, usd_rate)
        
        # Notify Safina
        admin_chat_id = await run_sync(get_admin_chat_id)
        if admin_chat_id:
            await send_admin_notification(expense_dict, admin_chat_id)
            
        await message.answer(f"✅ Заявка {request_id} создана!", reply_markup=get_main_kb())
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating expense via bot: {e}")
        await message.answer(f"❌ Ошибка при создании заявки. Попробуйте снова.", reply_markup=get_main_kb())
    finally:
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
