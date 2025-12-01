import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import ChatRequest, ChatResponse, IngestRequest, SuggestionRequest, AccountSuggestion

logger = logging.getLogger(__name__)

class DexterEngine:
    def __init__(self):
        self.model_name = "qwen2.5-coder:1.5b" # Should load from env
        # Initialize vector store connection here
        # Initialize Ollama client here
        pass

    async def chat(self, request: ChatRequest, db: Session) -> ChatResponse:
        """
        Active Mode: Process user chat message.
        """
        logger.info(f"Dexter Chat Request: {request.message} (UCID: {request.ucid})")
        
        from app.services.dexter.learning_engine import LearningEngine
        learning_engine = LearningEngine(db)
        
        # 1. Get embedding
        query_vector = await learning_engine.get_embedding(request.message)
        
        # 2. Search context
        context_docs = learning_engine.vector_store.search(request.ucid, query_vector, limit=5)
        context_text = "\n".join([f"- {doc.content}" for doc in context_docs])
        
        # 3. Construct prompt
        prompt = f"""You are Dexter, an expert AI accounting assistant for ChartForge.
Use the following context from the company's records to answer the user's question.
If the answer is not in the context, use your general accounting knowledge but mention that it's general advice.

Context:
{context_text}

User: {request.message}
Dexter:"""

        # 4. Call Ollama
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{learning_engine.ollama_base_url}/api/generate",
                json={
                    "model": learning_engine.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            reply = response.json()["response"]

        return ChatResponse(
            reply=reply,
            suggested_actions=[] # Could extract actions from reply if needed
        )

    async def ingest(self, request: IngestRequest):
        """
        Passive Mode: Ingest data for learning.
        Creates its own DB session to run in background safely.
        """
        logger.info(f"Dexter Ingest Request: {request.data_type} for UCID: {request.ucid}")
        
        from app.db.session import SessionLocal
        from app.services.dexter.learning_engine import LearningEngine
        
        db = SessionLocal()
        try:
            learning_engine = LearningEngine(db)
            if request.data_type == "master_chart":
                await learning_engine.ingest_company_accounts(request.ucid)
            elif request.data_type == "mappings":
                await learning_engine.ingest_mappings(request.ucid)
            elif request.data_type == "rebuild":
                await learning_engine.rebuild_embeddings(request.ucid)
            else:
                logger.warning(f"Unknown data type for ingestion: {request.data_type}")
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
        finally:
            db.close()

    async def suggest_account(self, request: SuggestionRequest, db: Session) -> AccountSuggestion:
        """
        Active Mode: Suggest account for a transaction.
        """
        logger.info(f"Dexter Suggestion Request: {request.description}")
        
        from app.services.dexter.learning_engine import LearningEngine
        learning_engine = LearningEngine(db)
        
        # 1. Get embedding
        query_vector = await learning_engine.get_embedding(request.description)
        
        # 2. Search for similar mappings or accounts
        # Search for mappings first as they are direct precedents
        similar_mappings = learning_engine.vector_store.search(request.ucid, query_vector, limit=3, entity_type="mapping")
        
        context_text = ""
        if similar_mappings:
            context_text += "Similar past mappings:\n" + "\n".join([f"- {doc.content}" for doc in similar_mappings])
        
        # Also search accounts
        similar_accounts = learning_engine.vector_store.search(request.ucid, query_vector, limit=3, entity_type="account")
        if similar_accounts:
            context_text += "\nRelevant accounts:\n" + "\n".join([f"- {doc.content}" for doc in similar_accounts])
            
        # 3. Prompt
        prompt = f"""You are Dexter, an accounting assistant.
Suggest the best General Ledger account for the following transaction description.
Return ONLY a JSON object with keys: "account_code", "account_name", "confidence" (0.0-1.0), "reasoning".

Transaction: {request.description}

Context:
{context_text}

Response (JSON only):"""

        # 4. Call Ollama
        import httpx
        import json
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{learning_engine.ollama_base_url}/api/generate",
                json={
                    "model": learning_engine.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json" # Enforce JSON
                },
                timeout=30.0
            )
            response.raise_for_status()
            result_json = response.json()["response"]
            
            try:
                result = json.loads(result_json)
                return AccountSuggestion(
                    account_code=result.get("account_code", "Unknown"),
                    account_name=result.get("account_name", "Unknown"),
                    confidence=result.get("confidence", 0.5),
                    reasoning=result.get("reasoning", "AI suggestion")
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from AI: {result_json}")
                return AccountSuggestion(
                    account_code="Unknown",
                    account_name="Unknown",
                    confidence=0.0,
                    reasoning="Failed to parse AI response"
                )

# Global instance
dexter_engine = DexterEngine()
