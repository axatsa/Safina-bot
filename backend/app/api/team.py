from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from app.db import models, schemas, crud
from app.core import auth, database

router = APIRouter(prefix="/team", tags=["team"])

@router.get("", response_model=List[schemas.TeamMemberSchema])
def read_team(
    include_blocked: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can view the team list")
    
    query = db.query(models.TeamMember)
    if not include_blocked:
        query = query.filter(models.TeamMember.status != "blocked")
        
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=schemas.TeamMemberSchema)
def create_team_member(
    member: schemas.TeamMemberCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create team members")
        
    db_user = db.query(models.TeamMember).filter(models.TeamMember.login == member.login).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    return crud.create_team_member(db=db, member=member)


@router.delete("/{member_id}")
def delete_team_member(
    member_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can delete team members")
        
    user = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Мягкое удаление вместо физического
    user.status = "blocked"
    user.telegram_chat_id = None  # разлогинить из Telegram бота немедленно
    db.commit()
    
    return {"status": "success", "detail": "Member blocked"}

@router.patch("/{member_id}/status")
def update_member_status(
    member_id: str,
    update: schemas.TeamMemberStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can change member status")

    if update.status not in ("active", "blocked"):
        raise HTTPException(status_code=400, detail="Status must be 'active' or 'blocked'")

    user = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")

    user.status = update.status
    db.commit()
    return {"status": "success", "member_status": update.status}
