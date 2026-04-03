import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

from app.db import models
from app.services.analytics import export as export_service

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_generate_xlsx():
    db = SessionLocal()
    try:
        # Get up to 10 expenses
        expenses = db.query(models.ExpenseRequest).limit(10).all()
        print(f"Fetched {len(expenses)} expenses.")
        
        output = export_service.generate_expenses_xlsx(expenses)
        
        with open("test_report.xlsx", "wb") as f:
            f.write(output.getvalue())
            
        print("Successfully generated and saved test_report.xlsx")
    except Exception as e:
        print(f"FAILED to generate XLSX: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_generate_xlsx()
