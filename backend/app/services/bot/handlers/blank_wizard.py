from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database, auth
from app.db import models, schemas, crud
from ..states import BlankWizard, RefundBlankWizard
from ..keyboards import (
    get_main_kb, get_fill_method_kb, get_currency_kb, 
    get_confirm_kb, get_back_kb, get_projects_kb, get_template_select_kb
)
from ..utils import _BACK
from ..notifications import send_admin_notification, get_admin_chat_id
from ...currency.service import currency_service
import os
import datetime
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

router = Router()

# Позиция 0. Вход в мастер бланков
@router.message(F.text == "📋 Заполнить бланк")
async def start_blank_wizard(message: types.Message, state: FSMContext):
    await state.clear()
    
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Ошибка: вы не зарегистрированы в системе.")
            return

        # Extract data while session is open
        user_templates = list(user.templates or [])
        projects_data = []
        for p in user.projects:
            projects_data.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "templates": list(p.templates or [])
            })
        
        if not projects_data and not user_templates:
            await message.answer("У вас нет назначенных проектов и личных шаблонов. Обратитесь к Сафине.")
            return

        # 2. Логика по количеству проектов
        if len(projects_data) > 1:
            await state.set_state(BlankWizard.project_selection)
            # Create a simplified project list for the keyboard
            await message.answer("Для какого проекта бланк?", reply_markup=get_projects_kb(projects_data))
        else:
            # 1 проект или вообще нет проектов (но есть личные шаблоны)
            project_id = projects_data[0]["id"] if projects_data else None
            await proceed_to_templates(message, state, user_templates, projects_data, project_id)

# Позиция 1. Выбор проекта (если 2+)
@router.message(BlankWizard.project_selection)
async def handle_project_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Пользователь не найден.")
            return

        # Extract data while session is open
        user_templates = list(user.templates or [])
        projects_data = []
        project_id = None
        for p in user.projects:
            p_data = {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "templates": list(p.templates or [])
            }
            projects_data.append(p_data)
            if f"{p.name} ({p.code})" == message.text:
                project_id = p.id
        
        if not project_id:
            await message.answer("Выберите проект из списка кнопок.")
            return

        await proceed_to_templates(message, state, user_templates, projects_data, project_id)

async def proceed_to_templates(message: types.Message, state: FSMContext, user_templates: list, projects_data: list, project_id: Optional[str]):
    # Собираем доступные шаблоны: личные + этого проекта
    template_keys = set(user_templates)
    
    if project_id:
        # Find project in our pre-loaded data
        project = next((p for p in projects_data if p["id"] == project_id), None)
        if project and project.get("templates"):
            template_keys.update(project["templates"])
    
    if not template_keys:
        await message.answer("Для этого проекта не назначены шаблоны. Обратитесь к Сафине.")
        return

    await state.update_data(project_id=project_id, available_templates=list(template_keys))
    
    if len(template_keys) > 1:
        await state.set_state(BlankWizard.template_selection)
        await message.answer("Выберите тип бланка:", reply_markup=get_template_select_kb(list(template_keys)))
    else:
        # 1 шаблон — переходим сразу
        template = list(template_keys)[0]
        await proceed_to_filling_method(message, state, template)

# Позиция 2. Выбор шаблона (если 2+)
@router.message(BlankWizard.template_selection)
async def handle_template_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        projects_data = []
        with next(database.get_db()) as db:
            user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
            if user:
                for p in user.projects:
                    projects_data.append({
                        "id": p.id,
                        "name": p.name,
                        "code": p.code,
                        "templates": list(p.templates or [])
                    })

        if len(projects_data) > 1:
            await state.set_state(BlankWizard.project_selection)
            await message.answer("Для какого проекта бланк?", reply_markup=get_projects_kb(projects_data))
        else:
            await state.clear()
            await message.answer("Возврат в главное меню.", reply_markup=get_main_kb())
        return

    # Маппинг имен обратно в ключи (упрощенно)
    names_rev = {"LAND": "land", "ЛС (Дружба)": "drujba", "Management": "management", "School": "school", "Заявление на возврат": "refund"}
    template = names_rev.get(message.text)
    
    if not template:
        # Попробуем найти по ключу напрямую
        data = await state.get_data()
        if message.text.lower() in data.get("available_templates", []):
            template = message.text.lower()
        else:
            await message.answer("Выберите бланк из списка кнопок.")
            return

    await proceed_to_filling_method(message, state, template)

async def proceed_to_filling_method(message: types.Message, state: FSMContext, template: str):
    await state.update_data(template=template, items=[])
    await state.set_state(BlankWizard.filling_method)
    await message.answer(f"Выбран бланк: {template.upper()}\nКак хотите заполнить его?", reply_markup=get_fill_method_kb())

@router.message(BlankWizard.filling_method)
async def handle_filling_method(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        if len(data.get("available_templates", [])) > 1:
            await state.set_state(BlankWizard.template_selection)
            await message.answer("Выберите тип бланка:", reply_markup=get_template_select_kb(data["available_templates"]))
        else:
            # Выход в главное меню
            await state.clear()
            await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    if message.text == "🌐 Открыть Web форму":
        data = await state.get_data()
        template = data.get("template")
        # Для WebApp передаем project_id и template
        base_url = os.getenv("WEB_APP_URL", "https://finance.thompson.uz")
        url = f"{base_url}/blank-form?template={template}&project_id={data.get('project_id', '')}"
        
        builder = ReplyKeyboardBuilder()
        builder.button(text="Открыть форму", web_app=types.WebAppInfo(url=url))
        builder.button(text=_BACK)
        builder.adjust(1)
        await message.answer(f"Используйте Web форму для заполнения:", reply_markup=builder.as_markup(resize_keyboard=True))
        return

    if message.text == "📱 Заполнить в боте":
        data = await state.get_data()
        if data.get("template") == "refund":
            await state.set_state(RefundBlankWizard.client_name)
            await message.answer("Заполнение заявления на возврат.\nФИО клиента (родителя):", reply_markup=get_back_kb())
        else:
            await state.set_state(BlankWizard.purpose)
            await message.answer("Введите цель расхода (назначение):", reply_markup=get_back_kb())

# --- Стандартный цикл заполнения (как в ExpenseWizard) ---

@router.message(BlankWizard.purpose)
async def handle_purpose(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.filling_method)
        await message.answer("Как хотите заполнить бланк?", reply_markup=get_fill_method_kb())
        return
    
    await state.update_data(purpose=message.text)
    await state.set_state(BlankWizard.item_name)
    await message.answer("Наименование позиции:", reply_markup=get_back_kb())

@router.message(BlankWizard.item_name)
async def handle_item_name(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.purpose)
        await message.answer("Введите цель расхода:", reply_markup=get_back_kb())
        return
    await state.update_data(curr_name=message.text)
    await state.set_state(BlankWizard.item_qty)
    await message.answer("Количество:", reply_markup=get_back_kb())

@router.message(BlankWizard.item_qty)
async def handle_item_qty(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_name)
        await message.answer("Наименование позиции:", reply_markup=get_back_kb())
        return
    try:
        val = float(message.text.replace(",", "."))
        await state.update_data(curr_qty=val)
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за единицу:", reply_markup=get_back_kb())
    except:
        await message.answer("Введите число.")

@router.message(BlankWizard.item_amount)
async def handle_item_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_qty)
        await message.answer("Количество:", reply_markup=get_back_kb())
        return
    try:
        val = float(message.text.replace(",", "."))
        await state.update_data(curr_amount=val)
        await state.set_state(BlankWizard.item_currency)
        await message.answer("Валюта:", reply_markup=get_currency_kb())
    except:
        await message.answer("Введите число.")

@router.message(BlankWizard.item_currency)
async def handle_item_currency(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за единицу:", reply_markup=get_back_kb())
        return
    
    data = await state.get_data()
    item = {
        "name": data["curr_name"],
        "quantity": data["curr_qty"],
        "amount": data["curr_amount"],
        "currency": message.text
    }
    items = data.get("items", [])
    items.append(item)
    await state.update_data(items=items)
    
    await state.set_state(BlankWizard.confirm)
    await message.answer(f"Позиция добавлена. Всего: {len(items)}", reply_markup=get_confirm_kb())

@router.message(BlankWizard.confirm)
async def handle_confirm(message: types.Message, state: FSMContext):
    if message.text == "Добавить ещё позицию":
        await state.set_state(BlankWizard.item_name)
        await message.answer("Наименование позиции:", reply_markup=get_back_kb())
    elif message.text == "Готово":
        await show_summary(message, state)
    elif message.text == _BACK:
        # Логика отмены последней позиции
        data = await state.get_data()
        items = data.get("items", [])
        if items: items.pop()
        await state.update_data(items=items)
        await state.set_state(BlankWizard.item_name)
        await message.answer("Наименование позиции:", reply_markup=get_back_kb())

async def show_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    items = data["items"]
    total = sum(i["quantity"] * i["amount"] for i in items)
    currency = items[0]["currency"] if items else "UZS"
    
    await state.update_data(total_amount=total, currency=currency)
    
    summary = f"📋 *ПРЕВЬЮ БЛАНКА*\n\n"
    summary += f"Тип: {data['template'].upper()}\n"
    summary += f"Проект: {data.get('project_id') or 'Не указан'}\n"
    summary += f"Цель: {data['purpose']}\n\n"
    summary += "Позиции:\n"
    for idx, i in enumerate(items):
        summary += f"{idx+1}. {i['name']} - {i['quantity']} x {i['amount']} {i['currency']}\n"
    summary += f"\n*ИТОГО: {total} {currency}*"
    
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ Отправить Сафине")
    kb.button(text=_BACK)
    kb.adjust(1)
    
    await message.answer(summary, parse_mode="Markdown", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(F.text == "✅ Отправить Сафине", BlankWizard.confirm)
async def handle_final_submit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    usd_rate = await currency_service.get_usd_rate()
    expense_req_id = None
    request_id = None
    
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Ошибка: пользователь не найден.")
            return

        # 1. Создаем ExpenseRequest в базе
        items_objs = [schemas.ExpenseItemSchema(**i) for i in data["items"]]
        
        expense_create = schemas.ExpenseRequestCreate(
            project_id=data.get("project_id"),
            purpose=data["purpose"],
            items=items_objs,
            currency=data["currency"],
            request_type="blank_refund" if data["template"] == "refund" else "blank",
            template_key=data["template"]
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
        f"✅ Заявка {request_id} отправлена Сафине.\n\n"
        f"Когда бланк будет утвержден, вы получите уведомление.",
        reply_markup=get_main_kb()
    )
