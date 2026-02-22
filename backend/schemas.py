from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ExpenseStatusEnum(str, Enum):
    request = "request"
    review = "review"
    confirmed = "confirmed"
    declined = "declined"
    revision = "revision"
    archived = "archived"

class CurrencyEnum(str, Enum):
    UZS = "UZS"
    USD = "USD"

class ExpenseItemSchema(BaseModel):
    name: str
    quantity: float
    amount: float
    currency: CurrencyEnum

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    code: str

class ProjectCreate(ProjectBase):
    pass

class MemberSummary(BaseModel):
    id: str
    last_name: str
    first_name: str
    position: Optional[str] = None

    class Config:
        from_attributes = True

class ProjectSchema(ProjectBase):
    id: str
    created_at: datetime
    members: List[MemberSummary] = []
    
    class Config:
        from_attributes = True

# Team Member Schemas
class TeamMemberBase(BaseModel):
    last_name: str
    first_name: str
    login: str
    position: Optional[str] = None
    status: str = "active"

class TeamMemberCreate(TeamMemberBase):
    password: str
    project_ids: List[str]

class TeamMemberSchema(TeamMemberBase):
    id: str
    created_at: datetime
    telegram_chat_id: Optional[int] = None
    projects: List[ProjectSchema] = []
    
    class Config:
        from_attributes = True

# Expense Request Schemas
class ExpenseRequestCreate(BaseModel):
    purpose: str
    items: List[ExpenseItemSchema]
    project_id: str
    total_amount: Optional[float] = None
    currency: Optional[CurrencyEnum] = None
    date: Optional[datetime] = None

class ExpenseStatusUpdate(BaseModel):
    status: ExpenseStatusEnum
    comment: Optional[str] = None

class InternalCommentUpdate(BaseModel):
    internal_comment: str

class ExpenseRequestSchema(ExpenseRequestBase):
    id: str
    request_id: str
    date: datetime
    status: ExpenseStatusEnum
    created_by: str
    created_by_id: str
    created_by_position: Optional[str] = None
    project_name: str
    project_code: str
    internal_comment: Optional[str] = None
    status_comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str = "admin"
    projectId: Optional[str] = None

class TokenData(BaseModel):
    login: Optional[str] = None

class LoginRequest(BaseModel):
    login: str
    password: str
