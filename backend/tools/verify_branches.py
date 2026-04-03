import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models
from sqlalchemy import func

db = SessionLocal()
try:
    print("Distribution by Branch:")
    dist = db.query(models.TeamMember.branch, func.count(models.ExpenseRequest.id)).join(
        models.ExpenseRequest, models.ExpenseRequest.created_by_id == models.TeamMember.id
    ).group_by(models.TeamMember.branch).all()
    
    for branch, count in dist:
        print(f"Branch: {branch or 'None'} -> {count} items")
        
    print("\nTotal items for charts:")
    charts = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.status.in_(["confirmed", "approved_senior"])).count()
    print(f"Eligible for charts: {charts}")

finally:
    db.close()
