from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repository.base import BaseRepository
from app.db.models import Branch, Project, ProjectCounter
from app.db.schemas import BranchCreate, BranchBase
import uuid

class BranchRepository(BaseRepository[Branch, BranchCreate, BranchBase]):
    def get_by_code(self, db: Session, code: str) -> Optional[Branch]:
        return db.query(Branch).filter(Branch.code == code).first()

    def get_multi_by_project(
        self, db: Session, *, project_id: str
    ) -> List[Branch]:
        return db.query(Branch).filter(Branch.project_id == project_id).all()

    def create_with_project(
        self, db: Session, *, obj_in: BranchCreate, project_id: str
    ) -> Branch:
        project = db.query(Project).get(project_id)
        if not project:
            raise ValueError("Project not found")

        # Logic for branch code generation (moved from old crud.py)
        name = obj_in.name.strip()
        branch_slug = "".join(x for x in name if x.isalnum()).upper()[:4]
        code = f"{project.code}-{branch_slug}"
        
        # Verify code uniqueness
        existing_branch = self.get_by_code(db, code)
        existing_counter = db.query(ProjectCounter).filter(ProjectCounter.project_code == code).first()
        
        if existing_branch or existing_counter:
            raise ValueError(f"Код филиала '{code}' уже занят. Пожалуйста, используйте другое название или свяжитесь с администратором.")

        db_obj = Branch(
            name=name,
            code=code,
            project_id=project_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Initialize counters for branch
        if not db.query(ProjectCounter).filter(ProjectCounter.project_code == code).first():
            db.add(ProjectCounter(project_code=code, counter=0))
        if not db.query(ProjectCounter).filter(ProjectCounter.project_code == f"{code}-REF").first():
            db.add(ProjectCounter(project_code=f"{code}-REF", counter=0))
        
        db.commit()
        return db_obj

    def remove(self, db: Session, *, id: str) -> Branch:
        branch = self.get(db, id)
        if branch:
            # Delete related counters
            db.query(ProjectCounter).filter(ProjectCounter.project_code == branch.code).delete()
            db.query(ProjectCounter).filter(ProjectCounter.project_code == f"{branch.code}-REF").delete()
            return super().remove(db, id=id)
        return None

branch_repository = BranchRepository(Branch)
