from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, JSON, BigInteger, Text
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

from sqlalchemy import Table

# Association table for TeamMember <-> Project
member_projects = Table(
    "member_projects",
    Base.metadata,
    Column("member_id", String, ForeignKey("team_members.id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", String, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    templates = Column(JSON, nullable=False, default=list) # Шаблоны назначенные Сафиной
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    members = relationship("TeamMember", secondary=member_projects, back_populates="projects")
    expenses = relationship("ExpenseRequest", back_populates="project", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    position = Column(String, nullable=True) # Official title/position
    telegram_chat_id = Column(BigInteger, unique=True, nullable=True, index=True)
    status = Column(String, default="active", index=True) # active, blocked
    branch = Column(String, nullable=True) # Branch Name (e.g. "School", "Kindergarten")
    team = Column(String, nullable=True) # Team Name (e.g. "Admins")
    templates = Column(JSON, nullable=False, default=list) # Сверх тех что даёт проект
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    projects = relationship("Project", secondary=member_projects, back_populates="members")
    expenses = relationship("ExpenseRequest", back_populates="created_by_user")

class ExpenseRequest(Base):
    __tablename__ = "expense_requests"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    request_id = Column(String, unique=True, nullable=False, index=True) # e.g. TST-1
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    purpose = Column(String, nullable=False)
    items = Column(JSON, nullable=False) # List of ExpenseItem
    total_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, nullable=False) # UZS, USD, RUB
    status = Column(String, default="request", index=True) # request, review, pending_senior, approved_senior, rejected_senior, confirmed, declined, revision, archived
    request_type = Column(String, default="expense", index=True) # expense, refund, blank, blank_refund
    template_key = Column(String, nullable=True) # land, drujba, management, school, refund
    receipt_photo_file_id = Column(String, nullable=True) # Telegram file_id or local path
    refund_data = Column(JSON, nullable=True) # Additonal Refund specific fields
    
    created_by_id = Column(String, ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(String, nullable=False) # Denormalized Full Name
    created_by_position = Column(String, nullable=True) # Denormalized Position
    
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    project_name = Column(String, nullable=True) # Denormalized Project Name
    project_code = Column(String, nullable=True) # Denormalized Project Code
    
    internal_comment = Column(String, nullable=True)
    usd_rate = Column(Numeric(precision=18, scale=6), nullable=True)
    # Course USD/UZS at creation time. Null for UZS expenses.
    status_comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    project = relationship("Project", back_populates="expenses")
    created_by_user = relationship("TeamMember", back_populates="expenses")
    status_history = relationship("ExpenseStatusHistory", back_populates="expense", cascade="all, delete-orphan")

class ExpenseStatusHistory(Base):
    __tablename__ = "expense_status_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    expense_id = Column(String, ForeignKey("expense_requests.id", ondelete="CASCADE"), index=True)
    status = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    changed_by_id = Column(String, ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True)
    changed_by_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    expense = relationship("ExpenseRequest", back_populates="status_history")

class ProjectCounter(Base):
    __tablename__ = "project_counters"
    
    project_code = Column(String, primary_key=True)
    counter = Column(Integer, default=0)

class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
