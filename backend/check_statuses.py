
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_statuses():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT status, count(*) FROM expense_requests GROUP BY status")).all()
        print("Status counts:")
        for status, count in result:
            print(f"{status}: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    check_statuses()
