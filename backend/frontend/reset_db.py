import sqlite3
import os

db_path = "backend/media/safina.db"

def reset_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Deleting garbage data...")
        
        # Tables to clear entirely
        tables_to_clear = [
            "expense_requests",
            "projects",
            "member_projects",
            "project_counters"
        ]

        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  Cleared table: {table}")

        # Clear team members except administrative ones
        # We assume farrukh and ganiev are in the DB and we want to keep them.
        # We also keep the admin login if it exists.
        cursor.execute("DELETE FROM team_members WHERE login NOT IN ('safina', 'farrukh', 'ganiev')")
        print("  Cleared non-admin team members.")

        conn.commit()
        print("Database cleanup successful.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_db()
