import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.core import auth, database
from app.db import models
from ..notifications import set_admin_chat_id
from ..states import ExpenseWizard
from ..keyboards import get_main_kb, get_projects_kb, get_date_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == tg_id).first()
        if user:
            await state.update_data(user_id=user.id)
            if user.position == "ceo":
                await message.answer(
                    f"👋 С возвращением, {user.first_name} (CEO)!\n"
                    "Вы будете получать заявки для финального согласования.",
                    reply_markup=get_main_kb(is_ceo=True)
                )
            elif user.position == "senior_financier":
                await message.answer(
                    f"👋 С возвращением, {user.first_name} (CFO)!\n"
                    "Вы будете получать заявки для согласования.",
                    reply_markup=get_main_kb(is_senior=True)
                )
            else:
                await message.answer(
                    f"С возвращением, {user.first_name}! Как хотите создать заявку?",
                    reply_markup=get_main_kb()
                )
            return

    # Check for admin
    with database.database_session() as db:
        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting and setting.value == str(tg_id):
            await message.answer("С возвращением, Сафина!", reply_markup=types.ReplyKeyboardRemove())
            return

    await message.answer(
        "Добро пожаловать в Thompson Finance Bot!\nПожалуйста, введите ваш логин:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(Command("logout"))
async def cmd_logout(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    with database.database_session() as db:
        db.query(models.TeamMember).filter(
            models.TeamMember.telegram_chat_id == tg_id
        ).update({models.TeamMember.telegram_chat_id: None})

        setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
        if setting and setting.value == str(tg_id):
            db.delete(setting)
        db.commit()

    await state.clear()
    await message.answer(
        "✅ Вы вышли из аккаунта. Используйте /start для нового входа.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(ExpenseWizard.waiting_for_auth)
async def process_login(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "login" not in data:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
        return

    login = data["login"]
    password = message.text
    try:
        await message.delete()
    except Exception:
        pass
    tg_id = message.from_user.id

    # Admin auth
    if login == os.getenv("ADMIN_LOGIN", "safina") and password == os.getenv("ADMIN_PASSWORD", "admin123"):
        set_admin_chat_id(tg_id)
        await message.answer("✅ Вход выполнен (Админ Сафина)!", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()
        if not (user and auth.verify_password(password, user.password_hash)):
            await message.answer("❌ Неверный логин или пароль. Попробуйте снова:")
            await state.clear()
            await state.set_state(ExpenseWizard.waiting_for_auth)
            return

        if user.status != "active":
            await message.answer("❌ Аккаунт заблокирован.")
            await state.clear()
            return

        user.telegram_chat_id = tg_id
        db.commit()
        await state.update_data(user_id=user.id)

        if user.position == "ceo":
            await message.answer(f"✅ Успешно, {user.first_name} (CEO)!", reply_markup=get_main_kb(is_ceo=True))
        elif user.position == "senior_financier":
            await message.answer(f"✅ Успешно, {user.first_name} (CFO)!", reply_markup=get_main_kb(is_senior=True))
        else:
            await message.answer(f"✅ Успешно, {user.first_name}!", reply_markup=get_main_kb())
        
        await state.clear()
