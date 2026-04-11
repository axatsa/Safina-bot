from sqlalchemy.orm import Session
from app.db.repository.project_repository import project_repository
from app.db.repository.branch_repository import branch_repository
from app.db.schemas import ProjectCreate, BranchCreate, ProjectBase, BranchBase
from app.db.models import Project, Branch, User
from typing import List, Optional
from fastapi import HTTPException

class ProjectService:
    def create_project(self, db: Session, project_in: ProjectCreate) -> Project:
        existing = project_repository.get_by_code(db, code=project_in.code.upper())
        if existing:
            raise HTTPException(status_code=400, detail="Project with this code already exists")
        return project_repository.create(db, obj_in=project_in)

    def delete_project(self, db: Session, project_id: str) -> bool:
        project = project_repository.remove(db, id=project_id)
        return project is not None

    def create_branch(self, db: Session, project_id: str, branch_in: BranchCreate) -> Branch:
        return branch_repository.create_with_project(db, obj_in=branch_in, project_id=project_id)

    def delete_branch(self, db: Session, branch_id: str) -> bool:
        branch = branch_repository.remove(db, id=branch_id)
        return branch is not None

    def add_member(self, db: Session, project_id: str, user_id: str) -> Project:
        project = project_repository.get(db, id=project_id)
        user = db.query(User).get(user_id)
        if not (project and user):
            raise HTTPException(status_code=404, detail="Project or User not found")
        
        if project not in user.projects:
            user.projects.append(project)
            db.commit()
            db.refresh(project)
        return project

    def remove_member(self, db: Session, project_id: str, user_id: str) -> Project:
        project = project_repository.get(db, id=project_id)
        user = db.query(User).get(user_id)
        if not (project and user):
            raise HTTPException(status_code=404, detail="Project or User not found")
        
        if project in user.projects:
            user.projects.remove(project)
            db.commit()
            db.refresh(project)
        return project

project_service = ProjectService()
