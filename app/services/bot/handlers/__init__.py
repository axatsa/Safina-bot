from aiogram import Router
from . import auth, expense_wizard, refund_wizard, decisions, documents, ceo

def register_all_handlers(dp):
    router = Router()
    router.include_router(auth.router)
    router.include_router(expense_wizard.router)
    router.include_router(refund_wizard.router)
    router.include_router(decisions.router)
    router.include_router(documents.router)
    router.include_router(ceo.router)
    dp.include_router(router)
