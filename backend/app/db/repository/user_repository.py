from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.repository.base import BaseRepository
from app.db.models import User, Project, Branch
from app.db.schemas import UserCreate, UserUpdate
from app.core.auth import get_password_hash

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_login(self, db: Session, login: str) -> Optional[User]:
        return db.query(User).filter(User.login == login).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            last_name=obj_in.last_name,
            first_name=obj_in.first_name,
            login=obj_in.login,
            password_hash=get_password_hash(obj_in.password),
            position=obj_in.position,
            role=obj_in.role,
            status=obj_in.status,
            team=obj_in.team,
            templates=obj_in.templates
        )
        
        # Handle project and branch assignments
        if obj_in.project_ids:
            projects = db.query(Project).filter(Project.id.in_(obj_in.project_ids)).all()
            db_obj.projects = projects
            
        if obj_in.branch_ids:
            branches = db.query(Branch).filter(Branch.id.in_(obj_in.branch_ids)).all()
            db_obj.branches = branches

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        if update_data.get("password"):
            password_hash = get_password_hash(update_data["password"])
            db_obj.password_hash = password_hash
            del update_data["password"]

        # Handle project and branch updates
        if "project_ids" in update_data:
            project_ids = update_data.pop("project_ids")
            if project_ids is not None:
                projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
                db_obj.projects = projects
                
        if "branch_ids" in update_data:
            branch_ids = update_data.pop("branch_ids")
            if branch_ids is not None:
                branches = db.query(Branch).filter(Branch.id.in_(branch_ids)).all()
                db_obj.branches = branches

        return super().update(db, db_obj=db_obj, obj_in=update_data)

user_repository = UserRepository(User)
