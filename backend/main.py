from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io
import csv

import models, schemas, crud, auth, database
from database import engine, get_db
from bot.notifications import send_status_notification

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Safina API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(request: schemas.TokenData, db: Session = Depends(get_db)):
    # Simple hardcoded admin for now as per README
    # In production, we'd check team_members table
    if request.login == "safina" and request.password == "admin123":
        access_token = auth.create_access_token(data={"sub": request.login})
        return {"access_token": access_token, "token_type": "bearer", "role": "admin"}
    
    # Check team members
    user = db.query(models.TeamMember).filter(models.TeamMember.login == request.login).first()
    if user and auth.verify_password(request.password, user.password_hash):
        access_token = auth.create_access_token(data={"sub": user.login})
        return {"access_token": access_token, "token_type": "bearer", "role": "user", "projectId": user.project_id}
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/api/projects", response_model=List[schemas.ProjectSchema])
def read_projects(db: Session = Depends(get_db)):
    return crud.get_projects(db)

@app.post("/api/projects", response_model=schemas.ProjectSchema)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db, project)

@app.get("/api/team", response_model=List[schemas.TeamMemberSchema])
def read_team(db: Session = Depends(get_db)):
    return crud.get_team(db)

@app.post("/api/team", response_model=schemas.TeamMemberSchema)
def create_member(member: schemas.TeamMemberCreate, db: Session = Depends(get_db)):
    return crud.create_team_member(db, member)

@app.get("/api/expenses", response_model=List[schemas.ExpenseRequestSchema])
def read_expenses(project: str = None, status: str = None, db: Session = Depends(get_db)):
    return crud.get_expenses(db, project_id=project, status=status)

@app.patch("/api/expenses/{expense_id}/status", response_model=schemas.ExpenseRequestSchema)
def update_status(expense_id: str, update: schemas.ExpenseStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # validation: declined/revision must have comment
    if update.status in ["declined", "revision"] and not update.comment:
        raise HTTPException(status_code=400, detail="Comment is required for declined or revision status")
    
    expense = crud.update_expense_status(db, expense_id, update)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Trigger Telegram notification
    if expense.created_by_user.telegram_chat_id:
        background_tasks.add_task(
            send_status_notification,
            expense.created_by_user.telegram_chat_id,
            expense.request_id,
            update.status,
            expense.total_amount,
            expense.currency,
            update.comment
        )
    
    return expense

@app.put("/api/expenses/{expense_id}/comment")
def update_internal_comment(expense_id: str, update: schemas.InternalCommentUpdate, db: Session = Depends(get_db)):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db_expense.internal_comment = update.internal_comment
    db.commit()
    return {"status": "success"}

@app.get("/api/expenses/export")
def export_expenses(project: str = None, from_date: str = None, to_date: str = None, allStatuses: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.ExpenseRequest)
    if project:
        query = query.filter(models.ExpenseRequest.project_id == project)
    if not allStatuses:
        query = query.filter(models.ExpenseRequest.status == "confirmed")
    
    # Date filtering logic
    if from_date:
        query = query.filter(models.ExpenseRequest.date >= datetime.datetime.fromisoformat(from_date))
    if to_date:
        query = query.filter(models.ExpenseRequest.date <= datetime.datetime.fromisoformat(to_date))
        
    expenses = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Project", "Purpose", "Amount", "Currency", "Status", "Responsible"])
    
    for e in expenses:
        writer.writerow([
            e.request_id,
            e.date.strftime("%Y-%m-%d %H:%M"),
            e.project_name,
            e.purpose,
            e.total_amount,
            e.currency,
            e.status,
            e.created_by
        ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=expenses_export.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
