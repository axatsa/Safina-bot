from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from app.db import models, schemas
from app.core import auth, database
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.Token)
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    # Use environment variables for admin login for safety
    admin_login = (os.getenv("ADMIN_LOGIN") or "safina").strip()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "admin123").strip()
    
    # Ensure inputs are strings to avoid attribute errors if pydantic validation is bypassed
    input_login = str(request.login or "").strip()
    input_password = str(request.password or "").strip()

    # Log login attempt (without password)
    logger.info(f"Login attempt for user: {input_login}")
    
    if input_login.lower() == admin_login.lower() and input_password == admin_password:
        logger.info(f"Admin login successful: {input_login}")
        access_token = auth.create_access_token(data={"sub": input_login})
        return {"access_token": access_token, "token_type": "bearer", "role": "admin"}
    
    # Check team members
    try:
        user = db.query(models.TeamMember).filter(models.TeamMember.login == input_login).first()
        if user and auth.verify_password(input_password, user.password_hash):
            if user.status != "active":
                logger.warning(f"Login blocked for user {input_login}: account status is {user.status}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is blocked",
                )
            
            logger.info(f"User login successful: {user.login} (position={user.position})")
            access_token = auth.create_access_token(data={"sub": user.login})
            
            # Use first project ID as default for non-admin frontend views
            project_id = None
            if user.projects:
                project_id = user.projects[0].id
                
            # Return the real position so the frontend can tailor its UI
            role = user.position
            if role not in ("admin", "senior_financier", "ceo"):
                role = "user"
                
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "role": role,
                "projectId": project_id,
            }
        
        if user:
            logger.warning(f"Invalid password for user: {input_login}")
        else:
            logger.warning(f"User not found: {input_login}")
            
    except Exception as e:
        logger.error(f"Database error during login for {input_login}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
