import os
import sys

# Add the parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models

def migrate():
    db = SessionLocal()
    try:
        # 1. Update all existing projects to 'startup' category
        projects = db.query(models.Project).all()
        for project in projects:
            if not project.category:
                project.category = 'startup'
            
            # Ensure separate counters for refunds exist
            # (crud.create_project does this now, but existing ones won't have it)
            from app.db.models import ProjectCounter
            refund_prefix = f"{project.code}-REF"
            existing_counter = db.query(ProjectCounter).filter(ProjectCounter.project_code == refund_prefix).first()
            if not existing_counter:
                db.add(ProjectCounter(project_code=refund_prefix, counter=0))
        
        db.commit()
        print(f"Successfully migrated {len(projects)} projects to 'startup' category and initialized refund counters.")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
