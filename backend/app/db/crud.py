from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models, schemas
from app.core import auth
from decimal import Decimal

import datetime

# Tashkent timezone: UTC+5
TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

def tashkent_now() -> datetime.datetime:
    """Return current datetime in Tashkent time (UTC+5)."""
    return datetime.datetime.now(tz=TASHKENT_TZ)

# Atomic counter logic
def generate_request_id(db: Session, project_code: str):
    # Using a simple SELECT for update (PostgreSQL style recommended in plan)
    # For SQLite, it's naturally serial in a transaction
    counter_record = db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == project_code).with_for_update().first()
    
    if not counter_record:
        counter_record = models.ProjectCounter(project_code=project_code, counter=1)
        db.add(counter_record)
        next_val = 1
    else:
        counter_record.counter += 1
        next_val = counter_record.counter
        
    return f"{project_code}-{next_val}"

# Projects
def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(name=project.name, code=project.code, templates=project.templates)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # Initialize counter
    counter = models.ProjectCounter(project_code=project.code, counter=0)
    db.add(counter)
    db.commit()
    return db_project

def delete_project(db: Session, project_id: str):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        # Delete counter
        db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == project.code).delete()
        # Delete project (CASCADE will handle associations and expenses)
        db.delete(project)
        db.commit()
    return True

def add_project_member(db: Session, project_id: str, member_id: str):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if project and member:
        if project not in member.projects:
            member.projects.append(project)
            db.commit()
            db.refresh(member)
    return member

def remove_project_member(db: Session, project_id: str, member_id: str):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if project and member:
        if project in member.projects:
            member.projects.remove(project)
            db.commit()
            db.refresh(member)
    return member

# Team
def get_team(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TeamMember).offset(skip).limit(limit).all()

def create_team_member(db: Session, member: schemas.TeamMemberCreate):
    hashed_password = auth.get_password_hash(member.password)
    db_member = models.TeamMember(
        last_name=member.last_name,
        first_name=member.first_name,
        login=member.login,
        password_hash=hashed_password,
        position=member.position,
        status=member.status,
        branch=member.branch,
        team=member.team,
        templates=member.templates
    )
    
    # Add projects
    for project_id in member.project_ids:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            db_member.projects.append(project)
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def reactivate_team_member(db: Session, db_user: models.TeamMember, member: schemas.TeamMemberCreate):
    db_user.last_name = member.last_name
    db_user.first_name = member.first_name
    db_user.password_hash = auth.get_password_hash(member.password)
    db_user.position = member.position
    db_user.status = "active"
    db_user.branch = member.branch
    db_user.team = member.team
    db_user.templates = member.templates
    
    # Update projects
    db_user.projects.clear()
    for project_id in member.project_ids:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            db_user.projects.append(project)
            
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_team_member(db: Session, member_id: str):
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if member:
        db.delete(member)
        db.commit()
    return True

# Expenses
def get_expenses(db: Session, project_id: str = None, status: str = None, user_id: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.ExpenseRequest)
    if project_id:
        query = query.filter(models.ExpenseRequest.project_id == project_id)
    if user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)
    if status:
        statuses = [s.strip() for s in status.split(",")]
        if len(statuses) > 1:
            query = query.filter(models.ExpenseRequest.status.in_(statuses))
        else:
            query = query.filter(models.ExpenseRequest.status == status)
    return query.order_by(models.ExpenseRequest.date.desc()).offset(skip).limit(limit).all()

def count_expenses(
    db: Session,
    project_id: str = None,
    status: str = None,
    user_id: str = None
) -> int:
    """Считает количество заявок по тем же фильтрам что get_expenses."""
    query = db.query(models.ExpenseRequest)

    if user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)
    if project_id:
        query = query.filter(models.ExpenseRequest.project_id == project_id)
    if status:
        statuses = [s.strip() for s in status.split(",")]
        if len(statuses) > 1:
            query = query.filter(models.ExpenseRequest.status.in_(statuses))
        else:
            query = query.filter(models.ExpenseRequest.status == status)

    return query.count()

def create_expense_request(db: Session, expense: schemas.ExpenseRequestCreate, user_id: str, usd_rate: Decimal = None):
    if user_id == "admin":
        user_name = "Safina Admin"
        user_position = "Administrator"
    else:
        user = db.query(models.TeamMember).filter(models.TeamMember.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        user_name = f"{user.last_name} {user.first_name}".strip()
        if user_name.lower().startswith("user "):
            user_name = user_name[5:].strip()
        
        # Filter technical roles
        SYSTEM_ROLES = {"user", "admin", "senior_financier", "ceo"}
        raw_pos = user.position or ""
        user_position = raw_pos if raw_pos not in SYSTEM_ROLES else None
        
    project_id = expense.project_id if expense.project_id else None
    if project_id:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        project_name = project.name
        project_code = project.code
        req_prefix = project.code
    else:
        project = None
        project_name = None
        project_code = None
        req_prefix = "REF" if expense.request_type == "refund" else "REQ"
    
    request_id = generate_request_id(db, req_prefix)
    
    currency = expense.currency
    if currency is None and expense.items:
        currency = expense.items[0].currency
    elif currency is None:
        currency = "UZS"

    # Validation: all items must have the same currency as the request
    for item in expense.items:
        if item.currency != currency:
            raise ValueError(f"Item currency mismatch: expected {currency}, got {item.currency}")

    total_amount = expense.total_amount
    if total_amount is None:
        total_amount = sum(item.amount * item.quantity for item in expense.items)

    # Конвертируем Decimal в float для JSON совместимости
    items_serializable = []
    for item in expense.items:
        items_serializable.append({
            "name": item.name,
            "quantity": float(item.quantity),
            "amount": float(item.amount),
            "currency": str(getattr(item.currency, 'value', item.currency)),
        })

    db_expense = models.ExpenseRequest(
        request_id=request_id,
        date=expense.date or tashkent_now(),
        purpose=expense.purpose,
        items=items_serializable,
        total_amount=float(total_amount) if total_amount else 0,
        currency=currency,
        usd_rate=float(usd_rate) if (usd_rate and currency == "USD") else None,
        created_by_id=user_id if user_id != "admin" else None,
        created_by=user_name,
        created_by_position=user_position,
        project_id=project_id,
        project_name=project_name,
        project_code=project_code,
        request_type=expense.request_type,
        template_key=expense.template_key,
        receipt_photo_file_id=expense.receipt_photo_file_id,
        refund_data=expense.refund_data.dict() if expense.refund_data else None
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    # Initial status history
    history = models.ExpenseStatusHistory(
        expense_id=db_expense.id,
        status=db_expense.status,
        changed_by_id=user_id if user_id != "admin" else None,
        changed_by_name=user_name,
        comment="Создание заявки"
    )
    db.add(history)
    db.commit()
    
    return db_expense

def update_expense_status(db: Session, expense_id: str, update: schemas.ExpenseStatusUpdate, user_id: str = None, user_name: str = None):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if db_expense:
        old_status = db_expense.status
        new_status_str = update.status.value if hasattr(update.status, "value") else update.status
        db_expense.status = new_status_str
        if update.comment:
            db_expense.status_comment = update.comment
            
        # Record history
        history = models.ExpenseStatusHistory(
            expense_id=db_expense.id,
            status=new_status_str,
            comment=update.comment or f"Статус изменен с {old_status} на {new_status_str}",
            changed_by_id=user_id if user_id != "admin" else None,
            changed_by_name=user_name
        )
        db.add(history)
        
        db.commit()
        db.refresh(db_expense)
    return db_expense
