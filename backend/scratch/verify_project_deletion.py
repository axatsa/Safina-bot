import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models, schemas, crud
import uuid

def test_project_deletion():
    db = SessionLocal()
    try:
        # 1. Create a project
        name = f"Delete Me {uuid.uuid4().hex[:4]}"
        code = f"DEL{uuid.uuid4().hex[:4]}".upper()
        print(f"Testing deletion for {name} ({code})")
        project = crud.create_project(db, schemas.ProjectCreate(name=name, code=code, category="corporate"))
        
        # 2. Add a branch
        branch = crud.create_branch(db, project.id, schemas.BranchCreate(name="Branch 1"))
        print(f"Created branch {branch.name} with code {branch.code}")
        
        # 3. Verify counters exist
        project_counters = db.query(models.ProjectCounter).filter(
            models.ProjectCounter.project_code.in_([code, f"{code}-REF"])
        ).all()
        branch_counters = db.query(models.ProjectCounter).filter(
            models.ProjectCounter.project_code.in_([branch.code, f"{branch.code}-REF"])
        ).all()
        
        print(f"Initial counters: Project={len(project_counters)}, Branch={len(branch_counters)}")
        
        # 4. Delete project
        print("Deleting project...")
        success = crud.delete_project(db, project.id)
        if not success:
            print("❌ crud.delete_project returned False")
            return

        # 5. Verify everything is gone
        project_after = db.query(models.Project).filter(models.Project.id == project.id).first()
        branch_after = db.query(models.Branch).filter(models.Branch.id == branch.id).first()
        
        project_counters_after = db.query(models.ProjectCounter).filter(
            models.ProjectCounter.project_code.in_([code, f"{code}-REF"])
        ).all()
        branch_counters_after = db.query(models.ProjectCounter).filter(
            models.ProjectCounter.project_code.in_([branch.code, f"{branch.code}-REF"])
        ).all()
        
        if not project_after and not branch_after and not project_counters_after and not branch_counters_after:
            print("✅ ALL DATA CLEANED UP SUCCESSFULLY")
        else:
            print("❌ CLEANUP FAILED")
            if project_after: print("- Project still exists")
            if branch_after: print("- Branch still exists")
            if project_counters_after: print(f"- {len(project_counters_after)} project counters remain")
            if branch_counters_after: print(f"- {len(branch_counters_after)} branch counters remain")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_project_deletion()
