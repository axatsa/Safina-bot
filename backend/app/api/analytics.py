from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import models
from app.core import database, auth
from decimal import Decimal
from typing import Optional, List

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/branches")
def get_branches(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    branches = db.query(models.Branch.name).distinct().all()
    branch_list = [b[0] for b in branches]
    logger.info(f"Unique branches found: {branch_list}")
    return branch_list

@router.get("")
def get_analytics(
    period: str = "1m", 
    segment: str = "global", 
    type: str = "all",
    branch: Optional[str] = None,
    branch_names: Optional[List[str]] = Query(None),
    project_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
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
        
    query = db.query(models.ExpenseRequest).filter(
        models.ExpenseRequest.date >= start_date
    )
    
    if branch:
        query = query.filter(models.ExpenseRequest.branch_name == branch)
        
    if branch_names:
        query = query.filter(models.ExpenseRequest.branch_name.in_(branch_names))
        
    if project_ids:
        query = query.filter(models.ExpenseRequest.project_id.in_(project_ids))
        
    expenses = query.all()
    
    timeline_data = {}
    expense_dist_data = {}
    refund_dist_data = {}
    user_dist_data = {} 
    status_summary = {"Pending": 0, "Approved": 0, "Rejected": 0, "Confirmed": 0}
    
    for expense in expenses:
        req_type = expense.request_type 
        is_refund = req_type in ["refund", "blank_refund"]
        
        if type == "refund" and not is_refund:
            continue
        if type == "expense" and is_refund:
            continue

        if not expense.date:
            continue
            
        date_str = expense.date.strftime("%Y-%m-%d")
        
        if expense.status in ["request", "review", "pending_senior", "revision"]:
            status_summary["Pending"] += 1
        elif expense.status in ["approved_senior", "pending_ceo"]:
            status_summary["Approved"] += 1
        elif expense.status in ["rejected_senior", "rejected_ceo", "declined"]:
            status_summary["Rejected"] += 1
        elif expense.status in ["confirmed", "approved_ceo"]:
            status_summary["Confirmed"] += 1
            
        if expense.status not in ["confirmed", "approved_senior", "approved_ceo", "pending_ceo"]:
            continue
            
        amount = Decimal(str(expense.total_amount)) if expense.total_amount else Decimal("0")
        if expense.currency == "USD" and expense.usd_rate:
            amount *= Decimal(str(expense.usd_rate))
        elif expense.currency == "RUB" and expense.usd_rate: 
             amount *= Decimal("135") 
            
        if date_str not in timeline_data:
            timeline_data[date_str] = {"date": date_str, "expenses": Decimal("0"), "refunds": Decimal("0")}
            
        if is_refund:
            timeline_data[date_str]["refunds"] += amount
        else:
            timeline_data[date_str]["expenses"] += amount
            
        key = "Unknown"
        if segment == "global":
            if is_refund:
                key = "Возвраты"
            else:
                key = "Расходы"
        elif segment == "branch":
            key = expense.branch_name if expense.branch_name else "Другое"
        elif segment == "project":
            key = expense.project_name if expense.project_name else "Без проекта"
            
        target_dist = refund_dist_data if is_refund else expense_dist_data
        
        if key not in target_dist:
            target_dist[key] = {"name": key, "value": Decimal("0")}
            
        target_dist[key]["value"] += amount

        user_name = expense.created_by
        if user_name not in user_dist_data:
            user_dist_data[user_name] = {"name": user_name, "count": 0, "total": Decimal("0")}
        
        user_dist_data[user_name]["count"] += 1
        user_dist_data[user_name]["total"] += amount
            
    sorted_timeline = [timeline_data[k] for k in sorted(timeline_data.keys())]
    combined_dist = list(expense_dist_data.values()) + list(refund_dist_data.values())
    
    return {
        "timeline": sorted_timeline,
        "distribution": combined_dist,
        "expense_distribution": list(expense_dist_data.values()),
        "refund_distribution": list(refund_dist_data.values()),
        "user_distribution": list(user_dist_data.values()), 
        "summary": status_summary
    }
