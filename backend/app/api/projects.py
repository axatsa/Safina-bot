from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from app.db import models, schemas, crud
from app.core import auth, database

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=List[schemas.ProjectSchema])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if current_user.login == os.getenv("ADMIN_LOGIN", "safina"):
        return crud.get_projects(db, skip=skip, limit=limit)
    return current_user.projects

@router.get("/by-chat-id/{chat_id}", response_model=List[schemas.ProjectSchema])
def read_projects_by_chat_id(chat_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == chat_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.projects

@router.post("", response_model=schemas.ProjectSchema)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can create projects")
    
    existing_project = db.query(models.Project).filter(models.Project.code == project.code).first()
    if existing_project:
        raise HTTPException(status_code=400, detail=f"Проект с кодом '{project.code}' уже существует")
        
    return crud.create_project(db=db, project=project)

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(database.get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(proj)
    db.commit()
    return {"status": "success"}

@router.post("/{project_id}/members/{member_id}")
def add_project_member(project_id: str, member_id: str, db: Session = Depends(database.get_db)):
    member = crud.add_project_member(db, project_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return {"status": "success"}

@router.delete("/{project_id}/members/{member_id}")
def remove_project_member(project_id: str, member_id: str, db: Session = Depends(database.get_db)):
    member = crud.remove_project_member(db, project_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return {"status": "success"}
