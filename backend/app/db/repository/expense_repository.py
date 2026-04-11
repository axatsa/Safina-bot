from typing import List, Optional, Union, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.repository.base import BaseRepository
from app.db.models import ExpenseRequest, ProjectCounter, ExpenseStatusHistory, User
from app.db.schemas import ExpenseRequestCreate, ExpenseStatusEnum
import datetime

# Tashkent timezone
TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

def tashkent_now() -> datetime.datetime:
    return datetime.datetime.now(tz=TASHKENT_TZ)

class ExpenseRepository(BaseRepository[ExpenseRequest, ExpenseRequestCreate, Any]):
    def generate_request_id(self, db: Session, project_code: str) -> str:
        counter_record = (
            db.query(ProjectCounter)
            .filter(ProjectCounter.project_code == project_code)
            .with_for_update()
            .first()
        )
        
        if not counter_record:
            counter_record = ProjectCounter(project_code=project_code, counter=1)
            db.add(counter_record)
            next_val = 1
        else:
            counter_record.counter += 1
            next_val = counter_record.counter
            
        return f"{project_code}-{next_val}"

    def get_multi_filtered(
        self, 
        db: Session, 
        *, 
        project_id: Optional[str] = None, 
        branch_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        request_type: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExpenseRequest]:
        query = db.query(ExpenseRequest)
        
        if project_id:
            query = query.filter(ExpenseRequest.project_id == project_id)
        if branch_id:
            query = query.filter(ExpenseRequest.branch_id == branch_id)
        if user_id:
            query = query.filter(ExpenseRequest.created_by_id == user_id)
        if status:
            statuses = [s.strip() for s in status.split(",")]
            query = query.filter(ExpenseRequest.status.in_(statuses))
        if request_type:
            types = [t.strip() for t in request_type.split(",")]
            query = query.filter(ExpenseRequest.request_type.in_(types))
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                (ExpenseRequest.request_id.ilike(search_lower)) |
                (ExpenseRequest.purpose.ilike(search_lower))
            )
        if from_date:
            query = query.filter(ExpenseRequest.date >= from_date)
        if to_date:
            query = query.filter(ExpenseRequest.date <= to_date)
            
        return query.order_by(ExpenseRequest.date.desc()).offset(skip).limit(limit).all()

    def count_filtered(self, db: Session, **kwargs) -> int:
        # Avoid full list retrieval for counting
        query = db.query(func.count(ExpenseRequest.id))
        
        if kwargs.get("project_id"):
            query = query.filter(ExpenseRequest.project_id == kwargs["project_id"])
        if kwargs.get("branch_id"):
            query = query.filter(ExpenseRequest.branch_id == kwargs["branch_id"])
        if kwargs.get("user_id"):
            query = query.filter(ExpenseRequest.created_by_id == kwargs["user_id"])
        if kwargs.get("status"):
            statuses = [s.strip() for s in kwargs["status"].split(",")]
            query = query.filter(ExpenseRequest.status.in_(statuses))
        if kwargs.get("request_type"):
            types = [t.strip() for t in kwargs["request_type"].split(",")]
            query = query.filter(ExpenseRequest.request_type.in_(types))
        if kwargs.get("search"):
            search_lower = f"%{kwargs['search'].lower()}%"
            query = query.filter(
                (ExpenseRequest.request_id.ilike(search_lower)) |
                (ExpenseRequest.purpose.ilike(search_lower))
            )
        if kwargs.get("from_date"):
            query = query.filter(ExpenseRequest.date >= kwargs["from_date"])
        if kwargs.get("to_date"):
            query = query.filter(ExpenseRequest.date <= kwargs["to_date"])
            
        return query.scalar()

    def create_with_history(
        self, 
        db: Session, 
        *, 
        obj_in: ExpenseRequest, 
        user_id: Optional[str] = None, 
        user_name: Optional[str] = None
    ) -> ExpenseRequest:
        db.add(obj_in)
        db.commit()
        db.refresh(obj_in)
        
        # Add initial status history
        history = ExpenseStatusHistory(
            expense_id=obj_in.id,
            status=obj_in.status,
            changed_by_id=user_id,
            changed_by_name=user_name,
            comment="Создание заявки"
        )
        db.add(history)
        db.commit()
        return obj_in

    def update_status(
        self, 
        db: Session, 
        *, 
        db_obj: ExpenseRequest, 
        new_status: str, 
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> ExpenseRequest:
        old_status = db_obj.status
        db_obj.status = new_status
        if comment:
            db_obj.status_comment = comment
            
        history = ExpenseStatusHistory(
            expense_id=db_obj.id,
            status=new_status,
            comment=comment or f"Статус изменен с {old_status} на {new_status}",
            changed_by_id=user_id,
            changed_by_name=user_name
        )
        db.add(history)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

expense_repository = ExpenseRepository(ExpenseRequest)
