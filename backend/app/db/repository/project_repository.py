from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repository.base import BaseRepository
from app.db.models import Project, ProjectCounter
from app.db.schemas import ProjectCreate, ProjectBase

class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectBase]):
    def get_by_code(self, db: Session, code: str) -> Optional[Project]:
        return db.query(Project).filter(Project.code == code).first()

    def get_multi_by_category(
        self, db: Session, *, category: str, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(Project)
            .filter(Project.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, *, obj_in: ProjectCreate) -> Project:
        db_obj = super().create(db, obj_in=obj_in)
        
        # Initialize counters for project
        counter = ProjectCounter(project_code=db_obj.code, counter=0)
        db.add(counter)
        
        refund_counter = ProjectCounter(project_code=f"{db_obj.code}-REF", counter=0)
        db.add(refund_counter)
        
        db.commit()
        return db_obj

    def remove(self, db: Session, *, id: str) -> Project:
        project = self.get(db, id)
        if project:
            # Delete related counters
            db.query(ProjectCounter).filter(ProjectCounter.project_code == project.code).delete()
            db.query(ProjectCounter).filter(ProjectCounter.project_code == f"{project.code}-REF").delete()
            
            # Delete counters for branches
            for branch in project.branches:
                db.query(ProjectCounter).filter(ProjectCounter.project_code == branch.code).delete()
                db.query(ProjectCounter).filter(ProjectCounter.project_code == f"{branch.code}-REF").delete()
            
            return super().remove(db, id=id)
        return None

project_repository = ProjectRepository(Project)
