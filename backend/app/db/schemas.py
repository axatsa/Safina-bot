from pydantic import BaseModel, Field, validator

from typing import List, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal
 
AVAILABLE_TEMPLATE_KEYS = {"land", "drujba", "management", "school"}

class ExpenseStatusEnum(str, Enum):
    request = "request"
    review = "review"
    pending_senior = "pending_senior"
    approved_senior = "approved_senior"
    rejected_senior = "rejected_senior"
    pending_ceo = "pending_ceo"
    approved_ceo = "approved_ceo"
    rejected_ceo = "rejected_ceo"
    confirmed = "confirmed"
    declined = "declined"
    revision = "revision"
    archived = "archived"

class CurrencyEnum(str, Enum):
    UZS = "UZS"
    USD = "USD"

class ExpenseItemSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Наименование товара или услуги")
    quantity: Decimal = Field(..., gt=0, description="Количество, должно быть больше нуля")
    amount: Decimal = Field(..., gt=0, description="Цена за единицу, должна быть больше нуля")
    currency: CurrencyEnum

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    code: str
    templates: List[str] = []

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
    branch: Optional[str] = None
    team: Optional[str] = None
    templates: List[str] = []

class TeamMemberCreate(TeamMemberBase):
    password: str
    project_ids: Optional[List[str]] = []

class TeamMemberSchema(TeamMemberBase):
    id: str
    created_at: datetime
    telegram_chat_id: Optional[int] = None
    projects: List[ProjectSchema] = []
    
    class Config:
        from_attributes = True

# Expense Request Schemas
    branch: Optional[str] = None
    team: Optional[str] = None
    client_name: Optional[str] = None
    passport_series: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issued_by: Optional[str] = None
    passport_date: Optional[str] = None
    phone: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    reason: Optional[str] = None
    amount: Optional[float] = None
    card_number: Optional[str] = None
    bank_name: Optional[str] = None

class ExpenseRequestCreate(BaseModel):
    purpose: str = Field(..., min_length=1, max_length=500)
    items: List[ExpenseItemSchema] = Field(default_factory=list, description="Список позиций (от 0 до 50)")
    project_id: Optional[str] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[CurrencyEnum] = None
    date: Optional[datetime] = None
    request_type: str = "expense"
    template_key: Optional[str] = None
    receipt_photo_file_id: Optional[str] = None
    refund_data: Optional[RefundDataSchema] = None

class ExpenseStatusUpdate(BaseModel):
    status: ExpenseStatusEnum
    comment: Optional[str] = None

class InternalCommentUpdate(BaseModel):
    internal_comment: str

class ExpenseStatusHistorySchema(BaseModel):
    status: str
    comment: Optional[str] = None
    changed_by_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExpenseRequestSchema(ExpenseRequestCreate):
    id: str
    request_id: str
    date: datetime
    status: ExpenseStatusEnum
    created_by: str
    created_by_id: Optional[str] = None
    created_by_position: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    internal_comment: Optional[str] = None
    usd_rate: Optional[Decimal] = None
    status_comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaginatedExpensesSchema(BaseModel):
    items: List[ExpenseRequestSchema]
    total: int        # всего записей в БД по текущим фильтрам
    skip: int         # с какой записи начали
    limit: int        # сколько запросили
    has_more: bool    # есть ли ещё записи после текущей страницы

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

class TeamMemberStatusUpdate(BaseModel):
    status: str  # "active" или "blocked"

# New schemas for template updates
class ProjectTemplatesUpdate(BaseModel):
    templates: List[str]

    @validator("templates")
    def validate_keys(cls, v):
        invalid = set(v) - AVAILABLE_TEMPLATE_KEYS
        if invalid:
            raise ValueError(f"Неизвестные ключи: {invalid}")
        return list(dict.fromkeys(v))  # remove duplicates

class TeamMemberTemplatesUpdate(BaseModel):
    templates: List[str]

    @validator("templates")
    def validate_keys(cls, v):
        invalid = set(v) - AVAILABLE_TEMPLATE_KEYS
        if invalid:
            raise ValueError(f"Неизвестные ключи: {invalid}")
        return list(dict.fromkeys(v))
