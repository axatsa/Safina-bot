from sqlalchemy.orm import Session
from app.db import models
from app.core import auth, database
import logging
import os

logger = logging.getLogger(__name__)

# --- Role definitions for scalability ---
# To add a new seeded user, add a dict to SEEDED_USERS:
#   login_env_key, password_env_key, default_login, default_password,
#   first_name, last_name, position, status
SEEDED_USERS = [
    {
        "login_env_key": "SF_LOGIN",
        "password_env_key": "SF_PASSWORD",
        "default_login": "farrukh",
        "default_password": "s_admin123",
        "first_name": "Фаррух",
        "last_name": "Носиров",
        "position": "senior_financier",
        "status": "active",
    },
    {
        "login_env_key": "CEO_LOGIN",
        "password_env_key": "CEO_PASSWORD",
        "default_login": "ganiev",
        "default_password": "g_admin123",
        "first_name": "Ганиев",
        "last_name": "CEO",
        "position": "ceo",
        "status": "active",
    },
]


def _seed_user(db: Session, user_data: dict) -> None:
    """Create or update a single seeded user."""
    login = os.getenv(user_data["login_env_key"], user_data["default_login"])
    password = os.getenv(user_data["password_env_key"], user_data["default_password"])
    hashed_password = auth.get_password_hash(password)

    user = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()

    if not user:
        logger.info(f"Seeding user: {login} (position={user_data['position']}) ...")
        new_user = models.TeamMember(
            login=login,
            password_hash=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            position=user_data["position"],
            status=user_data["status"],
        )
        db.add(new_user)
        db.commit()
        logger.info(f"User '{login}' created successfully.")
    else:
        # Update password from env if it has changed
        if not auth.verify_password(password, user.password_hash):
            user.password_hash = hashed_password
            db.commit()
            logger.info(f"User '{login}' password updated from .env.")
        else:
            logger.info(f"User '{login}' already exists, no changes needed.")


def seed_users() -> None:
    """Ensure all essential system users exist in the DB."""
    db: Session = next(database.get_db())
    try:
        for user_data in SEEDED_USERS:
            _seed_user(db, user_data)
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding users: {str(e)}", exc_info=True)
    finally:
        db.close()
