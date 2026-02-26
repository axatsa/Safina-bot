from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from app.db import models, schemas
from app.core import auth, database

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.Token)
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    # Use environment variables for admin login for safety
    admin_login = (os.getenv("ADMIN_LOGIN") or "safina").strip()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "admin123").strip()
    
    input_login = request.login.strip()
    input_password = request.password.strip()

    # DETAILED DEBUG LOGS
    print(f"DEBUG: Input='{input_login}' (len:{len(input_login)}), Expected='{admin_login}' (len:{len(admin_login)})")
    print(f"DEBUG: Password matches: {input_password == admin_password}")
    
    if input_login.lower() == admin_login.lower() and input_password == admin_password:
        access_token = auth.create_access_token(data={"sub": input_login})
        return {"access_token": access_token, "token_type": "bearer", "role": "admin"}


    
    # Check team members
    user = db.query(models.TeamMember).filter(models.TeamMember.login == request.login).first()
    if user and auth.verify_password(request.password, user.password_hash):
        access_token = auth.create_access_token(data={"sub": user.login})
        # Use first project ID as default for frontend
        project_id = user.projects[0].id if user.projects else None
        return {"access_token": access_token, "token_type": "bearer", "role": "user", "projectId": project_id}
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
