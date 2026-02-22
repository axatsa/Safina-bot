from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io
import csv
import datetime
import os

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
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Use environment variables for admin login for safety
    admin_login = os.getenv("ADMIN_LOGIN", "safina")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if request.login == admin_login and request.password == admin_password:
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
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db)):
    return crud.create_project(db=db, project=project)

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(database.get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    # Also delete associations
    db.delete(proj)
    db.commit()
    return {"status": "success"}

@app.get("/api/team", response_model=List[schemas.TeamMemberSchema])
def read_team(db: Session = Depends(get_db)):
    return crud.get_team(db)

@app.post("/api/expenses", response_model=schemas.ExpenseRequestSchema)
def create_expense(expense: schemas.ExpenseRequestCreate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    return crud.create_expense_request(db=db, expense=expense, user_id=current_user.id)

@app.post("/api/expenses/web-submit", response_model=schemas.ExpenseRequestSchema)
def web_submit_expense(data: dict, db: Session = Depends(database.get_db)):
    chat_id = data.get("chat_id")
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    # Simple integer check if it comes as string
    try:
        chat_id_int = int(chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == chat_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for this telegram account")
    
    # Map raw data to ExpenseRequestCreate
    items = []
    for item in data.get("items", []):
        items.append(schemas.ExpenseItem(
            name=item.get("name"),
            quantity=item.get("quantity"),
            amount=item.get("amount"),
            currency=item.get("currency")
        ))
    
    expense_create = schemas.ExpenseRequestCreate(
        project_id=data.get("project_id"),
        purpose=data.get("purpose"),
        items=items,
        currency=items[0].currency if items else "UZS"
    )
    
    return crud.create_expense_request(db=db, expense=expense_create, user_id=user.id)

@app.delete("/api/team/{member_id}")
def delete_team_member(member_id: str, db: Session = Depends(database.get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(user)
    db.commit()
    return {"status": "success"}

@app.get("/api/expenses", response_model=List[schemas.ExpenseRequestSchema])
def read_expenses(project: str = None, status: str = None, db: Session = Depends(get_db)):
    # Note: In a real app, we would get the current user from the token here
    # and restrict 'project' if they are a regular user.
    # For now, we allow filtering, but logic is ready for integration.
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
    
    # Date filtering logic with robust parsing
    if from_date:
        try:
            from_dt = datetime.datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date >= from_dt)
        except ValueError:
            pass # Or handle error
    if to_date:
        try:
            # For to_date, we often want the very end of the day if just a date is provided
            if len(to_date) <= 10: # YYYY-MM-DD
                to_dt = datetime.datetime.fromisoformat(to_date) + datetime.timedelta(days=1)
            else:
                to_dt = datetime.datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date <= to_dt)
        except ValueError:
            pass
        
    expenses = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    # New headers as per requirements
    writer.writerow(["Request ID", "Date", "Project Code", "Project Name", "Responsible", "Status", "Item Name", "Qty", "Amount", "Currency", "Total Amount"])
    
    for e in expenses:
        # Each expense can have multiple items, we export each as a separate row
        items = e.items if isinstance(e.items, list) else []
        for item in items:
            writer.writerow([
                e.request_id,
                e.date.strftime("%Y-%m-%d %H:%M"),
                e.project_code,
                e.project_name,
                e.created_by,
                e.status,
                item.get("name", ""),
                item.get("quantity", 0),
                item.get("amount", 0),
                item.get("currency", e.currency),
                e.total_amount
            ])
    
    content = output.getvalue()
    # UTF-8 with BOM for Excel compatibility
    bom = "\ufeff"
    return Response(
        content=bom + content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=expenses_export.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
