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

def get_main_kb(is_ceo: bool = False, is_senior: bool = False):
    b = ReplyKeyboardBuilder()
    if is_ceo or is_senior:
        b.button(text="🔄 Проверить новые заявки")
    else:
        b.button(text="Создать инвестицию (в боте)")
        b.button(text="Оформить возврат (в боте)")
        b.button(text="Создать инвестицию (Web-App)")
        b.button(text="Создать возврат (Web-App)")
        b.button(text="📋 Заполнить бланк")
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
        # p can be a Project ORM object or a dictionary from projects_data
        if isinstance(p, dict):
            name = p.get("name", str(p))
            code = p.get("code", "")
        else:
            name = getattr(p, "name", str(p))
            code = getattr(p, "code", "")
            
        label = f"{name} ({code})" if code else name
        b.button(text=label)
    b.button(text=_BACK)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_template_select_kb(template_keys: list):
    """Клавиатура выбора типа бланка."""
    names = {
        "land": "LAND",
        "drujba": "ЛС (Дружба)",
        "management": "Management",
        "school": "School",
        "refund": "Заявление на возврат"
    }
    b = ReplyKeyboardBuilder()
    for key in template_keys:
        b.button(text=names.get(key, key.upper()))
    b.button(text=_BACK)
    b.adjust(2, 1)
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

def get_refund_reasons_kb():
    """Кнопки причин для RefundBlankWizard."""
    reasons = [
        "Переезд", "Изменение графика", "Несоответствие",
        "Материальные трудности", "По личным причинам", "Другое"
    ]
    b = ReplyKeyboardBuilder()
    for r in reasons:
        b.button(text=r)
    b.button(text=_BACK)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def get_skip_back_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="⏭ Пропустить")
    b.button(text=_BACK)
    b.adjust(2)
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
