from sqlalchemy.orm import Session
from app.db.repository.expense_repository import expense_repository, tashkent_now
from app.db.repository.project_repository import project_repository
from app.db.repository.branch_repository import branch_repository
from app.db.models import ExpenseRequest, User, Project, Branch
from app.db.schemas import ExpenseRequestCreate, ExpenseStatusUpdate
from typing import Optional, List
from decimal import Decimal
from fastapi import HTTPException

class ExpenseService:
    def create_expense_request(
        self, 
        db: Session, 
        expense_in: ExpenseRequestCreate, 
        user_id: str, 
        usd_rate: Optional[Decimal] = None
    ) -> ExpenseRequest:
        # Get user info for denormalization
        if user_id == "admin":
            user_name, user_position = "Safina Admin", "Administrator"
            db_user_id = None
        else:
            user = db.query(User).get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_name = f"{user.last_name} {user.first_name}".strip()
            user_position = user.position
            db_user_id = user.id

        # Get project/branch info
        project = project_repository.get(db, id=expense_in.project_id) if expense_in.project_id else None
        branch = branch_repository.get(db, id=expense_in.branch_id) if expense_in.branch_id else None

        # Prefix logic
        base_prefix = "REQ"
        if branch:
            base_prefix = branch.code
        elif project:
            base_prefix = project.code
        elif expense_in.request_type == "refund":
            base_prefix = "REF"

        is_refund = expense_in.request_type in ["refund", "blank_refund"]
        request_prefix = f"{base_prefix}-REF" if is_refund else base_prefix
        
        request_id = expense_repository.generate_request_id(db, request_prefix)

        db_expense = ExpenseRequest(
            request_id=request_id,
            date=expense_in.date or tashkent_now(),
            purpose=expense_in.purpose,
            items=[{
                "name": i.name, "quantity": float(i.quantity), 
                "amount": float(i.amount), "currency": str(i.currency)
            } for i in expense_in.items],
            total_amount=float(expense_in.total_amount or sum(i.amount * i.quantity for i in expense_in.items)),
            currency=expense_in.currency or (expense_in.items[0].currency if expense_in.items else "UZS"),
            usd_rate=float(usd_rate) if (usd_rate and expense_in.currency == "USD") else None,
            created_by_id=db_user_id,
            created_by=user_name,
            created_by_position=user_position,
            project_id=project.id if project else None,
            project_name=project.name if project else None,
            project_code=project.code if project else None,
            branch_id=branch.id if branch else None,
            branch_name=branch.name if branch else None,
            branch_code=branch.code if branch else None,
            request_type=expense_in.request_type,
            template_key=expense_in.template_key,
            receipt_photo_file_id=expense_in.receipt_photo_file_id,
            refund_data=expense_in.refund_data.dict() if expense_in.refund_data else None
        )
        
        return expense_repository.create_with_history(
            db, obj_in=db_expense, user_id=db_user_id, user_name=user_name
        )

    def update_status(
        self, 
        db: Session, 
        expense_id: str, 
        update_in: ExpenseStatusUpdate, 
        user_id: Optional[str] = None, 
        user_name: Optional[str] = None
    ) -> ExpenseRequest:
        expense = expense_repository.get(db, id=expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense request not found")
            
        return expense_repository.update_status(
            db, 
            db_obj=expense, 
            new_status=update_in.status, 
            comment=update_in.comment,
            user_id=user_id,
            user_name=user_name
        )

    def get_expense_dict(self, expense: ExpenseRequest) -> dict:
        """Denormalize expense request for notifications or external APIs."""
        return {
            'id': expense.id,
            'request_id': expense.request_id,
            'date': expense.date,
            'project_name': getattr(expense, 'project_name', None),
            'project_code': getattr(expense, 'project_code', None),
            'branch_name': getattr(expense, 'branch_name', None),
            'branch_code': getattr(expense, 'branch_code', None),
            'created_by': getattr(expense, 'created_by', None),
            'purpose': getattr(expense, 'purpose', None),
            'total_amount': getattr(expense, 'total_amount', 0),
            'currency': getattr(expense, 'currency', 'UZS'),
            'usd_rate': getattr(expense, 'usd_rate', None),
            'request_type': getattr(expense, 'request_type', 'expense'),
        }

expense_service = ExpenseService()
