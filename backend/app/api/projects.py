from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from app.db import models, schemas, crud
from app.core import auth, database

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=List[schemas.ProjectSchema])
def read_projects(
    category: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db), 
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    if auth.is_admin(current_user):
        return crud.get_projects(db, skip=skip, limit=limit, category=category)
    return [p for p in current_user.projects if not category or p.category == category]

@router.post("", response_model=schemas.ProjectSchema)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create projects")
    
    existing_project = db.query(models.Project).filter(models.Project.code == project.code.upper()).first()
    if existing_project:
        raise HTTPException(status_code=400, detail=f"Проект с кодом '{project.code}' уже существует")
        
    return crud.create_project(db=db, project=project)

# Branches
@router.get("/{project_id}/branches", response_model=List[schemas.BranchSchema])
def read_project_branches(project_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    return crud.get_branches(db, project_id=project_id)

@router.post("/{project_id}/branches", response_model=schemas.BranchSchema)
def create_project_branch(project_id: str, branch: schemas.BranchCreate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create branches")
    return crud.create_branch(db, project_id, branch)

@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete branches")
    success = crud.delete_branch(db, branch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Branch not found")
    return {"status": "success"}

@router.get("/by-chat-id/{chat_id}", response_model=List[schemas.ProjectSchema])
def read_projects_by_chat_id(chat_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == chat_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.projects

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete projects")
    crud.delete_project(db, project_id)
    return {"status": "success"}

# Member Management
@router.post("/{project_id}/members/{member_id}", response_model=schemas.ProjectSchema)
def add_project_member(project_id: str, member_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can manage project members")
    project = crud.add_project_member(db, project_id, member_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return project

@router.delete("/{project_id}/members/{member_id}", response_model=schemas.ProjectSchema)
def remove_project_member(project_id: str, member_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can manage project members")
    project = crud.remove_project_member(db, project_id, member_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return project

@router.patch("/{project_id}/templates", response_model=schemas.ProjectSchema)
def update_project_templates(project_id: str, update: schemas.ProjectTemplatesUpdate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can update project templates")
    project = crud.update_project_templates(db, project_id, update.templates)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
