import sys
import os

# Add the project root directory to sys.path so we can import from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.db.seed import seed_users
from sqlalchemy import text

def reset_db():
    print("🚀 Starting database cleanup for production...")
    db = SessionLocal()
    try:
        # 1. Clear transaction data
        print("  Cleaning transaction data...")
        db.query(models.ExpenseStatusHistory).delete()
        db.query(models.ExpenseRequest).delete()
        db.query(models.ProjectCounter).delete()
        
        # 2. Clear project data
        print("  Cleaning project data...")
        # Since user_projects is an association table, we handle it via raw SQL if needed.
        db.execute(text("DELETE FROM user_projects"))
        db.query(models.Project).delete()
        
        # 3. Clear non-essential users
        print("  Cleaning users...")
        # We keep users defined in seed.py and the main admin from .env
        admin_login = os.getenv("ADMIN_LOGIN", "safina")
        essential_logins = ["farrukh", "ganiev", "financier", "abd", admin_login]
        
        db.query(models.User).filter(models.User.login.notin_(essential_logins)).delete()
        
        db.commit()
        print("✅ Data cleared successfully.")
        
        # 4. Re-run seed to ensure essential users are present and have correct data
        print("  Ensuring essential users exist...")
        seed_users()
        print("✅ Essential users verified.")
        
        print("\n✨ Database is now ready for production use!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    # Check if user really wants to do this
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        reset_db()
    else:
        confirm = input("⚠️ WARNING: This will delete ALL test data (expenses, projects, members). Continue? (y/n): ")
        if confirm.lower() == 'y':
            reset_db()
        else:
            print("Aborted.")
