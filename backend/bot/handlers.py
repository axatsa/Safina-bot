from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.states import ExpenseWizard
# Imports are already correct, but I'll remove the sys.path hack for cleaner code
import crud, database, models, auth, schemas
import datetime

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

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать в Safina Bot! Пожалуйста, введите ваш логин:")
    await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(ExpenseWizard.waiting_for_auth)
async def process_login(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "login" not in data:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
    else:
        # Check credentials
        with next(database.get_db()) as db:
            user = db.query(models.TeamMember).filter(models.TeamMember.login == data["login"]).first()
            if user and auth.verify_password(message.text, user.password_hash):
                await state.update_data(user_id=user.id, project_id=user.project_id)
                await message.answer(
                    f"Авторизация успешна, {user.first_name}! Давайте создадим заявку.\nВведите дату (ГГГГ-ММ-ДД), или нажмите кнопку «Сейчас»:",
                    reply_markup=get_date_kb()
                )
                await state.set_state(ExpenseWizard.date)
            else:
                await message.answer("Ошибка авторизации. Попробуйте логин еще раз:")
                await state.clear()
                await state.set_state(ExpenseWizard.waiting_for_auth)

@router.message(ExpenseWizard.date)
async def process_date(message: types.Message, state: FSMContext):
    date_val = message.text.lower()
    if date_val == "сейчас":
        d = datetime.datetime.utcnow().isoformat()
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
        await message.answer("Сумма:")
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
            # Calculate total amount
            total_amount = sum(item["amount"] for item in data["items"])
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
                user.telegram_chat_id = message.from_user.id
                db.commit()

            await message.answer(f"✅ Заявка {db_expense.request_id} успешно создана!\nСумма: {total_amount} {currency}", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            await message.answer(f"❌ Ошибка при сохранении: {str(e)}")
        
    await state.clear()

def register_handlers(dp):
    dp.include_router(router)
