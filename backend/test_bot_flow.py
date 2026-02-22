import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import crud, database, models, auth, schemas
from bot.handlers import process_login, process_date, process_purpose, process_item_name, process_item_qty, process_item_amount, process_item_currency, process_finish
from bot.states import ExpenseWizard

class MockMessage:
    def __init__(self, text, from_user_id=123):
        self.text = text
        self.from_user = MagicMock()
        self.from_user.id = from_user_id
        self.answer = AsyncMock()

class TestBotFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup mock state
        self.state = AsyncMock()
        self.state.get_data = AsyncMock(return_value={})
        self.state.update_data = AsyncMock()
        self.state.set_state = AsyncMock()
        self.state.clear = AsyncMock()

    @patch("database.get_db")
    @patch("auth.verify_password")
    async def test_full_successful_flow(self, mock_verify, mock_get_db):
        # 1. Auth Flow
        mock_user = MagicMock(spec=models.TeamMember)
        mock_user.id = 1
        mock_user.project_id = 1
        mock_user.first_name = "Test"
        mock_user.password_hash = "hashed"
        mock_user.login = "tester"
        mock_user.telegram_chat_id = None
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        mock_verify.return_value = True

        # process_login (Part 1: Login)
        msg_login = MockMessage("tester")
        await process_login(msg_login, self.state)
        self.state.update_data.assert_called_with(login="tester")

        # process_login (Part 2: Password)
        self.state.get_data.return_value = {"login": "tester"}
        msg_pass = MockMessage("password123")
        await process_login(msg_pass, self.state)
        self.state.update_data.assert_any_call(user_id=1, project_id=1)
        self.state.set_state.assert_called_with(ExpenseWizard.date)

        # 2. Date Flow
        msg_date = MockMessage("сейчас")
        await process_date(msg_date, self.state)
        self.state.update_data.assert_any_call(date=unittest.mock.ANY)
        self.state.set_state.assert_called_with(ExpenseWizard.purpose)

        # 3. Purpose Flow
        msg_purpose = MockMessage("Test Expense")
        await process_purpose(msg_purpose, self.state)
        self.state.update_data.assert_any_call(purpose="Test Expense", items=[])
        self.state.set_state.assert_called_with(ExpenseWizard.item_name)

        # 4. Item 1: Name -> Qty -> Amount -> Currency
        msg_item_name = MockMessage("Item 1")
        await process_item_name(msg_item_name, self.state)
        self.state.update_data.assert_any_call(current_item_name="Item 1")

        msg_item_qty = MockMessage("2,5") # Test comma handling
        await process_item_qty(msg_item_qty, self.state)
        self.state.update_data.assert_any_call(current_item_qty=2.5)

        msg_item_amount = MockMessage("1000.50") # Test dot handling
        await process_item_amount(msg_item_amount, self.state)
        self.state.update_data.assert_any_call(current_item_amount=1000.5)

        self.state.get_data.return_value = {
            "current_item_name": "Item 1",
            "current_item_qty": 2.5,
            "current_item_amount": 1000.5,
            "items": []
        }
        msg_item_curr = MockMessage("UZS")
        await process_item_currency(msg_item_curr, self.state)
        # Check if item was added correctly
        updated_items = self.state.update_data.call_args[1]['items']
        self.assertEqual(len(updated_items), 1)
        self.assertEqual(updated_items[0]['currency'], "UZS")

        # 5. Finish Flow
        self.state.get_data.return_value = {
            "purpose": "Test Expense",
            "items": updated_items,
            "project_id": 1,
            "user_id": 1,
            "date": datetime.datetime.utcnow().isoformat()
        }
        
        with patch("crud.create_expense_request") as mock_create:
            mock_expense = MagicMock()
            mock_expense.request_id = "TEST-1"
            mock_create.return_value = mock_expense
            
            msg_finish = MockMessage("Готово")
            await process_finish(msg_finish, self.state)
            
            mock_create.assert_called_once()
            args, _ = mock_create.call_args
            self.assertEqual(args[1].total_amount, 1000.5)
            self.assertEqual(args[1].currency, "UZS")
            self.state.clear.assert_called_once()

    @patch("database.get_db")
    async def test_currency_enforcement(self, mock_get_db):
        # Case: Existing item is USD, trying to add UZS
        self.state.get_data.return_value = {
            "current_item_name": "Item 2",
            "current_item_qty": 1,
            "current_item_amount": 10,
            "items": [{"name": "Item 1", "quantity": 1, "amount": 100, "currency": "USD"}]
        }
        msg_item_curr = MockMessage("UZS")
        await process_item_currency(msg_item_curr, self.state)
        
        # Should NOT trigger update_data for items, but should send warning
        last_answer = msg_item_curr.answer.call_args[0][0]
        self.assertIn("В одной заявке должна быть одна валюта", last_answer)

if __name__ == "__main__":
    unittest.main()
