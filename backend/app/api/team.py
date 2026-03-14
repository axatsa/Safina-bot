from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from app.db import models, schemas, crud
from app.core import auth, database

router = APIRouter(prefix="/team", tags=["team"])

@router.get("", response_model=List[schemas.TeamMemberSchema])
def read_team(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can view the team list")
    return crud.get_team(db, skip=skip, limit=limit)

@router.post("", response_model=schemas.TeamMemberSchema)
def create_team_member(member: schemas.TeamMemberCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.TeamMember).filter(models.TeamMember.login == member.login).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    return crud.create_team_member(db=db, member=member)

@router.delete("/{member_id}")
def delete_team_member(member_id: str, db: Session = Depends(database.get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(user)
    db.commit()
    return {"status": "success"}
