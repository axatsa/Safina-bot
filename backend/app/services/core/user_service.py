from sqlalchemy.orm import Session
from app.db.repository.user_repository import user_repository
from app.db.schemas import UserCreate, UserUpdate, UserRole
from app.db.models import User
from typing import Optional, List
from fastapi import HTTPException, status

class UserService:
    def create_user(self, db: Session, user_in: UserCreate) -> User:
        # Check if login exists
        existing_user = user_repository.get_by_login(db, login=user_in.login)
        if existing_user:
            if existing_user.status == "blocked":
                # Automatically reactivate and update the blocked user with new info
                user_update = UserUpdate(
                    last_name=user_in.last_name,
                    first_name=user_in.first_name,
                    position=user_in.position,
                    login=user_in.login,
                    password=user_in.password,
                    project_ids=user_in.project_ids,
                    branch_ids=user_in.branch_ids,
                    role=user_in.role,
                    team=user_in.team
                )
                # Add status update to move from blocked to active
                update_dict = user_update.dict(exclude_unset=True)
                update_dict["status"] = "active"
                return user_repository.update(db, db_obj=existing_user, obj_in=update_dict)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login already registered"
            )
        
        return user_repository.create(db, obj_in=user_in)

    def get_user(self, db: Session, user_id: str) -> Optional[User]:
        return user_repository.get(db, id=user_id)

    def update_user(self, db: Session, user_id: str, user_in: UserUpdate) -> User:
        user = user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user_in.login:
            existing = user_repository.get_by_login(db, login=user_in.login)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="Login already taken")
                
        return user_repository.update(db, db_obj=user, obj_in=user_in)

    def toggle_user_status(self, db: Session, user_id: str, status: str) -> User:
        user = user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user_repository.update(db, db_obj=user, obj_in={"status": status})

user_service = UserService()
