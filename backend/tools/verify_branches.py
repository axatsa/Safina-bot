import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models
from sqlalchemy import func

db = SessionLocal()
try:
    print("Distribution by Branch (from ExpenseRequest):")
    dist = db.query(models.ExpenseRequest.branch_name, func.count(models.ExpenseRequest.id)).group_by(
        models.ExpenseRequest.branch_name
    ).all()
    
    for branch, count in dist:
        print(f"Branch: {branch or 'None'} -> {count} items")
        
    print("\nTotal items for charts:")
    charts = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.status.in_(["confirmed", "approved_senior"])).count()
    print(f"Eligible for charts: {charts}")

finally:
    db.close()
