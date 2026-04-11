from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from app.db import models, schemas
from app.core import auth, database
from app.services.core.user_service import user_service

router = APIRouter(prefix="/team", tags=["team"])

@router.get("", response_model=List[schemas.UserSchema])
def read_team(
    include_blocked: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can view the team list")
    
    query = db.query(models.User)
    if not include_blocked:
        query = query.filter(models.User.status != "blocked")
        
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=schemas.UserSchema)
def create_user(
    user_in: schemas.UserCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create users")
        
    return user_service.create_user(db=db, user_in=user_in)

@router.get("/{user_id}", response_model=schemas.UserSchema)
def read_user(
    user_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db_user = user_service.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.patch("/{user_id}", response_model=schemas.UserSchema)
def update_user(
    user_id: str,
    update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only admins can update other users")
    
    return user_service.update_user(db=db, user_id=user_id, user_in=update)

@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can disable users")
        
    user_service.toggle_user_status(db, user_id=user_id, status="blocked")
    return {"status": "success", "detail": "User blocked"}

@router.patch("/{user_id}/status")
def update_user_status(
    user_id: str,
    update: schemas.UserStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can change user status")

    user_service.toggle_user_status(db, user_id=user_id, status=update.status)
    return {"status": "success", "user_status": update.status}

