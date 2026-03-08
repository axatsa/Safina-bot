from sqlalchemy.orm import Session
from app.db import models
from app.core import auth, database
import logging
import os

logger = logging.getLogger(__name__)

def seed_users():
    """Ensure essential users like the Senior Financier exist in the DB."""
    db: Session = next(database.get_db())
    try:
        # Define Senior Financier data
        sf_login = os.getenv("SF_LOGIN", "farrukh")
        sf_password = os.getenv("SF_PASSWORD", "s_admin123")
        sf_data = {
            "login": sf_login,
            "password": sf_password,
            "first_name": "Фаррух",
            "last_name": "Носиров",
            "position": "senior_financier",
            "status": "active"
        }

        # Check if user already exists
        user = db.query(models.TeamMember).filter(models.TeamMember.login == sf_data["login"]).first()
        
        if not user:
            logger.info(f"Seeding user: {sf_data['login']} ...")
            hashed_password = auth.get_password_hash(sf_data["password"])
            new_user = models.TeamMember(
                login=sf_data["login"],
                password_hash=hashed_password,
                first_name=sf_data["first_name"],
                last_name=sf_data["last_name"],
                position=sf_data["position"],
                status=sf_data["status"]
            )
            db.add(new_user)
            db.commit()
            logger.info(f"User {sf_data['login']} created successfully.")
            # Optionally update info if needed, but for now just update password hash if changed
            hashed_password = auth.get_password_hash(sf_data["password"])
            if user.password_hash != hashed_password:
                user.password_hash = hashed_password
                db.commit()
                logger.info(f"User {sf_data['login']} password updated from .env.")
            else:
                logger.info(f"User {sf_data['login']} already exists. Skipping seed.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding users: {str(e)}")
    finally:
        db.close()
