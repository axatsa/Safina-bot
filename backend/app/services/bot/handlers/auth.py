import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.core import auth, database
from app.db import models
from ..notifications import set_admin_chat_id
from ..states import ExpenseWizard
from ..keyboards import get_main_kb, get_projects_kb, get_date_kb
from ..utils import run_sync

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    
    def check_user(tid):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.telegram_chat_id == tid).first()
            if user:
                return {"id": user.id, "position": user.position, "name": user.first_name}
            
            setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
            if setting and setting.value == str(tid):
                return "admin"
            return None

    user_info = await run_sync(check_user, tg_id)
    
    if user_info == "admin":
        await message.answer("С возвращением, Сафина!", reply_markup=types.ReplyKeyboardRemove())
        return

    if user_info:
        await state.update_data(user_id=user_info["id"])
        if user_info["position"] == "ceo":
            await message.answer(
                f"👋 С возвращением, {user_info['name']} (CEO)!\n"
                "Вы будете получать заявки для финального согласования.",
                reply_markup=get_main_kb(is_ceo=True)
            )
        elif user_info["position"] == "senior_financier":
            await message.answer(
                f"👋 С возвращением, {user_info['name']} (CFO)!\n"
                "Вы будете получать заявки для согласования.",
                reply_markup=get_main_kb(is_senior=True)
            )
        else:
            await message.answer(
                f"С возвращением, {user_info['name']}! Как хотите создать заявку?",
                reply_markup=get_main_kb()
            )
        return

    await message.answer(
        "Добро пожаловать в Thompson Finance Bot!\nПожалуйста, введите ваш логин:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(Command("logout"))
async def cmd_logout(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    
    def logout_user(tid):
        with database.database_session() as db:
            db.query(models.User).filter(
                models.User.telegram_chat_id == tid
            ).update({models.User.telegram_chat_id: None})

            setting = db.query(models.Setting).filter(models.Setting.key == "admin_chat_id").first()
            if setting and setting.value == str(tid):
                db.delete(setting)
            db.commit()

    await run_sync(logout_user, tg_id)
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
        await run_sync(set_admin_chat_id, tg_id)
        await message.answer("✅ Вход выполнен (Админ Сафина)!", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    def verify_and_link(log, pw, tid):
        with database.database_session() as db:
            user = db.query(models.User).filter(models.User.login == log).first()
            if not (user and auth.verify_password(pw, user.password_hash)):
                return "invalid", None

            if user.status != "active":
                return "blocked", None

            user.telegram_chat_id = tid
            db.commit()
            return "ok", {"id": user.id, "position": user.position, "name": user.first_name}

    status, user_info = await run_sync(verify_and_link, login, password, tg_id)
    
    if status == "invalid":
        await message.answer("❌ Неверный логин или пароль. Попробуйте снова:")
        await state.clear()
        await state.set_state(ExpenseWizard.waiting_for_auth)
    elif status == "blocked":
        await message.answer("❌ Аккаунт заблокирован.")
        await state.clear()
    else:
        await state.update_data(user_id=user_info["id"])
        if user_info["position"] == "ceo":
            await message.answer(f"✅ Успешно, {user_info['name']} (CEO)!", reply_markup=get_main_kb(is_ceo=True))
        elif user_info["position"] == "senior_financier":
            await message.answer(f"✅ Успешно, {user_info['name']} (CFO)!", reply_markup=get_main_kb(is_senior=True))
        else:
            await message.answer(f"✅ Успешно, {user_info['name']}!", reply_markup=get_main_kb())
        await state.clear()
