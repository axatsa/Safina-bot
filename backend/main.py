from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io
import csv
import datetime
import os

import models, schemas, crud, auth, database
from database import engine, get_db
from bot.notifications import send_status_notification, send_admin_notification, get_admin_chat_id
from docx_generator import generate_docx

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
        # Use first project ID as default for frontend
        project_id = user.projects[0].id if user.projects else None
        return {"access_token": access_token, "token_type": "bearer", "role": "user", "projectId": project_id}
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/api/projects", response_model=List[schemas.ProjectSchema])
def read_projects(db: Session = Depends(get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    # Simplistic admin check: only 'safina' login has full access
    if current_user.login == "safina":
        return crud.get_projects(db)
    
    return current_user.projects

@app.get("/api/projects/by-chat-id/{chat_id}", response_model=List[schemas.ProjectSchema])
def read_projects_by_chat_id(chat_id: int, db: Session = Depends(get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == chat_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.projects

@app.post("/api/projects", response_model=schemas.ProjectSchema)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can create projects")
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

@app.post("/api/projects/{project_id}/members/{member_id}")
def add_project_member(project_id: str, member_id: str, db: Session = Depends(get_db)):
    member = crud.add_project_member(db, project_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return {"status": "success"}

@app.delete("/api/projects/{project_id}/members/{member_id}")
def remove_project_member(project_id: str, member_id: str, db: Session = Depends(get_db)):
    member = crud.remove_project_member(db, project_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project or Member not found")
    return {"status": "success"}

@app.get("/api/team", response_model=List[schemas.TeamMemberSchema])
def read_team(db: Session = Depends(get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    if current_user.login != "safina":
        raise HTTPException(status_code=403, detail="Only admins can view the team list")
    return crud.get_team(db)

@app.post("/api/team", response_model=schemas.TeamMemberSchema)
def create_team_member(member: schemas.TeamMemberCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.TeamMember).filter(models.TeamMember.login == member.login).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    return crud.create_team_member(db=db, member=member)

@app.post("/api/expenses", response_model=schemas.ExpenseRequestSchema)
def create_expense(expense: schemas.ExpenseRequestCreate, db: Session = Depends(get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    user_id = getattr(current_user, "id", None)
    if not user_id:
        # If admin doesn't have ID, maybe they shouldn't create expenses or we find/temp ID
        # For now, let's assume admins who create expenses are NOT virtual (rare case)
        # or we throw error
        raise HTTPException(status_code=400, detail="Admin cannot create expenses directly")
    expense_req = crud.create_expense_request(db=db, expense=expense, user_id=user_id)
    
    # Notify Admin
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, expense_req, admin_chat_id)
        
    return expense_req

@app.post("/api/expenses/web-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_expense(data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
        items.append(schemas.ExpenseItemSchema(
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
    
    expense_req = crud.create_expense_request(db=db, expense=expense_create, user_id=user.id)
    
    # Notify Admin
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, expense_req, admin_chat_id)
    
    return expense_req

@app.delete("/api/team/{member_id}")
def delete_team_member(member_id: str, db: Session = Depends(get_db)):
    user = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(user)
    db.commit()
    return {"status": "success"}

@app.get("/api/expenses", response_model=List[schemas.ExpenseRequestSchema])
def read_expenses(project: str = None, status: str = None, db: Session = Depends(get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    user_id = None if current_user.login == "safina" else current_user.id
    return crud.get_expenses(db, project_id=project, status=status, user_id=user_id)

# Removed duplicate create_expense endpoint

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
            expense.status,
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
    # ... existing CSV export ...
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
    
    # Status mapping for CSV
    status_map = {
        "request": "Запрос",
        "review": "На рассмотрении",
        "confirmed": "Подтверждено",
        "declined": "Отклонено",
        "revision": "Возврат на доработку",
        "archived": "Архивировано"
    }

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
                status_map.get(e.status, e.status),
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

@app.get("/api/expenses/{expense_id}/export-docx")
def export_expense_docx(expense_id: str, db: Session = Depends(get_db)):
    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # Prepare data for template
    data = {
        "sender_name": expense.created_by,
        "sender_position": expense.created_by_position or "",
        "purpose": expense.purpose,
        "items": expense.items,
        "total_amount": float(expense.total_amount),
        "currency": expense.currency,
        "request_id": expense.request_id,
        "date": expense.date.strftime("%d.%m.%Y")
    }
    
    template_path = os.path.join(os.path.dirname(__file__), "template.docx")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="Template file not found")
        
    try:
        file_stream = generate_docx(template_path, data)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=smeta_{expense.request_id}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
