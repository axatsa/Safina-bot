from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, JSON, BigInteger
from sqlalchemy.orm import relationship
from database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    members = relationship("TeamMember", back_populates="project")
    expenses = relationship("ExpenseRequest", back_populates="project")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"))
    login = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    telegram_chat_id = Column(BigInteger, nullable=True)
    status = Column(String, default="active") # active, blocked
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    project = relationship("Project", back_populates="members")
    expenses = relationship("ExpenseRequest", back_populates="created_by_user")

class ExpenseRequest(Base):
    __tablename__ = "expense_requests"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    request_id = Column(String, unique=True, nullable=False) # e.g. TST-1
    date = Column(DateTime, default=datetime.datetime.utcnow)
    purpose = Column(String, nullable=False)
    items = Column(JSON, nullable=False) # List of ExpenseItem
    total_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, nullable=False) # UZS, USD, RUB
    status = Column(String, default="request") # request, review, confirmed, declined, revision, archived
    
    created_by_id = Column(String, ForeignKey("team_members.id"))
    created_by = Column(String, nullable=False) # Denormalized Full Name
    
    project_id = Column(String, ForeignKey("projects.id"))
    project_name = Column(String, nullable=False) # Denormalized Project Name
    project_code = Column(String, nullable=False) # Denormalized Project Code
    
    internal_comment = Column(String, nullable=True)
    status_comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    project = relationship("Project", back_populates="expenses")
    created_by_user = relationship("TeamMember", back_populates="expenses")

class ProjectCounter(Base):
    __tablename__ = "project_counters"
    
    project_code = Column(String, primary_key=True)
    counter = Column(Integer, default=0)
