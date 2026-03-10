"""Quick test runner — prints results without encoding issues."""
import sys
import traceback

sys.path.insert(0, ".")

PASS = []
FAIL = []


def run(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")


# ---------------------------------------------------------------------------
# Import service
# ---------------------------------------------------------------------------
from app.services.refund.service import (
    validate_card_number,
    is_school_branch,
    EXPORTABLE_STATUSES,
    EXCLUDED_FROM_EXPORT,
)


# ---------------------------------------------------------------------------
# Card validation tests
# ---------------------------------------------------------------------------
run("card_valid_16_digits",             lambda: assert_(validate_card_number("8600123456789012") == (True,  "8600123456789012")))
run("card_valid_with_spaces",           lambda: assert_(validate_card_number("8600 1234 5678 9012") == (True, "8600123456789012")))
run("card_valid_with_dashes",           lambda: assert_(validate_card_number("8600-1234-5678-9012") == (True, "8600123456789012")))
run("card_too_short_15",                lambda: (assert_(validate_card_number("860012345678901")[0] is False),
                                                 assert_("16" in validate_card_number("860012345678901")[1])))
run("card_too_long_17",                 lambda: assert_(validate_card_number("86001234567890123")[0] is False))
run("card_empty",                       lambda: assert_(validate_card_number("")[0] is False))

# ---------------------------------------------------------------------------
# is_school_branch tests
# ---------------------------------------------------------------------------
run("school_branch_russian",            lambda: assert_(is_school_branch("Школа") is True))
run("school_branch_russian_partial",    lambda: assert_(is_school_branch("Школа Thompson") is True))
run("school_branch_english",            lambda: assert_(is_school_branch("School") is True))
run("school_branch_english_partial",    lambda: assert_(is_school_branch("Thompson School") is True))
run("school_branch_case_insensitive_ru",lambda: assert_(is_school_branch("ШКОЛА") is True))
run("school_branch_case_insensitive_en",lambda: assert_(is_school_branch("SCHOOL") is True))
run("non_school_branch",                lambda: assert_(is_school_branch("Ташкент Сити") is False))
run("none_branch",                      lambda: assert_(is_school_branch(None) is False))
run("empty_branch",                     lambda: assert_(is_school_branch("") is False))

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
run("pending_senior_not_in_exportable", lambda: assert_("pending_senior" not in EXPORTABLE_STATUSES))
run("pending_ceo_not_in_exportable",    lambda: assert_("pending_ceo" not in EXPORTABLE_STATUSES))
run("pending_senior_in_excluded",       lambda: assert_("pending_senior" in EXCLUDED_FROM_EXPORT))
run("pending_ceo_in_excluded",          lambda: assert_("pending_ceo"    in EXCLUDED_FROM_EXPORT))
run("archived_in_excluded",             lambda: assert_("archived"        in EXCLUDED_FROM_EXPORT))
run("confirmed_is_exportable",          lambda: assert_("confirmed" in EXPORTABLE_STATUSES))


# ---------------------------------------------------------------------------
# docx_export import check
# ---------------------------------------------------------------------------
def test_docx_export_importable():
    from app.services.refund.docx_export import generate_application_docx
    assert callable(generate_application_docx)

run("docx_export_importable", test_docx_export_importable)


def assert_(cond):
    if not cond:
        raise AssertionError("Assertion failed")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = len(PASS) + len(FAIL)
print(f"\n{'='*50}")
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed out of {total} tests")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
else:
    print("All tests PASSED!")
    sys.exit(0)
