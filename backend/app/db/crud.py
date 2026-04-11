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
def get_projects(db: Session, skip: int = 0, limit: int = 100, category: str = None):
    query = db.query(models.Project)
    if category:
        query = query.filter(models.Project.category == category)
    return query.offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name, 
        code=project.code.upper(), 
        category=project.category,
        templates=project.templates
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # Initialize counter for standard requests
    counter = models.ProjectCounter(project_code=db_project.code, counter=0)
    db.add(counter)
    # Initialize counter for refunds
    refund_counter = models.ProjectCounter(project_code=f"{db_project.code}-REF", counter=0)
    db.add(refund_counter)
    db.commit()
    return db_project

def delete_project(db: Session, project_id: str):
    print(f"DEBUG: Deleting project {project_id}")
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        # Delete counters for project
        db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == project.code).delete()
        db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{project.code}-REF").delete()
        
        # Delete counters for branches
        for branch in project.branches:
            db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == branch.code).delete()
            db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{branch.code}-REF").delete()
            
        db.delete(project)
        db.commit()
        return True
    return False

# Branches
def get_branches(db: Session, project_id: str = None):
    query = db.query(models.Branch)
    if project_id:
        query = query.filter(models.Branch.project_id == project_id)
    return query.all()

def create_branch(db: Session, project_id: str, branch: schemas.BranchCreate):
    print(f"DEBUG: Creating branch '{branch.name}' for project {project_id}")
    # Auto-generate unique code from name if possible, or use name-slug
    import re
    base_code = re.sub(r'[^A-Z0-9]', '', branch.name.upper())[:10]
    if not base_code: base_code = "BRN"
    
    # Ensure uniqueness across both Branch and ProjectCounter tables
    code = base_code
    suffix = 1
    while (db.query(models.Branch).filter(models.Branch.code == code).first() or 
           db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == code).first()):
        code = f"{base_code}{suffix}"
        suffix += 1
        
    db_branch = models.Branch(
        name=branch.name,
        code=code,
        project_id=project_id
    )
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    
    # Initialize counters for branch - handle potential existing counters gracefully
    try:
        if not db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == code).first():
            db.add(models.ProjectCounter(project_code=code, counter=0))
        if not db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{code}-REF").first():
            db.add(models.ProjectCounter(project_code=f"{code}-REF", counter=0))
        db.commit()
    except Exception as e:
        print(f"DEBUG: Counter initialization warning: {e}")
        db.rollback()
        # Non-fatal: generate_request_id will create them if needed later
    
    return db_branch

def delete_branch(db: Session, branch_id: str):
    print(f"DEBUG: Deleting branch {branch_id}")
    branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
    if branch:
        db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == branch.code).delete()
        db.query(models.ProjectCounter).filter(models.ProjectCounter.project_code == f"{branch.code}-REF").delete()
        db.delete(branch)
        db.commit()
        print(f"DEBUG: Branch {branch_id} deleted successfully")
        return True
    print(f"DEBUG: Branch {branch_id} not found")
    return False

def add_project_member(db: Session, project_id: str, member_id: str):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if project and member:
        if project not in member.projects:
            member.projects.append(project)
            db.commit()
            db.refresh(project)
    return project

def remove_project_member(db: Session, project_id: str, member_id: str):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if project and member:
        if project in member.projects:
            member.projects.remove(project)
            db.commit()
            db.refresh(project)
    return project

def update_project_templates(db: Session, project_id: str, templates: list):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        project.templates = templates
        db.commit()
        db.refresh(project)
    return project

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
        team=member.team,
        templates=member.templates
    )
    
    # Add projects
    if member.project_ids:
        for project_id in member.project_ids:
            project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if project:
                db_member.projects.append(project)
    
    # Add branches
    if member.branch_ids:
        for branch_id in member.branch_ids:
            branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
            if branch:
                db_member.branches.append(branch)
                
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def update_team_member(db: Session, member_id: str, update: schemas.TeamMemberUpdate):
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not member:
        return None
    if update.last_name is not None: member.last_name = update.last_name
    if update.first_name is not None: member.first_name = update.first_name
    if update.position is not None: member.position = update.position
    if update.team is not None: member.team = update.team
    if update.login is not None: member.login = update.login
    if update.password is not None: member.password_hash = auth.get_password_hash(update.password)
    if update.templates is not None: member.templates = update.templates
    
    if update.project_ids is not None:
        member.projects.clear()
        for project_id in update.project_ids:
            project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if project:
                member.projects.append(project)
                
    if update.branch_ids is not None:
        member.branches.clear()
        for branch_id in update.branch_ids:
            branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
            if branch:
                member.branches.append(branch)
                
    db.commit()
    db.refresh(member)
    return member

# Expenses
def get_expenses(
    db: Session, 
    project_id: str = None, 
    branch_id: str = None,
    status: str = None, 
    user_id: str = None, 
    request_type: str = None,
    branch_name: str = None, # legacy filter by name
    team: str = None,
    search: str = None,
    from_date: datetime.datetime = None,
    to_date: datetime.datetime = None,
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(models.ExpenseRequest)
    
    if branch_id:
        query = query.filter(models.ExpenseRequest.branch_id == branch_id)
    elif branch_name:
        # Compatibility with old string-based branch filter
        query = query.join(models.TeamMember, models.ExpenseRequest.created_by_id == models.TeamMember.id)
        query = query.filter(models.TeamMember.branch == branch_name)
        
    if team:
        if not branch_name and not branch_id:
            query = query.join(models.TeamMember, models.ExpenseRequest.created_by_id == models.TeamMember.id)
        query = query.filter(models.TeamMember.team == team)
            
    if user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)
    if project_id:
        query = query.filter(models.ExpenseRequest.project_id == project_id)
        
    if request_type:
        types = [t.strip() for t in request_type.split(",")]
        query = query.filter(models.ExpenseRequest.request_type.in_(types))

    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.filter(models.ExpenseRequest.status.in_(statuses))

    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(
            (models.ExpenseRequest.request_id.ilike(search_lower)) |
            (models.ExpenseRequest.purpose.ilike(search_lower))
        )

    if from_date: query.filter(models.ExpenseRequest.date >= from_date)
    if to_date: query.filter(models.ExpenseRequest.date <= to_date)
            
    return query.order_by(models.ExpenseRequest.date.desc()).offset(skip).limit(limit).all()

def count_expenses(db: Session, **kwargs) -> int:
    # Simplified count reusing filter logic could be added here, but for brevity:
    # (In real implementation, we'd refactor get_expenses to return query)
    return len(get_expenses(db, limit=1000000, **kwargs))

def create_expense_request(db: Session, expense: schemas.ExpenseRequestCreate, user_id: str, usd_rate: Decimal = None):
    user = None
    if user_id != "admin":
        user = db.query(models.TeamMember).filter(models.TeamMember.id == user_id).first()
        if not user: raise ValueError("User not found")
        user_name = f"{user.last_name} {user.first_name}".strip()
        SYSTEM_ROLES = {"user", "admin", "senior_financier", "ceo"}
        user_position = user.position if user.position not in SYSTEM_ROLES else None
    else:
        user_name, user_position = "Safina Admin", "Administrator"
        
    project_id = expense.project_id
    branch_id = expense.branch_id
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first() if project_id else None
    branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first() if branch_id else None
    
    # Prefix logic: Branch code > Project code > Default
    base_prefix = "REQ"
    if branch:
        base_prefix = branch.code
    elif project:
        base_prefix = project.code
    elif expense.request_type == "refund":
        base_prefix = "REF"

    # Separate counter for refunds as requested ("все отдельно")
    is_refund = expense.request_type in ["refund", "blank_refund"]
    request_prefix = f"{base_prefix}-REF" if is_refund else base_prefix
    
    request_id = generate_request_id(db, request_prefix)
    
    db_expense = models.ExpenseRequest(
        request_id=request_id,
        date=expense.date or tashkent_now(),
        purpose=expense.purpose,
        items=[{
            "name": i.name, "quantity": float(i.quantity), 
            "amount": float(i.amount), "currency": str(i.currency)
        } for i in expense.items],
        total_amount=float(expense.total_amount or sum(i.amount * i.quantity for i in expense.items)),
        currency=expense.currency or (expense.items[0].currency if expense.items else "UZS"),
        usd_rate=float(usd_rate) if (usd_rate and expense.currency == "USD") else None,
        created_by_id=user_id if user_id != "admin" else None,
        created_by=user_name,
        created_by_position=user_position,
        project_id=project_id,
        project_name=project.name if project else None,
        project_code=project.code if project else None,
        branch_id=branch_id,
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
        request_type=expense.request_type,
        template_key=expense.template_key,
        receipt_photo_file_id=expense.receipt_photo_file_id,
        refund_data=expense.refund_data.dict() if expense.refund_data else None
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    db.add(models.ExpenseStatusHistory(
        expense_id=db_expense.id, status=db_expense.status,
        changed_by_id=user_id if user_id != "admin" else None,
        changed_by_name=user_name, comment="Создание заявки"
    ))
    db.commit()
    return db_expense

def update_expense_status(db: Session, expense_id: str, update: schemas.ExpenseStatusUpdate, user_id: str = None, user_name: str = None):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if db_expense:
        old_status = db_expense.status
        new_status = update.status.value if hasattr(update.status, "value") else update.status
        db_expense.status = new_status
        if update.comment: db_expense.status_comment = update.comment
            
        db.add(models.ExpenseStatusHistory(
            expense_id=db_expense.id, status=new_status,
            comment=update.comment or f"Статус изменен с {old_status} на {new_status}",
            changed_by_id=user_id if user_id != "admin" else None,
            changed_by_name=user_name
        ))
        db.commit()
        db.refresh(db_expense)
    return db_expense
