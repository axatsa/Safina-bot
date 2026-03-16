from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from app.services.notifications.sse import sse_generator
from app.core import auth
from app.db import models

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/stream")
async def notification_stream(request: Request, current_user: models.TeamMember = Depends(auth.get_current_user)):
    """
    Subscribe to real-time notifications via Server-Sent Events (SSE).
    Admins listen to 'notifications:admin', regular users to 'notifications:{user_id}'.
    """
    is_admin = current_user.login == "safina" or current_user.position == "admin"
    channel = "notifications:admin" if is_admin else f"notifications:{current_user.id}"
    
    return EventSourceResponse(sse_generator(request, channel))
