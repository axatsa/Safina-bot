import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.db import models, schemas, crud
import uuid

def test_branch_creation():
    db = SessionLocal()
    try:
        # 1. Create a dummy project
        project_name = f"Test Project {uuid.uuid4().hex[:6]}"
        project_code = f"TP{uuid.uuid4().hex[:4]}".upper()
        print(f"Creating project {project_name} with code {project_code}")
        project = crud.create_project(db, schemas.ProjectCreate(
            name=project_name,
            code=project_code,
            category="corporate"
        ))
        
        # 2. Try to create a branch with the SAME name/code as the project
        # This used to cause an IntegrityError in ProjectCounter
        branch_name = project_code 
        print(f"Creating branch with name {branch_name} (colliding with project code)")
        branch = crud.create_branch(db, project.id, schemas.BranchCreate(name=branch_name))
        
        print(f"✅ Branch created successfully: {branch.name} (Code: {branch.code})")
        
        # 3. Verify counters
        counter1 = db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == branch.code).first()
        counter2 = db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{branch.code}-REF").first()
        
        if counter1 and counter2:
            print("✅ Counters initialized correctly")
        else:
            print("❌ Counters missing!")
            
        # 4. Try creating another branch with same name
        print(f"Creating another branch with same name {branch_name}")
        branch2 = crud.create_branch(db, project.id, schemas.BranchCreate(name=branch_name))
        print(f"✅ Second branch created successfully: {branch2.name} (Code: {branch2.code})")
        
        if branch2.code != branch.code:
            print(f"✅ Uniqueness check works: {branch.code} != {branch2.code}")
        else:
            print("❌ Uniqueness check failed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        # db.query(models.Project).filter(models.Project.id == project.id).delete()
        # db.commit()
        db.close()

if __name__ == "__main__":
    test_branch_creation()
