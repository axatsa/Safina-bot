from aiogram.fsm.state import State, StatesGroup

class ExpenseWizard(StatesGroup):
    waiting_for_auth = State()
    project_selection = State()
    
    # Creation flow
    date = State()
    purpose = State()
    
    # Item loop
    item_name = State()
    item_qty = State()
    item_amount = State()
    item_currency = State()
    
    confirm = State()
