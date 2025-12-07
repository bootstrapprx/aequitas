from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ClientLog(BaseModel):
    level: str
    message: str
    timestamp: str

@router.post("/client-logs")
async def log_client_message(log: ClientLog):
    """
    Receives logs from the frontend and prints them to stdout so they are captured by Docker logs.
    """
    # Format matches the style of uvicorn logs but distinct
    print(f"[CLIENT-LOG] [{log.timestamp}] [{log.level.upper()}] {log.message}")
    return {"status": "ok"}
