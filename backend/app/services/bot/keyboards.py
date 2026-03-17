from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .utils import _BACK

def get_confirm_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Добавить ещё позицию")
    b.button(text="Готово")
    b.button(text=_BACK)
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)

def get_date_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Сейчас")
    b.button(text=_BACK)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def get_currency_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="UZS")
    b.button(text="USD")
    b.button(text=_BACK)
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)

def get_main_kb(is_ceo: bool = False):
    b = ReplyKeyboardBuilder()
    if is_ceo:
        b.button(text="🔄 Проверить новые заявки")
    else:
        b.button(text="Создать инвестицию (в боте)")
        b.button(text="Оформить возврат (в боте)")
        b.button(text="Создать инвестицию (Web-App)")
        b.button(text="Создать возврат (Web-App)")
        b.button(text="📋 Заполнить бланк LAND")
        b.button(text="📋 Заполнить бланк ЛС")
        b.button(text="📋 Заполнить бланк Management")
        b.button(text="📋 Заполнить бланк School")
        b.button(text="🧾 Заявление на возврат")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_fill_method_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="📱 Заполнить в боте")
    b.button(text="🌐 Открыть Web форму")
    b.button(text=_BACK)
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)

def get_projects_kb(projects):
    b = ReplyKeyboardBuilder()
    for p in projects:
        b.button(text=f"{p.name} ({p.code})")
    b.button(text=_BACK)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_retention_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Да")
    b.button(text="Нет")
    b.button(text=_BACK)
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)

def get_back_kb():
    b = ReplyKeyboardBuilder()
    b.button(text=_BACK)
    return b.as_markup(resize_keyboard=True)

def get_reason_kb():
    """Пресет-клавиатура причин возврата с кнопкой Назад."""
    reasons = ["Переезд", "Отчисление", "Болезнь", "Другое"]
    b = ReplyKeyboardBuilder()
    for r in reasons:
        b.button(text=r)
    b.button(text=_BACK)
    b.adjust(2, 2, 1)
    return b.as_markup(resize_keyboard=True)

def get_refund_confirm_markup(expense_id: str) -> InlineKeyboardMarkup:
    """Inline-кнопки редактирования полей на экране подтверждения."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ ID ученика",  callback_data="refund_edit_student_id"),
            InlineKeyboardButton(text="✏️ Причину",     callback_data="refund_edit_reason"),
        ],
        [
            InlineKeyboardButton(text="✏️ Сумму",       callback_data="refund_edit_amount"),
            InlineKeyboardButton(text="✏️ Карту",       callback_data="refund_edit_card_number"),
        ],
        [
            InlineKeyboardButton(text="✅ Отправить заявку", callback_data="refund_submit"),
        ],
    ])
