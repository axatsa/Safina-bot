import database
from sqlalchemy import text

db = next(database.get_db())

alters = [
    "ALTER TABLE team_members DROP CONSTRAINT IF EXISTS team_members_project_id_fkey;",
    "ALTER TABLE team_members DROP COLUMN IF EXISTS project_id;",
    "ALTER TABLE member_projects DROP CONSTRAINT IF EXISTS member_projects_project_id_fkey;",
    "ALTER TABLE member_projects ADD CONSTRAINT member_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;",
    "ALTER TABLE member_projects DROP CONSTRAINT IF EXISTS member_projects_member_id_fkey;",
    "ALTER TABLE member_projects ADD CONSTRAINT member_projects_member_id_fkey FOREIGN KEY (member_id) REFERENCES team_members(id) ON DELETE CASCADE;",
    "ALTER TABLE expense_requests DROP CONSTRAINT IF EXISTS expense_requests_project_id_fkey;",
    "ALTER TABLE expense_requests ADD CONSTRAINT expense_requests_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;",
    "ALTER TABLE expense_requests DROP CONSTRAINT IF EXISTS expense_requests_created_by_id_fkey;",
    "ALTER TABLE expense_requests ADD CONSTRAINT expense_requests_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES team_members(id) ON DELETE SET NULL;"
]

for cmd in alters:
    try:
        db.execute(text(cmd))
    except Exception as e:
        print("Error:", e)
        db.rollback()

db.commit()
print("Cascade migration completed!")
