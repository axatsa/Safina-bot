import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models

db = SessionLocal()
try:
    total = db.query(models.ExpenseRequest).count()
    confirmed = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.status == "confirmed").count()
    approved = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.status == "approved_senior").count()
    refunds = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.request_type == "refund").count()
    blank_refunds = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.request_type == "blank_refund").count()
    
    print(f"Total Requests: {total}")
    print(f"Confirmed Requests: {confirmed}")
    print(f"Approved Senior Requests: {approved}")
    print(f"Refunds: {refunds}")
    print(f"Blank Refunds: {blank_refunds}")
    
    # Check if there's any data for the charts
    charts_data = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.status.in_(["confirmed", "approved_senior"])).count()
    print(f"Items that will show on dynamic charts: {charts_data}")

finally:
    db.close()
