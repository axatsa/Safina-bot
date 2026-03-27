from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import models
from app.core import database, auth
from decimal import Decimal

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("")
def get_analytics(
    period: str = "1m", 
    segment: str = "global", 
    type: str = "all",
    db: Session = Depends(database.get_db), 
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    now = datetime.utcnow()
    
    if period == "1m":
        start_date = now - timedelta(days=30)
    elif period == "3m":
        start_date = now - timedelta(days=90)
    elif period == "6m":
        start_date = now - timedelta(days=180)
    elif period == "1y":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
        
    expenses = db.query(
        models.ExpenseRequest,
        models.TeamMember.branch,
        models.TeamMember.team
    ).outerjoin(
        models.TeamMember, models.ExpenseRequest.created_by_id == models.TeamMember.id
    ).filter(
        models.ExpenseRequest.date >= start_date
    ).all()
    
    timeline_data = {}
    distribution_data = {}
    status_summary = {"Pending": 0, "Approved": 0, "Rejected": 0, "Confirmed": 0}
    
    for expense_tuple in expenses:
        expense = expense_tuple[0]
        branch = expense_tuple[1]
        team = expense_tuple[2]
        
        req_type = expense.request_type # 'expense', 'refund', 'blank', 'blank_refund'
        is_refund = req_type in ["refund", "blank_refund"]
        
        if type == "refund" and not is_refund:
            continue
        if type == "expense" and is_refund:
            continue

        if not expense.date:
            continue
            
        date_str = expense.date.strftime("%Y-%m-%d")
        
        # update status summary
        if expense.status in ["request", "review", "pending_senior"]:
            status_summary["Pending"] += 1
        elif expense.status == "approved_senior":
            status_summary["Approved"] += 1
        elif expense.status in ["rejected_senior", "declined"]:
            status_summary["Rejected"] += 1
        elif expense.status == "confirmed":
            status_summary["Confirmed"] += 1
            
        # Only process approved/confirmed for charts
        if expense.status not in ["confirmed", "approved_senior"]:
            continue
            
        amount = Decimal(str(expense.total_amount)) if expense.total_amount else Decimal("0")
        if expense.currency == "USD" and expense.usd_rate:
            amount *= Decimal(str(expense.usd_rate))
            
        if date_str not in timeline_data:
            timeline_data[date_str] = {"date": date_str, "expenses": 0, "refunds": 0}
            
        if req_type == "refund":
            timeline_data[date_str]["refunds"] += amount
        else:
            timeline_data[date_str]["expenses"] += amount
            
        # Distribution
        key = "Unknown"
        if segment == "global" or segment == "branch":
            key = branch if branch else "Другое"
        elif segment == "project":
            key = expense.project_name if expense.project_name else "Без проекта"
            
        if key not in distribution_data:
            distribution_data[key] = {"name": key, "value": 0}
            
        distribution_data[key]["value"] += amount
            
    sorted_timeline = [timeline_data[k] for k in sorted(timeline_data.keys())]
    
    return {
        "timeline": sorted_timeline,
        "distribution": list(distribution_data.values()),
        "summary": status_summary
    }
