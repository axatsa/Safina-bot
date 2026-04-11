import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models

def list_all_branches():
    db = SessionLocal()
    try:
        branches = db.query(models.Branch).all()
        print(f"Total branches: {len(branches)}")
        for b in branches:
            print(f"ID: {b.id} | Name: '{b.name}' | Code: {b.code} | ProjectID: {b.project_id}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_branches()
