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

# Team
def get_team(db: Session):
    return db.query(models.TeamMember).all()

def create_team_member(db: Session, member: schemas.TeamMemberCreate):
    hashed_password = auth.get_password_hash(member.password)
    db_member = models.TeamMember(
        last_name=member.last_name,
        first_name=member.first_name,
        project_id=member.project_id,
        login=member.login,
        password_hash=hashed_password,
        status=member.status
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

# Expenses
def get_expenses(db: Session, project_id: str = None, status: str = None):
    query = db.query(models.ExpenseRequest)
    if project_id:
        query = query.filter(models.ExpenseRequest.project_id == project_id)
    if status:
        query = query.filter(models.ExpenseRequest.status == status)
    return query.all()

def create_expense_request(db: Session, expense: schemas.ExpenseRequestCreate, user_id: str):
    user = db.query(models.TeamMember).filter(models.TeamMember.id == user_id).first()
    project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
    
    request_id = generate_request_id(db, project.code)
    
    db_expense = models.ExpenseRequest(
        request_id=request_id,
        date=expense.date or datetime.datetime.utcnow(),
        purpose=expense.purpose,
        items=[item.dict() for item in expense.items],
        total_amount=expense.total_amount,
        currency=expense.currency,
        created_by_id=user_id,
        created_by=f"{user.last_name} {user.first_name}",
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
