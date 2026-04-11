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
        "role": "senior_financier",
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
        "role": "ceo",
        "status": "active",
    },
    {
        "login_env_key": "FIN_LOGIN",
        "password_env_key": "FIN_PASSWORD",
        "default_login": "financier",
        "default_password": "f_admin123",
        "first_name": "Финансист",
        "last_name": "Команда",
        "position": "admin",
        "role": "admin",
        "team": "Финансисты",
        "status": "active",
    },
    {
        "login_env_key": "PM_LOGIN",
        "password_env_key": "PM_PASSWORD",
        "default_login": "abd",
        "default_password": "abd123",
        "first_name": "Product",
        "last_name": "Manager",
        "position": "product_manager",
        "role": "admin",
        "status": "active",
    },
]


def _seed_user(db: Session, user_data: dict) -> None:
    """Create or update a single seeded user."""
    login = os.getenv(user_data["login_env_key"], user_data["default_login"])
    
    # Check if using default password
    env_password = os.getenv(user_data["password_env_key"])
    if not env_password:
        logger.warning(f"⚠️ {user_data['password_env_key']} not set in environment! Using default password — CHANGE THIS IN PRODUCTION")
        password = user_data["default_password"]
    else:
        password = env_password
        
    hashed_password = auth.get_password_hash(password)

    user = db.query(models.User).filter(models.User.login == login).first()

    if not user:
        logger.info(f"Seeding user: {login} (position={user_data['position']}) ...")
        new_user = models.User(
            login=login,
            password_hash=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            position=user_data["position"],
            role=user_data.get("role", "user"),
            team=user_data.get("team"),
            status=user_data["status"],
        )
        db.add(new_user)
        db.commit()
        logger.info(f"User '{login}' created successfully.")
    else:
        # Update fields from SEEDED_USERS if needed
        updated = False
        if user.position != user_data["position"]:
            user.position = user_data["position"]
            updated = True
        if user_data.get("role") and user.role != user_data["role"]:
            user.role = user_data["role"]
            updated = True
        if user_data.get("team") and user.team != user_data["team"]:
            user.team = user_data["team"]
            updated = True
        
        # Update password from env if it has changed
        if not auth.verify_password(password, user.password_hash):
            user.password_hash = hashed_password
            updated = True
            logger.info(f"User '{login}' password updated from .env.")
            
        if updated:
            db.commit()
            logger.info(f"User '{login}' information updated.")
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
