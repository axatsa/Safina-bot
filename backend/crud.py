from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas, auth
import datetime

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
        
    db.commit()
    db.refresh(counter_record)
    return f"{project_code}-{next_val}"

# Projects
def get_projects(db: Session):
    return db.query(models.Project).all()

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(name=project.name, code=project.code)
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
def get_team(db: Session):
    return db.query(models.TeamMember).all()

def create_team_member(db: Session, member: schemas.TeamMemberCreate):
    hashed_password = auth.get_password_hash(member.password)
    db_member = models.TeamMember(
        last_name=member.last_name,
        first_name=member.first_name,
        login=member.login,
        password_hash=hashed_password,
        position=member.position,
        status=member.status
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

def delete_team_member(db: Session, member_id: str):
    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if member:
        db.delete(member)
        db.commit()
    return True

# Expenses
def get_expenses(db: Session, project_id: str = None, status: str = None, user_id: str = None):
    query = db.query(models.ExpenseRequest)
    if project_id:
        query = query.filter(models.ExpenseRequest.project_id == project_id)
    if status:
        query = query.filter(models.ExpenseRequest.status == status)
    if user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)
    return query.all()

def create_expense_request(db: Session, expense: schemas.ExpenseRequestCreate, user_id: str):
    user = db.query(models.TeamMember).filter(models.TeamMember.id == user_id).first()
    if not user:
        raise ValueError("User not found")
        
    project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    request_id = generate_request_id(db, project.code)
    
    total_amount = expense.total_amount
    if total_amount is None:
        total_amount = sum(item.amount for item in expense.items)
    
    currency = expense.currency
    if currency is None and expense.items:
        currency = expense.items[0].currency
    elif currency is None:
        currency = "UZS"

    db_expense = models.ExpenseRequest(
        request_id=request_id,
        date=expense.date or datetime.datetime.utcnow(),
        purpose=expense.purpose,
        items=[item.dict() for item in expense.items],
        total_amount=total_amount,
        currency=currency,
        created_by_id=user_id,
        created_by=f"{user.last_name} {user.first_name}",
        created_by_position=user.position,
        project_id=expense.project_id,
        project_name=project.name,
        project_code=project.code
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense_status(db: Session, expense_id: str, update: schemas.ExpenseStatusUpdate):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if db_expense:
        db_expense.status = update.status
        if update.comment:
            db_expense.status_comment = update.comment
        db.commit()
        db.refresh(db_expense)
    return db_expense
