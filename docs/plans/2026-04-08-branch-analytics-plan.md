# Branch-wise Analytics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a branch filter to the analytics dashboard to allow users to view financial statistics for individual branches.

**Architecture:** Add a new endpoint for fetching unique branches and update the existing analytics endpoint to support filtering. The frontend will use a Select component to toggle between branches.

**Tech Stack:** FastAPI, SQLAlchemy, React, TanStack Query, Recharts.

---

### Task 1: Backend - Fetch Unique Branches

**Files:**
- Modify: `d:\Projects\Safina bot\expense-tracker-pro\backend\app\api\analytics.py`

**Step 1: Add the branches endpoint**

```python
@router.get("/branches")
def get_branches(
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    branches = db.query(models.TeamMember.branch).filter(models.TeamMember.branch != None).distinct().all()
    return [b[0] for b in branches]
```

**Step 2: Verify endpoint works**
Run manual test or add a temporary test script.

**Step 3: Commit**
```bash
git add backend/app/api/analytics.py
git commit -m "feat(api): add endpoint to fetch unique branches"
```

### Task 2: Backend - Support Branch Filtering in Analytics

**Files:**
- Modify: `d:\Projects\Safina bot\expense-tracker-pro\backend\app\api\analytics.py`

**Step 1: Update get_analytics signature**

```python
@router.get("")
def get_analytics(
    period: str = "1m", 
    segment: str = "global", 
    type: str = "all",
    branch: str = None, # Add this
    db: Session = Depends(database.get_db), 
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
```

**Step 2: Add branch filter to the query**

```python
    query = db.query(
        models.ExpenseRequest,
        models.TeamMember.branch,
        models.TeamMember.team
    ).outerjoin(
        models.TeamMember, models.ExpenseRequest.created_by_id == models.TeamMember.id
    ).filter(
        models.ExpenseRequest.date >= start_date
    )
    
    if branch:
        query = query.filter(models.TeamMember.branch == branch)
        
    expenses = query.all()
```

**Step 3: Commit**
```bash
git add backend/app/api/analytics.py
git commit -m "feat(api): support branch filtering in analytics endpoint"
```

### Task 3: Frontend - Update Store for Branches

**Files:**
- Modify: `d:\Projects\Safina bot\expense-tracker-pro\frontend\src\lib\store.ts`

**Step 1: Add getBranches and update getAnalytics**

```typescript
  async getBranches() {
    return this.request('/analytics/branches');
  },
  async getAnalytics(params: { period?: string; segment?: string; type?: string; branch?: string }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/analytics?${query}`);
  },
```

**Step 2: Commit**
```bash
git add frontend/src/lib/store.ts
git commit -m "feat(store): add branch support to store"
```

### Task 4: Frontend - Implement Branch Filter UI

**Files:**
- Modify: `d:\Projects\Safina bot\expense-tracker-pro\frontend\src\pages\Statistics.tsx`

**Step 1: Fetch branches and manage state**

```tsx
    const [selectedBranch, setSelectedBranch] = useState<string>("all");
    const { data: branches = [] } = useQuery({
        queryKey: ["branches"],
        queryFn: () => store.getBranches(),
    });
```

**Step 2: Update analytics query to include branch**

```tsx
    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics", period, segment, requestType, selectedBranch],
        queryFn: () => store.getAnalytics({ 
            period, 
            segment, 
            type: requestType, 
            branch: selectedBranch === "all" ? undefined : selectedBranch 
        }),
    });
```

**Step 3: Add Select component for branches in the header**

**Step 4: Commit**
```bash
git add frontend/src/pages/Statistics.tsx
git commit -m "feat(ui): add branch filter to statistics page"
```
