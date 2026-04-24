from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.orm import joinedload
from app.core import database
from app.db import models, schemas
from app.services.core.expense_service import expense_service
from ..states import RefundBlankWizard
from ..keyboards import (
    get_main_kb, get_back_kb, 
    get_refund_reasons_kb, get_retention_kb,
    get_projects_kb, get_branches_kb
)
from ..utils import _BACK
import os
import re
from decimal import Decimal

router = Router()

@router.message(F.text == "Заявление на возврат (в боте)")
async def start_direct_refund_bot(message: types.Message, state: FSMContext):
    await state.clear()
    projects_data = []
    user_id = None
    
    with database.database_session() as db:
        user = db.query(models.User).options(
            joinedload(models.User.projects).joinedload(models.Project.branches),
            joinedload(models.User.branches)
        ).filter(
            models.User.telegram_chat_id == message.from_user.id
        ).first()
        
        if not user:
            await message.answer("Ошибка: вы не зарегистрированы в системе.")
            return
            
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

            projects_data.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "category": p.category,
                "branches_data": [{"id": b.id, "name": b.name} for b in filtered_branches]
            })

    await state.update_data(user_id=user_id, projects_data=projects_data)
    
    if not projects_data:
        await message.answer("У вас нет привязанных проектов. Обратитесь к Сафине.")
        return

    if len(projects_data) > 1:
        await state.set_state(RefundBlankWizard.project_selection)
        await message.answer("Для какого проекта возврат?", reply_markup=get_projects_kb(projects_data))
    else:
        proj = projects_data[0]
        await state.update_data(project_id=proj["id"])
        
        if proj["branches_data"]:
            if len(proj["branches_data"]) > 1:
                await message.answer("Выберите филиал:", reply_markup=get_branches_kb(proj["branches_data"]))
                await state.set_state(RefundBlankWizard.branch_selection)
            else:
                br = proj["branches_data"][0]
                await state.update_data(branch_id=br["id"], branch_name=br["name"])
                await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
                await state.set_state(RefundBlankWizard.student_id)
        else:
            await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
            await state.set_state(RefundBlankWizard.student_id)

@router.message(RefundBlankWizard.project_selection)
async def handle_refund_project_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    projects_data = data.get("projects_data", [])
    selected = next((p for p in projects_data if f"{p['name']} ({p['code']})" == message.text or p['name'] == message.text), None)
    
    if selected:
        await state.update_data(project_id=selected["id"])
        if selected["branches_data"]:
            if len(selected["branches_data"]) > 1:
                await message.answer("Выберите филиал:", reply_markup=get_branches_kb(selected["branches_data"]))
                await state.set_state(RefundBlankWizard.branch_selection)
            else:
                br = selected["branches_data"][0]
                await state.update_data(branch_id=br["id"], branch_name=br["name"])
                await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
                await state.set_state(RefundBlankWizard.student_id)
        else:
            await state.update_data(branch_id=None, branch_name=None)
            await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
            await state.set_state(RefundBlankWizard.student_id)
    else:
        await message.answer("Выберите проект из списка кнопок.")

@router.message(RefundBlankWizard.branch_selection)
async def handle_refund_branch_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        data = await state.get_data()
        projects_data = data.get("projects_data", [])
        if len(projects_data) > 1:
            await state.set_state(RefundBlankWizard.project_selection)
            await message.answer("Для какого проекта возврат?", reply_markup=get_projects_kb(projects_data))
        else:
            await state.clear()
            await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    project_id = data.get("project_id")
    projects_data = data.get("projects_data", [])
    project_obj = next((p for p in projects_data if p["id"] == project_id), None)
    
    if project_obj:
        branches = project_obj.get("branches_data", [])
        selected = next((b for b in branches if b["name"] == message.text), None)
        if selected:
            await state.update_data(branch_id=selected["id"], branch_name=selected["name"])
            await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
            await state.set_state(RefundBlankWizard.student_id)
        else:
            await message.answer("Выберите филиал из списка кнопок.", reply_markup=get_branches_kb(branches))
    else:
        await message.answer("Ошибка сессии. Начните заново.", reply_markup=get_main_kb())
        await state.clear()

@router.message(RefundBlankWizard.student_id)
async def handle_student_id(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await start_direct_refund_bot(message, state)
        return
    await state.update_data(student_id=message.text)
    await message.answer("Шаг 2/5 — Причина возврата:", reply_markup=get_refund_reasons_kb())
    await state.set_state(RefundBlankWizard.reason)

@router.message(RefundBlankWizard.reason)
async def handle_reason(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 1/5 — ID ученика:", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.student_id)
        return
    await state.update_data(reason=message.text)
    if message.text == "Другое":
        await message.answer("Укажите причину подробно:", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.reason_other)
    else:
        await message.answer("Шаг 3/5 — Сумма (только число):", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.amount)

@router.message(RefundBlankWizard.reason_other)
async def handle_reason_other(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 2/5 — Причина возврата:", reply_markup=get_refund_reasons_kb())
        await state.set_state(RefundBlankWizard.reason)
        return
    await state.update_data(reason_other=message.text)
    await message.answer("Шаг 3/5 — Сумма (только число):", reply_markup=get_back_kb())
    await state.set_state(RefundBlankWizard.amount)

@router.message(RefundBlankWizard.amount)
async def handle_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 2/5 — Причина возврата:", reply_markup=get_refund_reasons_kb())
        await state.set_state(RefundBlankWizard.reason)
        return
    try:
        val = float(message.text.replace(",", ".").replace(" ", ""))
        await state.update_data(amount=val)
        await message.answer("Шаг 4/5 — Номер карты (16 цифр):", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.card_number)
    except ValueError:
        await message.answer("Введите число.")

@router.message(RefundBlankWizard.card_number)
async def handle_card_number(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 3/5 — Сумма (только число):", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.amount)
        return
    digits = re.sub(r"\D", "", message.text)
    if len(digits) != 16:
        await message.answer(f"Нужно 16 цифр (введено {len(digits)}).")
        return
    await state.update_data(card_number=digits)
    await message.answer("Шаг 5/5 — Есть ли удержание?", reply_markup=get_retention_kb())
    await state.set_state(RefundBlankWizard.retention)

@router.message(RefundBlankWizard.retention)
async def handle_retention(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await message.answer("Шаг 4/5 — Номер карты (16 цифр):", reply_markup=get_back_kb())
        await state.set_state(RefundBlankWizard.card_number)
        return
    is_yes = message.text in ("Да", "Есть", "ДА", "yes", "+")
    await state.update_data(retention=is_yes)
    
    data = await state.get_data()
    reason_display = data['reason']
    if data['reason'] == 'Другое' and data.get('reason_other'):
        reason_display = f"Другое: {data['reason_other']}"
    
    text = (
        "🔍 *Проверьте данные заявления:*\n\n"
        f"👤 ID Ученика: `{data['student_id']}`\n"
        f"📝 Причина: {reason_display}\n"
        f"💰 Сумма: {data['amount']:,.0f} UZS\n"
        f"💳 Карта: `{data['card_number']}`\n"
        f"🔁 Удержание: {'ДА ✅' if is_yes else 'НЕТ ❌'}\n"
    )
    
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Отправить Сафине")
    builder.button(text=_BACK)
    builder.adjust(1)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(RefundBlankWizard.confirm)

@router.message(F.text == "✅ Отправить Сафине", RefundBlankWizard.confirm)
async def handle_refund_final_submit(message: types.Message, state: FSMContext):
    from app.services.refund.service import create_refund
    from ..notifications import send_admin_notification, get_admin_chat_id
    
    data = await state.get_data()
    
    try:
        with database.database_session() as db:
            reason = data["reason"]
            if reason == "Другое" and data.get("reason_other"):
                reason = f"Другое: {data['reason_other']}"
                
            expense_req = await create_refund(
                db,
                student_id=data["student_id"],
                reason=reason,
                amount=Decimal(str(data["amount"])),
                card_number=data["card_number"],
                retention=data.get("retention", False),
                user_id=data["user_id"],
                branch=data.get("branch_name"),
                project_id=data.get("project_id")
            )
            expense_dict = expense_service.get_expense_dict(expense_req)
            req_id = expense_req.request_id

        # Notify
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            await send_admin_notification(expense_dict, admin_chat_id)

        await message.answer(
            f"✅ Заявление {req_id} отправлено Сафине!",
            reply_markup=get_main_kb()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Refund final submit error: {e}")
        await message.answer(f"❌ Ошибка при отправке: {e}", reply_markup=get_main_kb())

    await state.clear()
