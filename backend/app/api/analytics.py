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
    expense_dist_data = {}
    refund_dist_data = {}
    status_summary = {"Pending": 0, "Approved": 0, "Rejected": 0, "Confirmed": 0}
    
    for expense_tuple in expenses:
        expense = expense_tuple[0]
        branch = expense_tuple[1]
        
        req_type = expense.request_type # 'expense', 'refund', 'blank', 'blank_refund'
        is_refund = req_type in ["refund", "blank_refund"]
        
        # global type filter for entire response
        if type == "refund" and not is_refund:
            continue
        if type == "expense" and is_refund:
            continue

        if not expense.date:
            continue
            
        date_str = expense.date.strftime("%Y-%m-%d")
        
        # update status summary
        if expense.status in ["request", "review", "pending_senior", "revision"]:
            status_summary["Pending"] += 1
        elif expense.status in ["approved_senior", "pending_ceo"]:
            status_summary["Approved"] += 1
        elif expense.status in ["rejected_senior", "rejected_ceo", "declined"]:
            status_summary["Rejected"] += 1
        elif expense.status in ["confirmed", "approved_ceo"]:
            status_summary["Confirmed"] += 1
            
        # Only process approved/confirmed for charts
        if expense.status not in ["confirmed", "approved_senior", "approved_ceo", "pending_ceo"]:
            continue
            
        amount = Decimal(str(expense.total_amount)) if expense.total_amount else Decimal("0")
        if expense.currency == "USD" and expense.usd_rate:
            amount *= Decimal(str(expense.usd_rate))
        elif expense.currency == "RUB" and expense.usd_rate: # Very rough RUB handling if rate is provided
             # If usd_rate is e.g. 12500, and RUB is 100 per USD, then RUB rate is 125.
             # This is a guestimate, but better than nothing if RUB rate isn't explicitly stored.
             amount *= Decimal("135") # Hardcoded rough RUB/UZS if not sure
            
        if date_str not in timeline_data:
            timeline_data[date_str] = {"date": date_str, "expenses": Decimal("0"), "refunds": Decimal("0")}
            
        if is_refund:
            timeline_data[date_str]["refunds"] += amount
        else:
            timeline_data[date_str]["expenses"] += amount
            
        # Distribution
        key = "Unknown"
        if segment == "global":
            # For global segmentation, we group by Request Category (from template_key) or Type
            if is_refund:
                key = "Возвраты"
            else:
                key = "Расходы"
        elif segment == "branch":
            key = branch if branch else "Другое"
        elif segment == "project":
            key = expense.project_name if expense.project_name else "Без проекта"
            
        target_dist = refund_dist_data if is_refund else expense_dist_data
        
        if key not in target_dist:
            target_dist[key] = {"name": key, "value": Decimal("0")}
            
        target_dist[key]["value"] += amount
            
    sorted_timeline = [timeline_data[k] for k in sorted(timeline_data.keys())]
    
    # Backward compatibility: 'distribution' field remains for old clients
    # but now contains the combined data if requested, or just one if filtered
    combined_dist = list(expense_dist_data.values()) + list(refund_dist_data.values())
    
    return {
        "timeline": sorted_timeline,
        "distribution": combined_dist,
        "expense_distribution": list(expense_dist_data.values()),
        "refund_distribution": list(refund_dist_data.values()),
        "summary": status_summary
    }
