import datetime
from decimal import Decimal

_BACK = "◀️ Назад"

TASHKENT_TZ = datetime.timezone(datetime.timedelta(hours=5))

def tashkent_now() -> datetime.datetime:
    return datetime.datetime.now(tz=TASHKENT_TZ)

def get_user_position(db, login: str) -> str | None:
    """Sync DB lookup for a user's position."""
    from app.db import models
    user = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()
    return user.position if user else None

def prepare_items_data(raw_items) -> list[dict]:
    """Parse raw JSON items from DB into a list of dicts for document generators."""
    import json
    if isinstance(raw_items, str):
        try:
            raw_items = json.loads(raw_items)
        except Exception:
            raw_items = []
    result = []
    if isinstance(raw_items, list):
        for idx, item in enumerate(raw_items):
            if isinstance(item, dict):
                try:
                    qty = Decimal(str(item.get("quantity", "0")))
                    price = Decimal(str(item.get("amount", "0")))
                    result.append({
                        "no": idx + 1,
                        "name": item.get("name", ""),
                        "quantity": qty,
                        "amount": price,
                        "price": price,
                        "unit_price": price,
                        "total": qty * price,
                    })
                except (ValueError, TypeError, Exception):
                    continue
    return result
