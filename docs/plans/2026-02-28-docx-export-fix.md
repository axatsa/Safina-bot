# DOCX Export Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the issue where DOCX exports are blank by first diagnosing the source of failure (template vs. data) using a simulation script.

**Architecture:** 
1. Create a standalone test script `test_render_docx.py`.
2. Map static data to the template using `docxtpl`.
3. Based on the test result, either sanitize the template XML or fix the backend data retrieval logic in `expenses.py`.

**Tech Stack:** Python, docxtpl

---

### Task 1: Create Diagnostic Script
**Files:**
- Create: `test_render_docx.py`

**Step 1: Write the diagnostic script**
Create a script that uses `docxtpl` to render `backend/app/services/docx/template.docx` with the mock data matching the application's schema.

**Step 2: Commit**
```bash
git add test_render_docx.py
git commit -m "debug: add docx diagnostic script"
```

---

### Task 2: Run Diagnostic & Analyze Result
**Files:**
- Read: `test_output.docx` (generated)

**Step 1: Execute diagnostic**
Run: `& "d:/Projects/Safina bot/.venv/Scripts/python.exe" "d:/Projects/Safina bot/test_render_docx.py"`
Expected: File `test_output.docx` created in root.

**Step 2: Analysis**
- If `test_output.docx` is correctly filled: The issue is in `backend/app/api/expenses.py` (database fetching).
- If `test_output.docx` is blank: The issue is in `template.docx` (XML tags corrupted).

---

### Task 3: Conditional Branching
*This task will be refined once Task 2 completes.*

#### Path A: Template Fix
- Open template, re-type tags without formatting breaks.
- Save and re-run Task 2.

#### Path B: Backend Logic Fix
- Modify `backend/app/api/expenses.py` to add logging of the `data` dictionary.
- Verify that `expense.items` and `expense.created_by` are not None/empty.
- Add fallbacks for empty fields.
