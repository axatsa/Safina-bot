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
    print("🚀 Starting Production Database Migration...")
    
    # Get DB URL from environment or fallback
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set!")
        return
        
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # 1. Add 'category' to 'projects'
        print("  Checking 'projects' table...")
        try:
            conn.execute(text("ALTER TABLE projects ADD COLUMN category VARCHAR DEFAULT 'startup'"))
            conn.execute(text("CREATE INDEX ix_projects_category ON projects (category)"))
            conn.commit()
            print("    ✅ Column 'category' added to 'projects'.")
        except Exception as e:
            conn.rollback()
            if "already exists" in str(e):
                print("    ℹ️ Column 'category' already exists in 'projects'.")
            else:
                print(f"    ❌ Error adding 'category': {e}")

        # 2. Create 'branches' table
        print("  Checking 'branches' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS branches (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    code VARCHAR NOT NULL UNIQUE,
                    project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_code ON branches (code)"))
            conn.commit()
            print("    ✅ Table 'branches' created.")
        except Exception as e:
            conn.rollback()
            print(f"    ❌ Error creating 'branches': {e}")

        # 3. Create 'member_branches' table
        print("  Checking 'member_branches' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS member_branches (
                    member_id VARCHAR NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
                    branch_id VARCHAR NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                    PRIMARY KEY (member_id, branch_id)
                )
            """))
            conn.commit()
            print("    ✅ Table 'member_branches' created.")
        except Exception as e:
            conn.rollback()
            print(f"    ❌ Error creating 'member_branches': {e}")

        # 4. Add branch columns to 'expense_requests'
        print("  Checking 'expense_requests' table...")
        cols_to_add = [
            ("branch_id", "VARCHAR REFERENCES branches(id) ON DELETE SET NULL"),
            ("branch_name", "VARCHAR"),
            ("branch_code", "VARCHAR")
        ]
        for col, col_type in cols_to_add:
            try:
                conn.execute(text(f"ALTER TABLE expense_requests ADD COLUMN {col} {col_type}"))
                conn.commit()
                print(f"    ✅ Column '{col}' added to 'expense_requests'.")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e):
                    print(f"    ℹ️ Column '{col}' already exists.")
                else:
                    print(f"    ❌ Error adding '{col}': {e}")
        
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_expense_requests_branch_id ON expense_requests (branch_id)"))
            conn.commit()
        except:
            conn.rollback()

    # 5. Restore Admin User
    print("  Ensuring Admin User exists...")
    db = Session(engine)
    try:
        admin_login = os.getenv("ADMIN_LOGIN", "safina")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        admin = db.query(models.TeamMember).filter(models.TeamMember.login == admin_login).first()
        hashed_password = auth.get_password_hash(admin_password)
        
        if not admin:
            print(f"    Creating admin user: {admin_login}...")
            new_admin = models.TeamMember(
                id=str(uuid.uuid4()),
                login=admin_login,
                password_hash=hashed_password,
                first_name="Admin",
                last_name="Safina",
                position="admin",
                status="active",
                team="Финансисты"
            )
            db.add(new_admin)
            print(f"    ✅ Admin user '{admin_login}' created.")
        else:
            print(f"    Admin user '{admin_login}' already exists. Updating password and permissions...")
            admin.password_hash = hashed_password
            admin.status = "active"
            admin.position = "admin"
            admin.team = "Финансисты"
            print(f"    ✅ Admin user '{admin_login}' updated.")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"    ❌ Error managing admin user: {e}")
    finally:
        db.close()

    print("\n✨ Migration complete!")

if __name__ == "__main__":
    migrate()
