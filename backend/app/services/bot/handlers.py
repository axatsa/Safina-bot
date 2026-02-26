from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from .states import ExpenseWizard
from app.db import models, schemas, crud
from app.core import auth, database
import datetime
import os
from .notifications import set_admin_chat_id, get_admin_chat_id
from app.services.docx_generator import generate_docx


TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

def tashkent_now() -> datetime.datetime:
    """Return current datetime in Tashkent time (UTC+5)."""
    return datetime.datetime.now(tz=TASHKENT_TZ)

router = Router()

def get_confirm_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Добавить ещё позицию")
    builder.button(text="Готово")
    return builder.as_markup(resize_keyboard=True)

def get_date_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сейчас")
    return builder.as_markup(resize_keyboard=True)

def get_currency_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="UZS")
    builder.button(text="USD")
    return builder.as_markup(resize_keyboard=True)

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Создать заявку (в боте)")
    builder.button(text="Веб-форма (быстрее)")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_projects_kb(projects):
    builder = ReplyKeyboardBuilder()
    for p in projects:
        builder.button(text=f"{p.name} ({p.code})")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Check if user already linked
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if user:
            await state.update_data(user_id=user.id)
            await message.answer(
                f"С возвращением, {user.first_name}! Как хотите создать заявку?",
                reply_markup=get_main_kb()
            )
            return

    await message.answer("Добро пожаловать в Thompson Finance Bot! Пожалуйста, введите ваш логин:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(F.text == "Веб-форма (быстрее)")
@router.message(Command("form"))
async def show_form_link(message: types.Message):
    base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
    url = f"{base_url}/submit?chat_id={message.from_user.id}"
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Открыть форму заявки", url=url)
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть форму заявки:\n"
        "_(Убедитесь, что вы авторизованы в боте)_",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.message(F.text == "Создать заявку (в боте)")
async def start_wizard_selection(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).first()
        if not user:
            await message.answer("Пожалуйста, сначала авторизуйтесь с помощью /start")
            return
        
        if len(user.projects) > 1:
            await message.answer("Выберите проект:", reply_markup=get_projects_kb(user.projects))
            await state.set_state(ExpenseWizard.project_selection)
        elif len(user.projects) == 1:
            await state.update_data(project_id=user.projects[0].id)
            await message.answer(
                "Введите дату (ГГГГ-ММ-ДД), или нажмите кнопку «Сейчас»:",
                reply_markup=get_date_kb()
            )
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("К вашему аккаунту не привязано ни одного проекта.")

@router.message(ExpenseWizard.waiting_for_auth)
async def process_login(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "login" not in data:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
    else:
        with next(database.get_db()) as db:
            # Check if it's admin login
            admin_login = os.getenv("ADMIN_LOGIN", "safina")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            
            if data["login"] == admin_login and message.text == admin_password:
                set_admin_chat_id(message.from_user.id)
                await message.answer("✅ Вход выполнен (Администратор)!\nТеперь вы будете получать уведомления о новых заявках в этом чате.")
                await state.clear()
                return

            user = db.query(models.TeamMember).filter(models.TeamMember.login == data["login"]).first()
            if user and auth.verify_password(message.text, user.password_hash):
                if user.status != "active":
                    await message.answer("❌ Ваш аккаунт заблокирован. Обратитесь к администратору.")
                    await state.clear()
                    return
                # IMPORTANT: Clear this chat_id if it's already linked to someone else
                # to prevent UniqueConstraint error
                db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).update({models.TeamMember.telegram_chat_id: None})
                
                # Save chat ID for persistence
                user.telegram_chat_id = message.from_user.id
                db.commit()
                
                await state.update_data(user_id=user.id)
                if len(user.projects) > 1:
                    await message.answer("Авторизация успешна! Выберите проект:", reply_markup=get_projects_kb(user.projects))
                    await state.set_state(ExpenseWizard.project_selection)
                elif len(user.projects) == 1:
                    await state.update_data(project_id=user.projects[0].id)
                    await message.answer(
                        f"Авторизация успешна, {user.first_name}! Давайте создадим заявку.\nВведите дату (ГГГГ-ММ-ДД), или нажмите кнопку «Сейчас»:",
                        reply_markup=get_date_kb()
                    )
                    await state.set_state(ExpenseWizard.date)
                else:
                    await message.answer("Авторизация успешна, но к вам не привязано ни одного проекта.")
                    await state.clear()
            else:
                await message.answer("Ошибка авторизации. Попробуйте логин еще раз:")
                await state.clear()
                await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(ExpenseWizard.project_selection)
async def process_project_selection(message: types.Message, state: FSMContext):
    with next(database.get_db()) as db:
        # Match project by name (Code)
        projects = db.query(models.Project).all()
        selected_project = None
        for p in projects:
            if f"{p.name} ({p.code})" == message.text:
                selected_project = p
                break
        
        if selected_project:
            await state.update_data(project_id=selected_project.id)
            await message.answer(
                f"Проект выбран: {selected_project.name}. Введите дату (ГГГГ-ММ-ДД) или нажмите «Сейчас»:",
                reply_markup=get_date_kb()
            )
            await state.set_state(ExpenseWizard.date)
        else:
            await message.answer("Пожалуйста, выберите проект из списка.")

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    date_val = message.text.lower()
    if date_val == "сейчас":
        d = tashkent_now().isoformat()
    else:
        try:
            d = datetime.datetime.strptime(date_val, "%Y-%m-%d").isoformat()
        except:
            await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД или нажмите «Сейчас»:", reply_markup=get_date_kb())
            return
    await state.update_data(date=d)
    await message.answer("Введите назначение расхода:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.purpose)

@router.message(ExpenseWizard.purpose)
async def process_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text, items=[])
    await message.answer("Добавление позиций сметы.\nВведите наименование товара/услуги:")
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.item_name)
async def process_item_name(message: types.Message, state: FSMContext):
    await state.update_data(current_item_name=message.text)
    await message.answer("Количество:")
    await state.set_state(ExpenseWizard.item_qty)

@router.message(ExpenseWizard.item_qty)
async def process_item_qty(message: types.Message, state: FSMContext):
    try:
        # Support both dot and comma
        qty_str = message.text.replace(",", ".")
        qty = float(qty_str)
        await state.update_data(current_item_qty=qty)
        await message.answer("Сумма (за 1 единицу):")
        await state.set_state(ExpenseWizard.item_amount)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например: 10 или 10.5):")

@router.message(ExpenseWizard.item_amount)
async def process_item_amount(message: types.Message, state: FSMContext):
    try:
        # Support both dot and comma
        amount_str = message.text.replace(",", ".")
        amount = float(amount_str)
        await state.update_data(current_item_amount=amount)
        await message.answer("Выберите валюту:", reply_markup=get_currency_kb())
        await state.set_state(ExpenseWizard.item_currency)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например: 1000 или 1500.50):")

@router.message(ExpenseWizard.item_currency)
async def process_item_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    if currency not in ["UZS", "USD"]:
        await message.answer("Пожалуйста, выберите валюту (UZS или USD) с помощью кнопок:", reply_markup=get_currency_kb())
        return
    
    data = await state.get_data()
    items = data.get("items", [])
    
    # Currency Enforce: check if currency matches existing items
    if items and items[0]["currency"] != currency:
        await message.answer(f"❌ В одной заявке должна быть одна валюта. Ваша текущая валюта: {items[0]['currency']}.\nДля другой валюты создайте новую заявку.")
        return

    items.append({
        "name": data["current_item_name"],
        "quantity": data["current_item_qty"],
        "amount": data["current_item_amount"],
        "currency": currency
    })
    await state.update_data(items=items)
    
    await message.answer("Позиция добавлена. Хотите добавить еще одну?", reply_markup=get_confirm_kb())
    await state.set_state(ExpenseWizard.confirm)

@router.message(ExpenseWizard.confirm, F.text == "Добавить ещё позицию")
async def process_add_more(message: types.Message, state: FSMContext):
    await message.answer("Введите наименование товара/услуги:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ExpenseWizard.item_name)

@router.message(ExpenseWizard.confirm, F.text == "Готово")
async def process_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    with next(database.get_db()) as db:
        try:
            # Calculate total amount (Price * Quantity)
            total_amount = sum(item["amount"] * item["quantity"] for item in data["items"])
            # Currency is guaranteed to be consistent due to enforced check
            currency = data["items"][0]["currency"] if data["items"] else "UZS"

            expense_create = schemas.ExpenseRequestCreate(
                purpose=data["purpose"],
                items=[schemas.ExpenseItemSchema(**item) for item in data["items"]],
                total_amount=total_amount,
                currency=currency,
                project_id=data["project_id"],
                date=datetime.datetime.fromisoformat(data["date"])
            )
            
            db_expense = crud.create_expense_request(db, expense_create, user_id=data["user_id"])
            
            # Link telegram_chat_id if not linked yet
            user = db.query(models.TeamMember).filter(models.TeamMember.id == data["user_id"]).first()
            if user and not user.telegram_chat_id:
                # Clear from others first
                db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == message.from_user.id).update({models.TeamMember.telegram_chat_id: None})
                user.telegram_chat_id = message.from_user.id
                db.commit()

            await message.answer(f"✅ Заявка {db_expense.request_id} успешно создана!\nСумма: {total_amount} {currency}", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            await message.answer(f"❌ Ошибка при сохранении: {str(e)}")
        
    await state.clear()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    await message.answer("Вход в панель администратора. Введите логин:")
    await state.set_state(ExpenseWizard.waiting_for_admin_login)

@router.message(ExpenseWizard.waiting_for_admin_login)
async def process_admin_login(message: types.Message, state: FSMContext):
    await state.update_data(admin_login=message.text)
    await message.answer("Введите пароль:")
    await state.set_state(ExpenseWizard.waiting_for_admin_password)

@router.message(ExpenseWizard.waiting_for_admin_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    admin_login = os.getenv("ADMIN_LOGIN", "safina")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if data["admin_login"] == admin_login and message.text == admin_password:
        set_admin_chat_id(message.from_user.id)
        await message.answer("✅ Вход выполнен! Теперь вы будете получать уведомления о новых заявках в этом чате.")
    else:
        await message.answer("❌ Неверный логин или пароль.")
    await state.clear()

@router.callback_query(F.data.startswith("download_smeta_"))
async def handle_download_smeta(callback: types.CallbackQuery):
    expense_id = callback.data.replace("download_smeta_", "")
    
    with next(database.get_db()) as db:
        expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
        if not expense:
            await callback.answer("Заявка не найдена")
            return
            
        await callback.answer("Генерирую смету...")
        
        # Prepare items, ensuring they are a list of dicts and adding line totals
        items_data = []
        raw_items = expense.items
        if isinstance(raw_items, str):
            import json
            try:
                raw_items = json.loads(raw_items)
            except:
                raw_items = []
                
        if isinstance(raw_items, list):
            for idx, item in enumerate(raw_items):
                if isinstance(item, dict):
                    items_data.append({
                        "no": idx + 1,
                        "name": item.get("name", ""),
                        "quantity": item.get("quantity", 0),
                        "amount": item.get("amount", 0),
                        "price": item.get("amount", 0),
                        "unit_price": item.get("amount", 0),
                        "total": float(item.get("amount", 0)) * float(item.get("quantity", 0))
                    })

        data = {
            "sender_name": expense.created_by,
            "sender_position": expense.created_by_position or "Сотрудник",
            "purpose": expense.purpose,
            "items": items_data,
            "total_amount": float(expense.total_amount),
            "currency": expense.currency,
            "request_id": expense.request_id,
            "date": expense.date.strftime("%d.%m.%Y")
        }
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template.docx")

        try:
            file_stream = generate_docx(template_path, data)
            document = types.BufferedInputFile(file_stream.read(), filename=f"smeta_{expense.request_id}.docx")
            await callback.message.answer_document(document)
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка генерации: {str(e)}")

def register_handlers(dp):
    dp.include_router(router)
