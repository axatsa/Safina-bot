
import os
import io
import datetime
from decimal import Decimal
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

from app.db import models, crud
from app.services.analytics import export as export_service

# Use a temporary SQLite database for testing if possible, 
# but here we'll just use the existing one and look for specific data.
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_enhanced_export():
    db = SessionLocal()
    try:
        print("--- Testing CRUD Filtering ---")
        # 1. Test filtering by request_type
        refunds = crud.get_expenses(db, request_type="refund", limit=5)
        print(f"Found {len(refunds)} refunds via request_type='refund'")
        for r in refunds:
            assert r.request_type == "refund"

        # 2. Test filtering by branch (if any exist)
        all_expenses = db.query(models.ExpenseRequest).limit(50).all()
        branches = set()
        for e in all_expenses:
            user = db.query(models.TeamMember).filter(models.TeamMember.id == e.created_by_id).first()
            if user and user.branch:
                branches.add(user.branch)
        
        if branches:
            branch_to_test = list(branches)[0]
            branch_expenses = crud.get_expenses(db, branch=branch_to_test, limit=10)
            print(f"Found {len(branch_expenses)} expenses for branch '{branch_to_test}'")
            for e in branch_expenses:
                user = db.query(models.TeamMember).filter(models.TeamMember.id == e.created_by_id).first()
                assert user.branch == branch_to_test
        else:
            print("No branches found in existing data to test branch filter.")

        print("\n--- Testing XLSX Generation with Refund Data ---")
        # Fetch some refunds specifically to test the new columns
        refund_requests = db.query(models.ExpenseRequest).filter(models.ExpenseRequest.request_type == "refund").limit(5).all()
        if not refund_requests:
            print("No refunds found in DB. Please run populate_test_data.py first.")
            return

        # Generate XLSX
        output = export_service.generate_expenses_xlsx(refund_requests)
        
        # Verify content using pandas
        output.seek(0)
        df = pd.read_excel(output)
        
        print(f"Generated DataFrame columns: {df.columns.tolist()}")
        
        expected_columns = [
            "ID Ученика", "ФИО Клиента", "Телефон", "Паспорт", 
            "Контракт", "Причина", "Номер карты", "Банк"
        ]
        
        for col in expected_columns:
            if col in df.columns:
                print(f"Column '{col}' is present.")
            else:
                print(f"MISSING column '{col}'!")
        
        # Check if first row has data in these columns
        if not df.empty:
            print(f"Sample row (ID Ученика): {df.iloc[0].get('ID Ученика')}")
            print(f"Sample row (ФИО Клиента): {df.iloc[0].get('ФИО Клиента')}")

        print("\nVerification SUCCESSFUL!")

    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_enhanced_export()
