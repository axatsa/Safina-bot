from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db import models, schemas
from app.core import auth, database
from app.services.core.project_service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/by-chat-id/{chat_id}", response_model=List[schemas.ProjectSchema])
def get_projects_by_chat_id(
    chat_id: int,
    db: Session = Depends(database.get_db),
):
    """Returns projects assigned to a Telegram user by chat_id, with branches filtered to user-assigned ones. No auth required (called from WebApp)."""
    user = db.query(models.User).options(
        joinedload(models.User.projects).joinedload(models.Project.branches),
        joinedload(models.User.branches)
    ).filter(models.User.telegram_chat_id == chat_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_branch_ids = {b.id for b in user.branches}
    is_privileged = user.role in ["admin", "ceo", "senior_financier"]

    result = []
    for project in user.projects:
        if user_branch_ids:
            filtered = [b for b in project.branches if b.id in user_branch_ids]
        elif is_privileged:
            filtered = list(project.branches)
        else:
            filtered = []

        result.append({
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "category": project.category,
            "templates": project.templates or [],
            "created_at": project.created_at,
            "branches": [
                {"id": b.id, "name": b.name, "code": b.code,
                 "project_id": b.project_id, "created_at": b.created_at}
                for b in filtered
            ],
            "members": [],
        })
    return result

@router.get("", response_model=List[schemas.ProjectSchema])
def read_projects(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Project)
    if category:
        query = query.filter(models.Project.category == category)
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=schemas.ProjectSchema)
def create_project(
    project: schemas.ProjectCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create projects")
    return project_service.create_project(db, project_in=project)

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete projects")
    
    deleted = project_service.delete_project(db, project_id=project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "detail": "Project deleted"}

@router.get("/{project_id}/branches", response_model=List[schemas.BranchSchema])
def read_branches(
    project_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return project_service.get_branches(db, project_id=project_id)

@router.post("/{project_id}/branches", response_model=schemas.BranchSchema)
def create_branch(
    project_id: str,
    branch: schemas.BranchCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can create branches")
    return project_service.create_branch(db, project_id=project_id, branch_in=branch)

@router.delete("/branches/{branch_id}")
def delete_branch(
    branch_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete branches")
    
    deleted = project_service.delete_branch(db, branch_id=branch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Branch not found")
    return {"status": "success", "detail": "Branch deleted"}

@router.post("/{project_id}/members/{user_id}", response_model=schemas.ProjectSchema)
def add_project_member(
    project_id: str,
    user_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can add members")
    return project_service.add_member(db, project_id=project_id, user_id=user_id)

@router.delete("/{project_id}/members/{user_id}", response_model=schemas.ProjectSchema)
def remove_project_member(
    project_id: str,
    user_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    return project_service.remove_member(db, project_id=project_id, user_id=user_id)

@router.patch("/{project_id}/templates", response_model=schemas.ProjectSchema)
def update_project_templates(
    project_id: str,
    update: schemas.ProjectTemplatesUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can update templates")
    
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.templates = update.templates
    db.commit()
    db.refresh(project)
    return project
