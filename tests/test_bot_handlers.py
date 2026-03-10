"""
Bot FSM handler unit tests.
Tests the refund wizard state transitions and validation logic
without running a real aiogram event loop.
Run: cd backend && python -m pytest tests/test_bot_handlers.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.refund.service import validate_card_number, is_school_branch


# ---------------------------------------------------------------------------
# Card validation used inside handlers
# ---------------------------------------------------------------------------

def test_handler_card_validation_16_digits_pass():
    ok, _ = validate_card_number("8600123456789012")
    assert ok is True


def test_handler_card_validation_15_digits_fail():
    ok, msg = validate_card_number("123456789012345")
    assert ok is False
    assert "16" in msg


# ---------------------------------------------------------------------------
# Mock-based FSM transition tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_refund_amount_accepts_valid():
    """A valid positive number should advance FSM to card_number state."""
    from app.services.bot.handlers import process_refund_amount
    from app.services.bot.states import RefundWizard

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"reason": "Переезд"})
    message = AsyncMock()
    message.text = "1500000"

    with patch("app.services.bot.handlers.get_back_kb", return_value=MagicMock()):
        await process_refund_amount(message, state)

    state.update_data.assert_called_once_with(amount=1500000.0)
    state.set_state.assert_called_once_with(RefundWizard.card_number)


@pytest.mark.asyncio
async def test_process_refund_amount_rejects_non_number():
    """A non-numeric string should NOT advance to next state."""
    from app.services.bot.handlers import process_refund_amount

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"reason": "Болезнь"})
    message = AsyncMock()
    message.text = "abc"

    with patch("app.services.bot.handlers.get_back_kb", return_value=MagicMock()):
        await process_refund_amount(message, state)

    state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_refund_card_16_digits_ok():
    """A 16-digit card number advances to retention state."""
    from app.services.bot.handlers import process_refund_card
    from app.services.bot.states import RefundWizard

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"amount": 1000000.0})
    message = AsyncMock()
    message.text = "8600123456789012"

    with patch("app.services.bot.handlers.get_retention_kb", return_value=MagicMock()), \
         patch("app.services.bot.handlers.get_back_kb", return_value=MagicMock()):
        await process_refund_card(message, state)

    state.set_state.assert_called_once_with(RefundWizard.retention)
    state.update_data.assert_called_once_with(card_number="8600123456789012")


@pytest.mark.asyncio
async def test_process_refund_card_15_digits_stays():
    """A 15-digit card number should NOT advance to next state."""
    from app.services.bot.handlers import process_refund_card

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"amount": 1000000.0})
    message = AsyncMock()
    message.text = "860012345678901"  # 15 digits

    with patch("app.services.bot.handlers.get_back_kb", return_value=MagicMock()):
        await process_refund_card(message, state)

    state.set_state.assert_not_called()
    message.answer.assert_called_once()
    assert "16" in message.answer.call_args.args[0]


@pytest.mark.asyncio
async def test_process_refund_reason_back_navigation():
    """Pressing ◀️ Назад from reason step returns to student_id step."""
    from app.services.bot.handlers import process_refund_reason
    from app.services.bot.states import RefundWizard

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"student_id": "STU001"})
    message = AsyncMock()
    message.text = "◀️ Назад"

    with patch("app.services.bot.handlers.get_reason_kb", return_value=MagicMock()):
        await process_refund_reason(message, state)

    state.set_state.assert_called_once_with(RefundWizard.student_id)
    state.update_data.assert_not_called()


@pytest.mark.asyncio
async def test_start_refund_wizard_saves_branch_team():
    """After /start, the wizard should save user.branch and user.team."""
    from app.services.bot.handlers import start_refund_wizard
    from app.services.bot.states import RefundWizard
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.branch = "Thompson School"
    mock_user.team = "Grade 5"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    state = AsyncMock()
    message = AsyncMock()
    message.from_user.id = 999

    with patch("app.services.bot.handlers.database.get_db", return_value=iter([mock_db])):
        await start_refund_wizard(message, state)

    state.update_data.assert_called_once_with(
        user_id="user-123",
        branch="Thompson School",
        team="Grade 5",
    )
    state.set_state.assert_called_once_with(RefundWizard.student_id)
