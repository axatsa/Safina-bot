from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, File, Form, UploadFile, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import re
import csv
import datetime
import os
import uuid
import shutil
from urllib.parse import quote
from app.db import models, schemas, crud
from app.core import auth, database
from app.core.logging_config import get_logger
from decimal import Decimal
from app.services.currency.service import currency_service
from app.services.docx.service import docx_service
from app.services.refund.service import (
    create_refund,
    save_receipt_photo,
    EXPORTABLE_STATUSES,
    EXCLUDED_FROM_EXPORT,
)
from app.services.bot.notifications import (
    send_status_notification,
    send_admin_notification,
    get_admin_chat_id,
    send_senior_notification,
    send_ceo_notification,
    get_ceo_chat_id,
)

logger = get_logger(__name__)


def get_expense_dict(expense) -> dict:
    return {
        'id': expense.id,
        'request_id': expense.request_id,
        'date': expense.date,
        'project_name': getattr(expense, 'project_name', None),
        'project_code': getattr(expense, 'project_code', None),
        'created_by': getattr(expense, 'created_by', None),
        'purpose': getattr(expense, 'purpose', None),
        'total_amount': getattr(expense, 'total_amount', 0),
        'currency': getattr(expense, 'currency', 'UZS'),
        'usd_rate': getattr(expense, 'usd_rate', None),
        'request_type': getattr(expense, 'request_type', 'expense'),
    }

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("", response_model=schemas.PaginatedExpensesSchema)
def read_expenses(
    project: str = None,
    status: str = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=5000),
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    user_id = None if auth.is_admin(current_user) else current_user.id
    items = crud.get_expenses(db, project_id=project, status=status, user_id=user_id, skip=skip, limit=limit)
    total = crud.count_expenses(db, project_id=project, status=status, user_id=user_id)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total
    }

@router.post("", response_model=schemas.ExpenseRequestSchema)
async def create_expense(expense: schemas.ExpenseRequestCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    user_id = getattr(current_user, "id", None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Admin cannot create expenses directly")
    
    usd_rate = await currency_service.get_usd_rate()
    expense_req = crud.create_expense_request(db=db, expense=expense, user_id=user_id, usd_rate=usd_rate)
    
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, get_expense_dict(expense_req), admin_chat_id)
    return expense_req

@router.post("/web-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_expense(
    data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    authorization: Optional[str] = Header(None)
):
    """Web-App endpoint: creates an investment request.
    Supports two auth methods:
    - JWT Bearer token (web dashboard)
    - chat_id in request body (Telegram Mini-App, no token needed)
    """
    user = None

    # 1. Try JWT auth
    if authorization and authorization.startswith("Bearer "):
        try:
            user = auth.get_current_user_from_token(authorization.replace("Bearer ", ""), db)
        except Exception:
            pass

    # 2. Fallback: chat_id from request body
    if user is None:
        chat_id = data.get("chat_id")
        if chat_id:
            try:
                chat_id_int = int(chat_id)
                user = db.query(models.TeamMember).filter(
                    models.TeamMember.telegram_chat_id == chat_id_int
                ).first()
            except (ValueError, TypeError):
                pass

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Не удалось определить пользователя. Войдите в систему или откройте через Telegram."
        )

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

    usd_rate = await currency_service.get_usd_rate()
    expense_req = crud.create_expense_request(db=db, expense=expense_create, user_id=user.id, usd_rate=usd_rate)

    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, get_expense_dict(expense_req), admin_chat_id)
    return expense_req


@router.post("/refund/web-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_refund(
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    student_id: str = Form(...),
    reason: str = Form(...),
    amount: float = Form(...),
    card_number: str = Form(...),
    retention: str = Form("false"),
    chat_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    """Web-App endpoint: создаёт заявку возврата.
    Поддерживает два способа авторизации:
    - JWT Bearer токен (веб-дашборд)
    - chat_id (Telegram Mini-App, без токена)
    """
    user = None

    # 1. Попытка авторизации через JWT
    if authorization and authorization.startswith("Bearer "):
        try:
            user = auth.get_current_user_from_token(authorization.replace("Bearer ", ""), db)
        except Exception:
            pass

    # 2. Fallback: авторизация через Telegram chat_id
    if user is None and chat_id:
        try:
            chat_id_int = int(chat_id)
            user = db.query(models.TeamMember).filter(
                models.TeamMember.telegram_chat_id == chat_id_int
            ).first()
        except (ValueError, TypeError):
            pass

    if user is None:
        raise HTTPException(status_code=401, detail="Не удалось определить пользователя. Войдите в систему или откройте через Telegram.")

    retention_bool = retention.lower() == "true"

    try:
        expense_req = await create_refund(
            db,
            student_id=student_id,
            reason=reason,
            amount=amount,
            card_number=card_number,
            retention=retention_bool,
            user_id=user.id,
            branch=user.branch,
            team=user.team,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, get_expense_dict(expense_req), admin_chat_id)
    return expense_req

@router.post("/blank-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_blank(
    data: dict, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(database.get_db), 
    authorization: Optional[str] = Header(None)
):
    """Web-App endpoint: создаёт заявку-бланк (служебную записку)."""
    user = None
    if authorization and authorization.startswith("Bearer "):
        try:
            user = auth.get_current_user_from_token(authorization.replace("Bearer ", ""), db)
        except Exception:
            pass

    chat_id = data.get("chat_id")
    if user is None and chat_id:
        try:
            chat_id_int = int(chat_id)
            user = db.query(models.TeamMember).filter(
                models.TeamMember.telegram_chat_id == chat_id_int
            ).first()
        except (ValueError, TypeError):
            pass

    if user is None:
        raise HTTPException(status_code=401, detail="Не удалось определить пользователя. Войдите в систему или откройте через Telegram.")
    current_user = user
    # Validation
    tpl = data.get("template")
    if not tpl:
        raise HTTPException(status_code=400, detail="Template is required")
        
    items_data = []
    for item in data.get("items", []):
        items_data.append(schemas.ExpenseItemSchema(
            name=item.get("name"),
            quantity=item.get("qty", 1),
            amount=item.get("amount", 0),
            currency=item.get("currency", "UZS")
        ))
    
    purpose = data.get("purpose", f"Бланк: {tpl}")
    
    expense_create = schemas.ExpenseRequestCreate(
        project_id=data.get("project_id"),
        purpose=purpose,
        items=items_data,
        currency=items_data[0].currency if items_data else "UZS"
    )
    
    usd_rate = await currency_service.get_usd_rate()
    expense_req = crud.create_expense_request(
        db=db, 
        expense=expense_create, 
        user_id=current_user.id, 
        usd_rate=usd_rate
    )
    
    expense_req.request_type = "blank"
    expense_req.template_key = tpl
    db.commit()
    db.refresh(expense_req)
    
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, get_expense_dict(expense_req), admin_chat_id)
        
    return expense_req

@router.post("/refund-application-submit", response_model=schemas.ExpenseRequestSchema)
async def web_submit_refund_application(
    data: dict, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(database.get_db), 
    authorization: Optional[str] = Header(None)
):
    """Web-App endpoint: создаёт заявку на возврат клиента (blank_refund)."""
    user = None
    if authorization and authorization.startswith("Bearer "):
        try:
            user = auth.get_current_user_from_token(authorization.replace("Bearer ", ""), db)
        except Exception:
            pass

    chat_id = data.get("chat_id")
    if user is None and chat_id:
        try:
            chat_id_int = int(chat_id)
            user = db.query(models.TeamMember).filter(
                models.TeamMember.telegram_chat_id == chat_id_int
            ).first()
        except (ValueError, TypeError):
            pass

    if user is None:
        raise HTTPException(status_code=401, detail="Не удалось определить пользователя. Войдите в систему или откройте через Telegram.")
    current_user = user

    purpose = f"Возврат: {data.get('client_name')} ({data.get('contract_number', 'б/н')})"
    amount = float(data.get("amount", 0))
    
    expense_create = schemas.ExpenseRequestCreate(
        project_id=data.get("project_id"),
        purpose=purpose,
        items=[],
        currency="UZS"
    )
    
    usd_rate = await currency_service.get_usd_rate()
    expense_req = crud.create_expense_request(
        db=db, 
        expense=expense_create, 
        user_id=current_user.id, 
        usd_rate=usd_rate
    )
    
    expense_req.request_type = "blank_refund"
    expense_req.template_key = "refund"
    expense_req.total_amount = amount
    expense_req.refund_data = data
    db.commit()
    db.refresh(expense_req)
    
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        background_tasks.add_task(send_admin_notification, get_expense_dict(expense_req), admin_chat_id)
        
    return expense_req




@router.get("/refund/{expense_id}/export-application-docx")
def export_refund_application(
    expense_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user),
):
    """Скачать заявление на возврат (шаблон для школьного филиала)."""
    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if expense.request_type != "refund":
        raise HTTPException(status_code=400, detail="Только для заявок типа 'refund'")

    rd = expense.refund_data or {}
    fname = f"заявление_{expense.request_id}.docx"
    try:
        stream = docx_service.generate_expense_docx(expense)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    encoded_filename = quote(fname)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"},
    )

@router.patch("/{expense_id}/refund-confirm", response_model=schemas.ExpenseRequestSchema)
async def confirm_refund_with_receipt(
    expense_id: str,
    retention: str = Form(...),           # "true" or "false"
    receipt_photo: UploadFile = File(...),
    recipient_ids: Optional[str] = Form(None), # JSON list of user IDs
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Safina attaches receipt photo and sets retention flag on a refund request."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admin can confirm refunds")

    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.request_type not in ("refund", "blank_refund"):
        raise HTTPException(status_code=400, detail="This endpoint is only for refund requests")

    # Save photo
    receipt_path = save_receipt_photo(receipt_photo)
    expense.receipt_photo_file_id = receipt_path

    # Update retention in refund_data JSON
    retention_bool = retention.lower() == "true"
    refund_data = expense.refund_data or {}
    refund_data["retention"] = retention_bool
    expense.refund_data = refund_data

    # Mark as confirmed
    expense.status = "confirmed"
    db.commit()
    db.refresh(expense)

    # Send notifications if recipients selected
    if recipient_ids:
        try:
            import json
            ids_list = json.loads(recipient_ids)
            if ids_list:
                # Resolve chat IDs
                recipients = db.query(models.TeamMember).filter(
                    models.TeamMember.id.in_(ids_list),
                    models.TeamMember.telegram_chat_id.isnot(None)
                ).all()
                chat_ids = [r.telegram_chat_id for r in recipients]
                
                if chat_ids:
                    from app.services.bot.notifications import send_refund_receipt_notification
                    initiator_name = expense.created_by or "Неизвестный"
                    background_tasks.add_task(
                        send_refund_receipt_notification,
                        chat_ids=chat_ids,
                        request_id=expense.request_id,
                        amount=float(expense.total_amount),
                        currency=expense.currency,
                        photo_path=receipt_path,
                        initiator_name=initiator_name
                    )
        except Exception as e:
            logger.error(f"Error processing refund notification recipients: {e}")

    return expense

ALLOWED_TRANSITIONS = {
    "pending_senior": ["request", "review", "revision"],
    "approved_senior": ["pending_senior"],
    "rejected_senior": ["pending_senior"],
    "pending_ceo": ["approved_senior", "pending_senior"],
    "approved_ceo": ["pending_ceo"],
    "rejected_ceo": ["pending_ceo"],
    "confirmed": ["approved_ceo", "approved_senior", "review", "request"],
    "declined": ["request", "review", "pending_senior", "pending_ceo"],
    "revision": ["request", "review", "pending_senior", "pending_ceo"],
    "review": ["request", "revision"],
    "archived": ["confirmed", "declined"]
}

def validate_transition(current_status: str, new_status: str) -> bool:
    if new_status not in ALLOWED_TRANSITIONS:
        return True
    allowed = ALLOWED_TRANSITIONS.get(new_status, [])
    return current_status in allowed

@router.patch("/{expense_id}/status", response_model=schemas.ExpenseRequestSchema)
def update_status(expense_id: str, update: schemas.ExpenseStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    if not validate_transition(db_expense.status, update.status):
        raise HTTPException(status_code=400, detail=f"Нельзя перевести в {update.status} из статуса {db_expense.status}")

    if update.status in ["declined", "revision"] and not update.comment:
        raise HTTPException(status_code=400, detail="Comment is required for declined or revision status")
    
    user_name = f"{current_user.last_name} {current_user.first_name}"
    expense = crud.update_expense_status(db, expense_id, update, user_id=current_user.id, user_name=user_name)
    
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

@router.get("/{expense_id}/history", response_model=List[schemas.ExpenseStatusHistorySchema])
def read_expense_history(expense_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense.status_history

@router.post("/{expense_id}/forward_senior", response_model=schemas.ExpenseRequestSchema)
def forward_to_senior_financier(
    expense_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user),
):
    """Forward an expense to the CFO (Senior Financier). Only Safina admin can do this."""
    is_admin = auth.is_admin(current_user)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can forward to the Senior Financier")

    update = schemas.ExpenseStatusUpdate(
        status="pending_senior",
        comment="Отправлено на согласование Старшему финансисту (CFO)",
    )
    user_name = f"{current_user.last_name} {current_user.first_name}"
    expense = crud.update_expense_status(db, expense_id, update, user_id=current_user.id, user_name=user_name)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    from app.services.bot.notifications import get_senior_financier_chat_ids
    logger.info(f"Forwarding expense {expense.request_id} (status: {expense.status}) to Senior Financier")
    senior_chat_ids = get_senior_financier_chat_ids()
    if senior_chat_ids:
        for chat_id in senior_chat_ids:
            background_tasks.add_task(send_senior_notification, get_expense_dict(expense), chat_id)
    else:
        logger.warning(f"No linked Senior Financiers (CFO) found for expense {expense.request_id}")

    from app.services.notifications.sse import publish_notification
    background_tasks.add_task(
        publish_notification,
        "notifications:admin",
        {"title": "Статус обновлен", "message": f"Заявка {expense.request_id} отправлена CFO."},
    )
    return expense


@router.post("/{expense_id}/forward_ceo", response_model=schemas.ExpenseRequestSchema)
def forward_to_ceo(
    expense_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user),
):
    """Forward an expense to the CEO. Only CFO (senior_financier) or Admin can do this."""
    if not auth.is_admin(current_user) and current_user.position != "senior_financier":
        raise HTTPException(status_code=403, detail="Only the CFO or Admin can forward to CEO")

    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")


    update = schemas.ExpenseStatusUpdate(
        status="pending_ceo",
        comment="Отправлено на финальное согласование CEO",
    )
    user_name = f"{current_user.last_name} {current_user.first_name}"
    expense = crud.update_expense_status(db, expense_id, update, user_id=current_user.id, user_name=user_name)

    logger.info(f"Forwarding expense {expense.request_id} (status: {expense.status}) to CEO")
    ceo_chat_id = get_ceo_chat_id()
    if ceo_chat_id:
        background_tasks.add_task(send_ceo_notification, get_expense_dict(expense), ceo_chat_id)
    else:
        logger.warning("CEO has not linked their Telegram account yet.")

    from app.services.notifications.sse import publish_notification
    background_tasks.add_task(
        publish_notification,
        "notifications:senior",
        {"title": "Статус обновлен", "message": f"Заявка {expense.request_id} отправлена CEO."},
    )
    return expense


@router.put("/{expense_id}/comment")
def update_internal_comment(expense_id: str, update: schemas.InternalCommentUpdate, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    db_expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db_expense.internal_comment = update.internal_comment
    db.commit()
    return {"status": "success"}

@router.get("/export")
def export_expenses(project: str = None, user_id: str = None, from_date: str = None, to_date: str = None, allStatuses: bool = False, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    query = db.query(models.ExpenseRequest)
    
    # Ограничение по пользователю
    is_admin = auth.is_admin(current_user)
    if not is_admin:
        query = query.filter(models.ExpenseRequest.created_by_id == current_user.id)
    elif user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)

    if project:
        query = query.filter(models.ExpenseRequest.project_id == project)

    # Фильтр статусов: pending_* и archived никогда не попадают в экспорт
    if allStatuses:
        query = query.filter(~models.ExpenseRequest.status.in_(list(EXCLUDED_FROM_EXPORT)))
    else:
        query = query.filter(models.ExpenseRequest.status.in_(EXPORTABLE_STATUSES))
    
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
    writer.writerow(["Request ID", "Date", "Project Code", "Project Name", "Responsible", "Status", "Item Name", "Qty", "Amount", "Currency", "USD Rate", "Amount in UZS"])
    
    status_map = {
        "request": "Запрос",
        "review": "На рассмотрении",
        "pending_senior": "На согласовании CFO",
        "approved_senior": "Утверждено CFO",
        "pending_ceo": "На согласовании CEO",
        "approved_ceo": "Одобрено CEO",
        "confirmed": "Подтверждено",
        "declined": "Отклонено",
        "revision": "Возврат на доработку",
        "archived": "Архивировано"
    }

    for e in expenses:
        usd_rate = Decimal(str(e.usd_rate)) if e.usd_rate else None
        items = e.items if isinstance(e.items, list) else []
        for item in items:
            item_currency = item.get("currency", e.currency)
            item_amount_native = Decimal(str(item.get("amount", 0))) * Decimal(str(item.get("quantity", 0)))
            
            amount_uzs = item_amount_native
            if item_currency == "USD" and usd_rate:
                amount_uzs = item_amount_native * usd_rate
            elif item_currency == "RUB" and usd_rate: # Assuming RUB to UZS conversion via USD rate if available
                amount_uzs = item_amount_native / Decimal("100") * usd_rate # Example conversion, adjust as needed

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
                item_currency,
                float(usd_rate) if usd_rate else "",
                float(round(amount_uzs, 2))
            ])
    
    content = output.getvalue()
    bom = "\ufeff"
    filename = "expenses_export.csv"
    encoded_filename = quote(filename)
    return Response(
        content=bom + content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )

@router.get("/export-xlsx")
def export_expenses_xlsx(project: str = None, user_id: str = None, from_date: str = None, to_date: str = None, allStatuses: bool = False, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    from app.services.analytics import export as export_service
    
    query = db.query(models.ExpenseRequest)
    
    is_admin = auth.is_admin(current_user)
    if not is_admin:
        query = query.filter(models.ExpenseRequest.created_by_id == current_user.id)
    elif user_id:
        query = query.filter(models.ExpenseRequest.created_by_id == user_id)

    if project:
        query = query.filter(models.ExpenseRequest.project_id == project)

    # Фильтр статусов: pending_* и archived никогда не попадают в экспорт
    if allStatuses:
        query = query.filter(~models.ExpenseRequest.status.in_(list(EXCLUDED_FROM_EXPORT)))
    else:
        query = query.filter(models.ExpenseRequest.status.in_(EXPORTABLE_STATUSES))
    
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
    output = export_service.generate_expenses_xlsx(expenses)
    
    filename = f"expenses_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/{expense_id}/export-docx")
def export_expense_docx(expense_id: str, db: Session = Depends(database.get_db), current_user: models.TeamMember = Depends(auth.get_current_user)):
    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    try:
        file_stream = docx_service.generate_expense_docx(expense)
        filename = f"smeta_{expense.request_id}.docx"
        encoded_filename = quote(filename)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{expense_id}/export-blank-docx")
def export_blank_docx(
    expense_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    """Экспорт бланка в DOCX. Доступ только для админов, CFO и CEO."""
    # RBAC Check
    if not auth.is_admin(current_user) and current_user.position not in ["senior_financier", "ceo"]:
        raise HTTPException(status_code=403, detail="У вас нет прав для скачивания этого документа")

    expense = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    # Check if it's a blank or refund
    if expense.request_type not in ["blank", "blank_refund", "refund"]:
        raise HTTPException(status_code=400, detail="Этот документ не является бланком")

    try:
        file_stream = docx_service.generate_expense_docx(expense)
        # Choose filename based on template or request_id
        tpl_label = expense.template_key.upper() if expense.template_key else "BLANK"
        filename = f"{tpl_label}_{expense.request_id}.docx"
        encoded_filename = quote(filename)
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating blank DOCX: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при генерации документа")

@router.get("/{expense_id}", response_model=schemas.ExpenseRequestSchema)
def read_expense_by_id(
    expense_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    expense = db.query(models.ExpenseRequest).filter(
        models.ExpenseRequest.id == expense_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if not auth.is_admin(current_user) and expense.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return expense
