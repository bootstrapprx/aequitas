from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    ucid: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    sources: Optional[List[str]] = None
    suggested_actions: Optional[List[str]] = None

class IngestRequest(BaseModel):
    ucid: str
    data_type: str  # "account_patterns", "ledger", "mappings"
    content: Optional[Dict[str, Any]] = None

class SuggestionRequest(BaseModel):
    ucid: str
    description: str
    amount: Optional[float] = None
    vendor: Optional[str] = None

class AccountSuggestion(BaseModel):
    account_code: str
    account_name: str
    confidence: float
    reasoning: str
