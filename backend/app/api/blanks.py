from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import datetime
import os
import io

from app.db import models, schemas
from app.core import auth, database
from app.services.docx.service import docx_service

router = APIRouter(prefix="/blanks", tags=["blanks"])

class BlankItemSchema(BaseModel):
    name: str
    qty: float
    amount: float
    currency: str

class BlankGenerateRequest(BaseModel):
    template: str # land, ls, management, school, refund
    sender_name: Optional[str] = None
    sender_position: Optional[str] = None
    purpose: Optional[str] = None
    items: Optional[List[BlankItemSchema]] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    date: Optional[str] = None
    
    # Refund specific fields
    client_name: Optional[str] = None
    passport_series: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issued_by: Optional[str] = None
    passport_date: Optional[str] = None
    phone: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    reason: Optional[str] = None
    reason_other: Optional[str] = None
    amount: Optional[float] = None
    amount_words: Optional[str] = None
    card_holder: Optional[str] = None
    card_number: Optional[str] = None
    transit_account: Optional[str] = None
    bank_iin: Optional[str] = None
    bank_mfo: Optional[str] = None
    bank_name: Optional[str] = None

@router.post("/generate")
async def generate_blank(
    request: BlankGenerateRequest,
    current_user: models.TeamMember = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Generate a DOCX blank based on the provided template and data.
    """
    # 1. Determine template path
    template_name_map = {
        "land": "LAND.docx",
        "ls": "School.docx", # LS uses School template per common practice in this bot, or we can use a dedicated one if it exists
        "management": "Management.docx",
        "school": "School.docx",
        "refund": "Заявление_на_возврат_денег.docx"
    }
    
    if request.template not in template_name_map:
        raise HTTPException(status_code=400, detail=f"Unsupported template type: {request.template}")
    
    template_filename = template_name_map[request.template]
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "docx", "templates")
    template_path = os.path.join(templates_dir, template_filename)
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail=f"Template file not found: {template_filename}")

    # 2. Prepare data for docxtpl
    # Prefill some data from current_user if not provided
    data = request.dict(exclude_unset=True)
    if not data.get("sender_name"):
        data["sender_name"] = f"{current_user.last_name} {current_user.first_name}"
    if not data.get("sender_position"):
        data["sender_position"] = current_user.position or "Сотрудник"
    if not data.get("date"):
        data["date"] = datetime.datetime.now().strftime("%d.%m.%Y")
    
    # Special handling for short name
    full_name = data.get("sender_name", "")
    parts = full_name.split()
    if len(parts) >= 2:
        data["sender_name_short"] = f"{parts[0]} {parts[1][0]}."
    else:
        data["sender_name_short"] = full_name

    # Checkboxes for refund reason
    if request.template == "refund":
        reasons = {
            "Переезд": "reason_pereezd",
            "Изменение графика": "reason_grafik",
            "Несоответствие": "reason_ozhidaniy",
            "Материальные трудности": "reason_trudnosti",
            "По личным причинам": "reason_lichnye",
            "Другое": "reason_drugoe"
        }
        for res_text, res_key in reasons.items():
            data[res_key] = "☑" if request.reason == res_text else "□"
        
        if request.reason == "Другое":
            data["reason_drugoe_text"] = request.reason_other
        else:
            data["reason_drugoe_text"] = ""

    # 3. Generate DOCX
    from app.services.docx.generator import generate_docx
    try:
        stream = generate_docx(template_path, data)
        fname = f"blank_{request.template}_{datetime.datetime.now().strftime('%d%m%Y')}.docx"
        
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={fname}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
