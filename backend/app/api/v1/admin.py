from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db, engine
from app.db.base import Base
from app.api.v1.auth import get_current_user
from app.db.models.user import User

router = APIRouter()

@router.post("/reset-db")
def reset_database(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset the database by dropping and recreating all tables.
    Only accessible by superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Recreate all tables
    Base.metadata.create_all(bind=engine)
    
    # Re-seed superuser
    from app.db.init_db import init_db
    init_db(db)
    
    return {"message": "Database reset successfully"}
