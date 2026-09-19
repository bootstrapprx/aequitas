from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()

class ClientLog(BaseModel):
    level: str = Field(max_length=20)
    message: str = Field(max_length=4_000)
    timestamp: str = Field(max_length=64)


@router.post("/client-logs")
async def log_client_message(
    log: ClientLog,
    current_user: User = Depends(get_current_user),
):
    """
    Receives logs from the frontend and prints them to stdout so they are captured by Docker logs.
    """
    # Format matches the style of uvicorn logs but distinct
    print(f"[CLIENT-LOG] [{log.timestamp}] [{log.level.upper()}] {log.message}")
    return {"status": "ok"}
