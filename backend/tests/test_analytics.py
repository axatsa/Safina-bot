import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import models
from app.api.analytics import get_analytics
from app.core import database

# Setup test DB session
# Use absolute path for DB
db_path = os.path.abspath('backend/media/safina.db')
print(f"Using DB at: {db_path}")
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Test get_analytics
try:
    # Use a dummy user
    user = db.query(models.User).first()
    if not user:
        print("No user found in DB")
        sys.exit(0)
        
    branch_name = user.branches[0].name if user.branches else "None"
    print(f"Testing for user: {user.first_name} {user.last_name} (Branch: {branch_name})")
    result = get_analytics(db=db, current_user=user)
    print("Result keys:", result.keys())
    print("Summary:", result['summary'])
    print("Timeline count:", len(result['timeline']))
    print("Distribution items:", len(result['distribution']))
    if result['distribution']:
        print("Distribution sample:", result['distribution'][0])
    print("Expense Dist count:", len(result['expense_distribution']))
    print("Refund Dist count:", len(result['refund_distribution']))
    print("User Dist count:", len(result['user_distribution']))
    if result['user_distribution']:
        print("User Dist sample:", result['user_distribution'][0])
    
    # Check for Decimal presence in the final output
    import json
    from fastapi.encoders import jsonable_encoder
    json_ready = jsonable_encoder(result)
    print("JSON ready sample (summary):", json_ready['summary'])
    print("JSON ready sample (first distribution):", json_ready['distribution'][0] if json_ready['distribution'] else "None")
    print("JSON ready sample (first user distribution):", json_ready['user_distribution'][0] if json_ready['user_distribution'] else "None")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
