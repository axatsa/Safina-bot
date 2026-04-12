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
        
        # 3. Verify Telegram notification was sent
        self.assertTrue(mock_send_msg.called, "Telegram admin notification should be triggered")
        
        # 4. Verify SSE notification was triggered
        self.assertTrue(mock_publish.called, "SSE notification for admin should be triggered")
        
        args, kwargs = mock_publish.call_args
        self.assertEqual(args[0], "notifications:admin")
        self.assertIn("Заявка", args[1]["message"])

if __name__ == "__main__":
    unittest.main()
