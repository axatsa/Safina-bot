"""
Unit tests for the refund service layer.
Tests are independent of FastAPI and aiogram — pure Python/SQLAlchemy.
Run: cd backend && python -m pytest tests/test_refund_service.py -v
"""
import pytest
from app.services.refund.service import (
    validate_card_number,
    is_school_branch,
    EXCLUDED_FROM_EXPORT,
    EXPORTABLE_STATUSES,
)


# ---------------------------------------------------------------------------
# validate_card_number
# ---------------------------------------------------------------------------

def test_card_valid_16_digits():
    ok, cleaned = validate_card_number("8600123456789012")
    assert ok is True
    assert cleaned == "8600123456789012"


def test_card_valid_with_spaces():
    ok, cleaned = validate_card_number("8600 1234 5678 9012")
    assert ok is True
    assert cleaned == "8600123456789012"


def test_card_valid_with_dashes():
    ok, cleaned = validate_card_number("8600-1234-5678-9012")
    assert ok is True
    assert cleaned == "8600123456789012"


def test_card_too_short():
    ok, msg = validate_card_number("860012345678901")  # 15 digits
    assert ok is False
    assert "16" in msg


def test_card_too_long():
    ok, msg = validate_card_number("86001234567890123")  # 17 digits
    assert ok is False
    assert "16" in msg


def test_card_empty():
    ok, msg = validate_card_number("")
    assert ok is False


# ---------------------------------------------------------------------------
# is_school_branch
# ---------------------------------------------------------------------------

def test_school_branch_russian():
    assert is_school_branch("Школа") is True


def test_school_branch_russian_partial():
    assert is_school_branch("Школа Thompson") is True


def test_school_branch_english():
    assert is_school_branch("School") is True


def test_school_branch_english_partial():
    assert is_school_branch("Thompson School") is True


def test_school_branch_case_insensitive_ru():
    assert is_school_branch("ШКОЛА") is True


def test_school_branch_case_insensitive_en():
    assert is_school_branch("SCHOOL") is True


def test_non_school_branch():
    assert is_school_branch("Ташкент Сити") is False


def test_none_branch():
    assert is_school_branch(None) is False


def test_empty_branch():
    assert is_school_branch("") is False


# ---------------------------------------------------------------------------
# Status constants sanity
# ---------------------------------------------------------------------------

def test_pending_statuses_not_in_exportable():
    assert "pending_senior" not in EXPORTABLE_STATUSES
    assert "pending_ceo" not in EXPORTABLE_STATUSES


def test_pending_statuses_in_excluded():
    assert "pending_senior" in EXCLUDED_FROM_EXPORT
    assert "pending_ceo" in EXCLUDED_FROM_EXPORT
    assert "archived" in EXCLUDED_FROM_EXPORT


def test_confirmed_is_exportable():
    assert "confirmed" in EXPORTABLE_STATUSES
