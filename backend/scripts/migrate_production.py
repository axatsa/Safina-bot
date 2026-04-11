import sys
import os
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import uuid

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import auth, database
from app.db import models

def migrate():
    print("🚀 Starting Production Database Migration & Admin Setup...")
    
    # Get DB URL from environment or fallback
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set!")
        return
        
    engine = create_engine(db_url)
    
    # 1. Ensure Admin User exists in the NEW 'users' table
    print("  Ensuring Admin User exists...")
    db = Session(engine)
    try:
        admin_login = os.getenv("ADMIN_LOGIN", "safina")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        # We now query from models.User
        admin = db.query(models.User).filter(models.User.login == admin_login).first()
        hashed_password = auth.get_password_hash(admin_password)
        
        if not admin:
            print(f"    Creating admin user: {admin_login}...")
            new_admin = models.User(
                id=str(uuid.uuid4()),
                login=admin_login,
                password_hash=hashed_password,
                first_name="Admin",
                last_name="Safina",
                position="Administrator",
                role="admin",
                status="active",
                team="Администрация"
            )
            db.add(new_admin)
            print(f"    ✅ Admin user '{admin_login}' created.")
        else:
            print(f"    Admin user '{admin_login}' already exists. Updating credentials...")
            admin.password_hash = hashed_password
            admin.status = "active"
            admin.role = "admin"
            if not admin.team:
                admin.team = "Администрация"
            print(f"    ✅ Admin user '{admin_login}' updated.")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"    ❌ Error managing admin user: {e}")
    finally:
        db.close()

    print("\n✨ Migration script completed (Note: Core schema is handled by Alembic).")

if __name__ == "__main__":
    migrate()

if __name__ == "__main__":
    migrate()
