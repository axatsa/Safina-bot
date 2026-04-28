import sys
import os
import json
from decimal import Decimal
from datetime import datetime

# Setup path
sys.path.append(os.path.abspath('.'))

from app.core.database import SessionLocal
from app.db import models

db = SessionLocal()
expenses = db.query(models.ExpenseRequest).all()

invalid_statuses = set()
for exp in expenses:
    if exp.status not in ["request", "review", "pending_senior", "approved_senior", "rejected_senior", "pending_ceo", "approved_ceo", "rejected_ceo", "confirmed", "declined", "revision", "archived"]:
        invalid_statuses.add(exp.status)

print(f"Invalid statuses in DB: {invalid_statuses}")
