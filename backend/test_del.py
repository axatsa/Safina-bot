import sys
import traceback

try:
    import database, models, auth
    from sqlalchemy import text
    db = next(database.get_db())
    proj = db.query(models.Project).first()
    if proj:
        print('Deleting project:', proj.id)
        db.delete(proj)
        db.commit()
        print('Deleted')
    else:
        print('No projects')
except Exception as e:
    print('EXCEPTION OCCURRED:')
    traceback.print_exc()
