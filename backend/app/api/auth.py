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
    admin_login = os.getenv("ADMIN_LOGIN", "safina")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    input_login = str(request.login or "").strip()
    input_password = str(request.password or "").strip()

    logger.info(f"Login attempt for user: {input_login}")
    
    # 1. Check for system admin login
    if input_login.lower() == admin_login.lower() and input_password == admin_password:
        logger.info(f"Admin login successful: {input_login}")
        access_token = auth.create_access_token(data={"sub": input_login})
        return {"access_token": access_token, "token_type": "bearer", "role": "admin", "team": "Администрация"}
    
    # 2. Check users in database
    try:
        user = db.query(models.User).filter(models.User.login == input_login).first()
        if user and auth.verify_password(input_password, user.password_hash):
            if user.status != "active":
                logger.warning(f"Login blocked for user {input_login}: account status is {user.status}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is blocked",
                )
            
            logger.info(f"User login successful: {user.login} (role={user.role})")
            access_token = auth.create_access_token(data={"sub": user.login})
            
            project_id = user.projects[0].id if user.projects else None
                
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "role": user.role,
                "team": user.team,
                "projectId": project_id,
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DATABASE ERROR during login for '{input_login}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )
        
    logger.warning(f"AUTH FAILED: Incorrect login or password for user '{input_login}'")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
