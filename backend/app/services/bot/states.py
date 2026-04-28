from aiogram.fsm.state import State, StatesGroup

class ExpenseWizard(StatesGroup):
    waiting_for_auth = State()
    project_selection = State()
    branch_selection = State()
    
    # Creation flow
    date = State()
    purpose = State()
    
    # Item loop
    item_name = State()
    item_qty = State()
    item_amount = State()
    item_currency = State()
    
    confirm = State()
    # Admin Flow
    waiting_for_admin_login = State()
    waiting_for_admin_password = State()

class RefundWizard(StatesGroup):
    branch_selection = State()
    student_id = State()
    reason = State()
    reason_other = State()
    amount = State()
    card_number = State()
    retention = State()
    confirm = State()

class BlankWizard(StatesGroup):
    project_selection = State()  # если 2+ проекта — выбор проекта
    branch_selection = State()   # если проект корпоративный — выбор филиала
    template_selection = State()  # если 2+ шаблона — выбор шаблона
    template = State()
    filling_method = State() # Bot or Web
    purpose = State()
    
    # Items loop
    item_name = State()
    item_qty = State()
    item_amount = State()
    item_currency = State()
    
    confirm = State()

class RefundBlankWizard(StatesGroup):
    project_selection = State()
    branch_selection = State()
    student_id = State()
    reason = State()
    reason_other = State()
    amount = State()
    card_number = State()
    retention = State()
    confirm = State()

