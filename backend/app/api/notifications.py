from fastapi import APIRouter, Depends, Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from app.services.notifications.sse import sse_generator
from app.core import auth
from app.db import models
from app.core.database import get_db
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter(prefix="/notifications", tags=["notifications"])

async def get_current_user_sse(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> models.TeamMember:
    """
    Custom dependency for SSE that tries to get token from:
    1. Authorization header
    2. token query parameter
    """
    # 1. Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 2. Try query parameter if no token from header
    if not token:
        token = request.query_params.get("token")
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return auth.get_current_user(db=db, token=token)

@router.get("/stream")
async def notification_stream(
    request: Request, 
    current_user: models.TeamMember = Depends(get_current_user_sse)
):
    """
    Subscribe to real-time notifications via Server-Sent Events (SSE).
    Admins listen to 'notifications:admin', regular users to 'notifications:{user_id}'.
    """
    is_admin = current_user.login == "safina" or current_user.position == "admin"
    channel = "notifications:admin" if is_admin else f"notifications:{current_user.id}"
    
    return EventSourceResponse(sse_generator(request, channel))
