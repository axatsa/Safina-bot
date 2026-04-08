# Design: Branch-wise Analytics Filter

## Goal
Add the ability to filter the analytics dashboard by branch to allow detailed financial tracking per branch.

## Proposed Changes

### Backend (FastAPI)
- **`GET /analytics/branches`**:
    - Query `TeamMember.branch` for all unique, non-null values.
    - Return a list of strings: `["School", "Kindergarten", ...]`
- **Update `GET /analytics`**:
    - Add `branch: Optional[str] = None` query parameter.
    - If provided, filter `ExpenseRequest` query by `TeamMember.branch == branch`.
    - Ensure all aggregations (timeline, distribution, summary) respect this filter.

### Frontend (React + Vite)
- **Store**:
    - Add `getBranches()` method.
    - Update `getAnalytics(params)` to include `branch`.
- **UI (Statistics.tsx)**:
    - Inline branch selection dropdown in the header.
    - Use "All Branches" as the default selection.
    - Reactive update of all charts when the branch is changed.

## Success Criteria
- User can see a list of available branches in a dropdown.
- Selecting a branch correctly filters the "Traffic Dynamics", "Expense Structure", and "Returns Structure" charts.
- Summary cards (Pending, Approved, Confirmed, Rejected) reflect branch-specific counts.
