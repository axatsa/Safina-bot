import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models

def cleanup_corrupted_branches():
    db = SessionLocal()
    try:
        # Find branches with empty or null names
        corrupted = db.query(models.Branch).filter(
            (models.Branch.name == "") | 
            (models.Branch.name == None) |
            (models.Branch.name == "null")
        ).all()
        
        print(f"Found {len(corrupted)} corrupted branches to remove.")
        for b in corrupted:
            print(f"Removing branch ID: {b.id} (code: {b.code})")
            # Also remove related counters if they exist
            db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == b.code).delete()
            db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{b.code}-REF").delete()
            db.delete(b)
        
        db.commit()
        print("Cleanup completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_corrupted_branches()
