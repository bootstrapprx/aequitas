from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.db.session import get_db
from sqlalchemy.orm import Session
from .models import ChatRequest, ChatResponse, IngestRequest, SuggestionRequest, AccountSuggestion
from .engine import dexter_engine

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Interact with Dexter via chat.
    """
    try:
        return await dexter_engine.chat(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_data(request: IngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest data into Dexter's knowledge base (Passive Mode).
    Runs in background.
    """
    # Note: Passing db session to background task can be tricky if session closes.
    # Ideally, background task should create its own session.
    # But for simplicity here, we'll assume it runs quickly or we should refactor to pass session factory.
    # Actually, fastapi background tasks run after response, so dependency session might be closed.
    # Better to instantiate a new session in the background task or use a service that manages it.
    # For now, let's pass the request and let the engine handle session creation if possible, 
    # OR just run it synchronously for now if it's fast, OR accept the risk/refactor later.
    # Given the constraints, I'll pass the session but it's risky. 
    # BETTER: Pass a session factory or just don't use background task for the DB part if possible.
    # OR: The engine method `ingest` should create a new session.
    # Let's change `ingest` to NOT take db from dependency, but create one?
    # No, `get_db` yields a session.
    # Let's run it synchronously for now to avoid session closed error, or use `BackgroundTasks` properly with a separate session.
    # I will run it synchronously for now to be safe, or just await it.
    # The prompt asked for background job pipelines.
    # I'll leave it as background task but I'll need to fix the session issue.
    # I'll update `ingest` in engine to create a new session.
    background_tasks.add_task(dexter_engine.ingest, request)
    return {"message": "Ingestion started"}

@router.post("/suggest-account", response_model=AccountSuggestion)
async def suggest_account(request: SuggestionRequest, db: Session = Depends(get_db)):
    """
    Get an account suggestion for a transaction.
    """
    try:
        return await dexter_engine.suggest_account(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
