import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Setup path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test DB
os.environ["DATABASE_URL"] = "sqlite:///./media/bot_admin_test.db"

from main import app
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.services.bot.handlers.expense_wizard import process_finish
from app.services.notifications.sse import publish_notification


class TestBotAdminIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Always drop+recreate to start clean (avoids UNIQUE constraint on settings.key)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

        # Create a test user with telegram chat id
        self.user = models.User(
            id="test_user_id",
            login="testuser",
            password_hash="fakehash",
            first_name="Test",
            last_name="User",
            role="user",
            telegram_chat_id=123456
        )
        self.db.add(self.user)

        # Create a test project
        self.project = models.Project(id="test_proj_id", name="Test Project", code="TP")
        self.db.add(self.project)

        # Add admin_chat_id setting
        self.admin_setting = models.Setting(key="admin_chat_id", value="999888777")
        self.db.add(self.admin_setting)

        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./media/bot_admin_test.db"):
             os.remove("./media/bot_admin_test.db")

    @patch("app.services.bot.notifications._send_message", new_callable=AsyncMock)
    @patch("app.services.bot.notifications.publish_notification", new_callable=AsyncMock)
    async def test_bot_submission_triggers_sse_notification(self, mock_publish, mock_send_msg):
        """
        Test that when an expense is finished in the bot,
        it triggers an SSE notification for the admin dashboard.
        """
        # 1. Setup mock message and state
        message = MagicMock()
        message.answer = AsyncMock()

        state = AsyncMock()
        state.get_data.return_value = {
            "user_id": self.user.id,
            "project_id": self.project.id,
            "purpose": "Bot test expense",
            "date": "2026-04-12T12:00:00",
            "items": [
                {"name": "test item", "quantity": 1, "amount": 100, "currency": "UZS"}
            ]
        }

        # 2. Execute process_finish handler
        await process_finish(message, state)

        # 3. Verify Telegram notification was sent to admin
        self.assertTrue(mock_send_msg.called, "Telegram admin notification should be triggered")

        # 4. Verify SSE notification was triggered
        self.assertTrue(mock_publish.called, "SSE notification for admin should be triggered")

        args, kwargs = mock_publish.call_args
        self.assertEqual(args[0], "notifications:admin")
        self.assertIn("Заявка", args[1]["message"])

    @patch("app.services.bot.notifications._send_message", new_callable=AsyncMock)
    @patch("app.services.bot.notifications.publish_notification", new_callable=AsyncMock)
    async def test_bot_submission_answer_on_success(self, mock_publish, mock_send_msg):
        """Test that the bot answers the user with a success message after submission."""
        message = MagicMock()
        message.answer = AsyncMock()

        state = AsyncMock()
        state.get_data.return_value = {
            "user_id": self.user.id,
            "project_id": self.project.id,
            "purpose": "Office supplies",
            "date": "2026-04-15T09:00:00",
            "items": [
                {"name": "Pens", "quantity": 10, "amount": 5000, "currency": "UZS"}
            ]
        }

        await process_finish(message, state)

        # Verify the bot replied to the user
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        self.assertIn("✅", call_text)

    @patch("app.services.bot.notifications._send_message", new_callable=AsyncMock)
    @patch("app.services.bot.notifications.publish_notification", new_callable=AsyncMock)
    async def test_bot_submission_no_items_shows_error(self, mock_publish, mock_send_msg):
        """Test that submitting with no items shows an error, not a crash."""
        message = MagicMock()
        message.answer = AsyncMock()

        state = AsyncMock()
        state.get_data.return_value = {
            "user_id": self.user.id,
            "project_id": self.project.id,
            "purpose": "Empty submission",
            "date": "2026-04-15T09:00:00",
            "items": []  # Empty items list
        }

        await process_finish(message, state)

        # Bot should respond with an error about no items
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        self.assertIn("Нет", call_text)
        # SSE should NOT be triggered
        mock_publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
