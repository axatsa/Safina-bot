from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
import csv
import datetime
import os
from app.db import models, schemas, crud
from app.core import auth, database
from app.services.docx.generator import generate_docx
from app.services.bot.notifications import send_status_notification, send_admin_notification, get_admin_chat_id

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("", response_model=List[schemas.ExpenseRequestSchema])
def read_expenses(project: str = None, status: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    user_id = None if current_user.login == os.getenv("ADMIN_LOGIN", "safina") else current_user.id
    return crud.get_expenses(db, project_id=project, status=status, user_id=user_id, skip=skip, limit=limit)

@router.post("", response_model=schemas.ExpenseRequestSchema)
def create_expense(expense: schemas.ExpenseRequestCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    user_id = getattr(current_user, "id", None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Admin cannot create expenses directly")
    expense_req = crud.create_expense_request(db=db, expense=expense, user_id=user_id)
    
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, expense_req.id, admin_chat_id)
    return expense_req

@router.post("/web-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_expense(data: dict, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    chat_id = data.get("chat_id")
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    try:
        chat_id_int = int(chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    user = db.query(models.TeamMember).filter(models.TeamMember.telegram_chat_id == chat_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for this telegram account")
    
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
    
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, expense_req.id, admin_chat_id)
    return expense_req

@router.patch("/{expense_id}/status", response_model=schemas.ExpenseRequestSchema)
def update_status(expense_id: str, update: schemas.ExpenseStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    if update.status in ["declined", "revision"] and not update.comment:
        raise HTTPException(status_code=400, detail="Comment is required for declined or revision status")
    
    expense = crud.update_expense_status(db, expense_id, update)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.created_by_user and expense.created_by_user.telegram_chat_id:
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

@router.put("/{expense_id}/comment")
def update_internal_comment(expense_id: str, update: schemas.InternalCommentUpdate, db: Session = Depends(database.get_db)):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db_expense.internal_comment = update.internal_comment
    db.commit()
    return {"status": "success"}

@router.get("/export")
def export_expenses(project: str = None, user_id: str = None, from_date: str = None, to_date: str = None, allStatuses: bool = False, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    query = db.query(models.ExpenseRequest)
    
    # Restrict non-admins to only view their own expenses
    is_admin = current_user.login == os.getenv("ADMIN_LOGIN", "safina")
    if not is_admin:
        query = query.filter(models.ExpenseRequest.created_by_id == current_user.id)
    elif user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)

    if project:
        query = query.filter(models.ExpenseRequest.project_id == project)
    if not allStatuses:
        query = query.filter(models.ExpenseRequest.status == "confirmed")
    
    if from_date:
        try:
            from_dt = datetime.datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date >= from_dt)
        except ValueError:
            pass
    if to_date:
        try:
            if len(to_date) <= 10:
                to_dt = datetime.datetime.fromisoformat(to_date) + datetime.timedelta(days=1)
            else:
                to_dt = datetime.datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date <= to_dt)
        except ValueError:
            pass
        
    expenses = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Request ID", "Date", "Project Code", "Project Name", "Responsible", "Status", "Item Name", "Qty", "Amount", "Currency", "Total Amount"])
    
    status_map = {
        "request": "Запрос",
        "review": "На рассмотрении",
        "confirmed": "Подтверждено",
        "declined": "Отклонено",
        "revision": "Возврат на доработку",
        "archived": "Архивировано"
    }

    for e in expenses:
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
    bom = "\ufeff"
    return Response(
        content=bom + content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=expenses_export.csv"}
    )

@router.get("/export-xlsx")
def export_expenses_xlsx(project: str = None, user_id: str = None, from_date: str = None, to_date: str = None, allStatuses: bool = False, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    import pandas as pd
    
    query = db.query(models.ExpenseRequest)
    
    # Restrict non-admins to only view their own expenses
    is_admin = current_user.login == os.getenv("ADMIN_LOGIN", "safina")
    if not is_admin:
        query = query.filter(models.ExpenseRequest.created_by_id == current_user.id)
    elif user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)

    if project:
        query = query.filter(models.ExpenseRequest.project_id == project)
    if not allStatuses:
        query = query.filter(models.ExpenseRequest.status == "confirmed")
    
    if from_date:
        try:
            from_dt = datetime.datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date >= from_dt)
        except ValueError:
            pass
    if to_date:
        try:
            if len(to_date) <= 10:
                to_dt = datetime.datetime.fromisoformat(to_date) + datetime.timedelta(days=1)
            else:
                to_dt = datetime.datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query = query.filter(models.ExpenseRequest.date <= to_dt)
        except ValueError:
            pass
        
    expenses = query.all()
    
    data = []
    status_map = {
        "request": "Запрос",
        "review": "На рассмотрении",
        "confirmed": "Подтверждено",
        "declined": "Отклонено",
        "revision": "Возврат на доработку",
        "archived": "Архивировано"
    }

    for e in expenses:
        items = e.items if isinstance(e.items, list) else []
        for item in items:
            data.append({
                "ID Запроса": e.request_id,
                "Дата": e.date.strftime("%d.%m.%Y %H:%M"),
                "Код проекта": e.project_code,
                "Название проекта": e.project_name,
                "Ответственный": e.created_by,
                "Статус": status_map.get(e.status, e.status),
                "Наименование": item.get("name", ""),
                "Кол-во": item.get("quantity", 0),
                "Сумма": item.get("amount", 0),
                "Валюта": item.get("currency", e.currency),
                "Общая сумма": float(e.total_amount)
            })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
        
        # Auto-adjust columns width
        worksheet = writer.sheets['Expenses']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=expenses_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )


@router.get("/{expense_id}/export-docx")
def export_expense_docx(expense_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # Prepare items, ensuring they are a list of dicts and adding line totals
    items_data = []
    raw_items = expense.items
    if isinstance(raw_items, str):
        import json
        try:
            raw_items = json.loads(raw_items)
        except:
            raw_items = []
            
    if isinstance(raw_items, list):
        for idx, item in enumerate(raw_items):
            if isinstance(item, dict):
                # We need to be defensive here to avoid 500 errors if some keys are missing
                try:
                    qty = float(item.get("quantity", 0))
                    price = float(item.get("amount", 0))
                    items_data.append({
                        "no": idx + 1,
                        "name": item.get("name", "Без названия"),
                        "quantity": qty,
                        "price": price,
                        "total": qty * price
                    })
                except (ValueError, TypeError):
                    continue

    data = {
        "sender_name": expense.created_by,
        "sender_position": expense.created_by_position or "Сотрудник",
        "purpose": expense.purpose,
        "items": items_data,
        "total_amount": float(expense.total_amount),
        "currency": expense.currency,
        "request_id": expense.request_id,
        "date": expense.date
    }
    
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services/docx/template.docx")
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
