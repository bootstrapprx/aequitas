import sys
from sqlalchemy.orm import configure_mappers
from app.db.base import Base
from app.db.models import *  # Import all models

try:
    print("Configuring mappers...")
    configure_mappers()
    print("Mapper configuration successful!")
except Exception as e:
    print(f"Mapper configuration failed: {e}")
    import traceback
    traceback.print_exc()
