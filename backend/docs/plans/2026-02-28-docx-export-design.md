# Design: DOCX Export Diagnostic Simulation

**Date:** 2026-02-28
**Topic:** Fixing Blank DOCX Export

## Current Problem
The application generates DOCX files that contain the template's layout and styling, but all fields mapped to `{{ key }}` and `{% for ... %}` loops appear empty.

## Goal
Verify if the issue lies within:
1.  **Template Compatibility:** Are the tags in `template.docx` corrupted or unreadable by `docxtpl`?
2.  **Data Logic:** Is the backend in `expenses.py` failing to fetch or format the data correctly before passing it to the generator?

## Proposed Approach
Create a standalone diagnostic script `test_render_docx.py` that renders the production template with static, known-good data.

### Approach 1: Diagnostic Simulation (Selected)
- **Logic:** Direct invocation of `docxtpl.DocxTemplate.render()` with a mock object matching the application's data schema.
- **Success Criteria:** If `test_output.docx` is correctly populated, the template is fine, and we focus on `backend/app/api/expenses.py` and CRM logic.

## Design Details
### 1. Mock Data Structure
Must match `backend/app/api/expenses.py:271` exactly:
- `sender_name`: string
- `sender_position`: string
- `purpose`: string
- `items`: list of dicts (`no`, `name`, `quantity`, `price`, `total`)
- `total_amount`: float
- `currency`: string
- `request_id`: string
- `date`: string (already formatted in `generator.py`)

### 2. Files Involved
- `d:\Projects\Safina bot\expense-tracker-pro\test_render_docx.py` (New)
- `d:\Projects\Safina bot\expense-tracker-pro\backend\app\services\docx\template.docx` (Read)

## Verification Plan
1. Run the script using the project's virtual environment.
2. Manually inspect `test_output.docx`.
3. If successful, proceed to debug database data fetching in the main app.
