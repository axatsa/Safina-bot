import database, models
from sqlalchemy import text

db = next(database.get_db())

# Add new columns manually

try:
    db.execute(text("ALTER TABLE team_members ADD COLUMN position VARCHAR;"))
except Exception as e:
    print(e)
    db.rollback()

try:
    db.execute(text("ALTER TABLE team_members ADD COLUMN telegram_chat_id BIGINT UNIQUE;"))
except Exception as e:
    print(e)
    db.rollback()

try:
    db.execute(text("ALTER TABLE expense_requests ADD COLUMN created_by_position VARCHAR;"))
except Exception as e:
    print(e)
    db.rollback()

try:
    db.execute(text("ALTER TABLE expense_requests ADD COLUMN created_at TIMESTAMP;"))
except Exception as e:
    print(e)
    db.rollback()

try:
    db.execute(text("ALTER TABLE expense_requests ADD COLUMN internal_comment VARCHAR;"))
except Exception as e:
    print(e)
    db.rollback()

try:
    db.execute(text("ALTER TABLE expense_requests ADD COLUMN status_comment VARCHAR;"))
except Exception as e:
    print(e)
    db.rollback()

db.commit()
print("Migrations completed!")
