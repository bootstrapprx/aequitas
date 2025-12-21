import logging
import re
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from .models import (
    ChatRequest, ChatResponse, IngestRequest, SuggestionRequest, AccountSuggestion,
    OnboardingPreprocessRequest, OnboardingPreprocessResponse
)
from .fiscal_adapter import FiscalAdapter
from app.services.normalization_service import normalization_service

logger = logging.getLogger(__name__)

class DexterEngine:
    def __init__(self):
        self.model_name = "qwen2.5-coder:1.5b" # Should load from env
        # Initialize vector store connection here
        # Initialize Ollama client here
        pass

    def _is_fiscal_query(self, message: str) -> bool:
        """
        Detect if the query is about tax exposure / fiscal matters.
        """
        fiscal_keywords = [
            "tax", "liability", "exposure", "taxable income", "projected tax",
            "tax position", "tax driver", "what do i owe", "tax estimate",
            "fiscal", "tax calculation", "missing input"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in fiscal_keywords)

    def _extract_company_id(self, ucid: str, db: Session) -> Optional[UUID]:
        """
        Extract company UUID from UCID.
        """
        from app.db.models.company import Company
        company = db.query(Company).filter(Company.ucid == ucid).first()
        return company.id if company else None

    async def chat(self, request: ChatRequest, db: Session) -> ChatResponse:
        """
        Active Mode: Process user chat message.
        """
        logger.info(f"Dexter Chat Request: {request.message} (UCID: {request.ucid})")

        # Check if this is a fiscal query
        if self._is_fiscal_query(request.message):
            return await self._handle_fiscal_query(request, db)

        from app.services.dexter.learning_engine import LearningEngine
        learning_engine = LearningEngine(db)

        # 1. Get embedding
        query_vector = await learning_engine.get_embedding(request.message)

        # 2. Search context
        context_docs = learning_engine.vector_store.search(request.ucid, query_vector, limit=5)
        context_text = "\n".join([f"- {doc.content}" for doc in context_docs])

        # 3. Construct prompt
        prompt = f"""You are Dexter, an expert AI accounting assistant for Aequitas.
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

    async def _handle_fiscal_query(self, request: ChatRequest, db: Session) -> ChatResponse:
        """
        Handle fiscal/tax-related queries using the FiscalAdapter.
        """
        logger.info(f"Handling fiscal query: {request.message}")

        # Get company ID from UCID
        company_id = self._extract_company_id(request.ucid, db)
        if not company_id:
            return ChatResponse(
                reply="I couldn't find a company with that UCID. Please check the company identifier.",
                suggested_actions=[]
            )

        # Initialize fiscal adapter
        fiscal_adapter = FiscalAdapter(db)

        # Determine query type
        message_lower = request.message.lower()
        if any(word in message_lower for word in ["driver", "what's driving", "why", "breakdown"]):
            question_type = "drivers"
        elif any(word in message_lower for word in ["missing", "incomplete", "what do i need", "checklist"]):
            question_type = "missing_inputs"
        elif any(word in message_lower for word in ["liability", "owe", "tax", "exposure", "projected"]):
            question_type = "liability"
        else:
            question_type = "all"

        # Get formatted response
        reply = fiscal_adapter.format_for_dexter_response(company_id, question_type)

        # Generate suggested actions based on missing inputs
        suggested_actions = []
        if question_type in ["missing_inputs", "all"]:
            checklist = fiscal_adapter.get_missing_inputs_checklist(company_id)
            if checklist.get("checklist"):
                suggested_actions.append("Update tax profile")
                suggested_actions.append("Add tax tags to accounts")

        return ChatResponse(
            reply=reply,
            suggested_actions=suggested_actions
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

    async def preprocess_onboarding(self, request: OnboardingPreprocessRequest) -> OnboardingPreprocessResponse:
        """
        Active Mode: Preprocess user input during onboarding.
        Delegates to NormalizationService for deterministic checks.
        """
        logger.info(f"Dexter Preprocess Request: {request.field}='{request.user_input}' (Step: {request.step})")
        
        # 1. Company Name Normalization
        if request.field == "name" or request.field == "company_name":
            normalized, confidence, changes = normalization_service.normalize_company_name(request.user_input)
            
            if normalized != request.user_input:
                explanation = "I've standardized the capitalization for consistency."
                if any("suffix" in c for c in changes):
                    explanation += " I also updated the legal suffix."
                
                return OnboardingPreprocessResponse(
                    suggested_value=normalized,
                    confidence=confidence,
                    correction_type="capitalization",
                    explanation=explanation,
                    requires_confirmation=True
                )
        
        # 2. Country Code Normalization
        elif request.field == "country":
            res = normalization_service.normalize_country_code(request.user_input)
            if res:
                code, confidence = res
                if code != request.user_input:
                    return OnboardingPreprocessResponse(
                        suggested_value=code,
                        confidence=confidence,
                        correction_type="standardization",
                        explanation=f"I've set the country code to {code}.",
                        requires_confirmation=True
                    )

        # 3. Currency Code Normalization
        elif request.field == "currency":
             res = normalization_service.normalize_currency_code(request.user_input)
             if res:
                code, confidence = res
                if code != request.user_input:
                    return OnboardingPreprocessResponse(
                        suggested_value=code,
                        confidence=confidence,
                        correction_type="standardization",
                        explanation=f"I've set the currency code to {code}.",
                        requires_confirmation=True
                    )

        # 4. Economic Activity (Heuristic/AI)
        elif request.field == "description" and request.step == "company_details":
            # Implementation of NLP classification
            matches = normalization_service.classify_economic_activity(request.user_input)
            if matches:
                 top_cat, conf = matches[0]
                 return OnboardingPreprocessResponse(
                     suggested_value=top_cat,
                     confidence=conf,
                     correction_type="classification",
                     explanation=f"Based on your description, I suggest classifying this as {top_cat}.",
                     requires_confirmation=True
                 )

        # Default: No suggestion
        return OnboardingPreprocessResponse(
            suggested_value=request.user_input,
            confidence=1.0,
            requires_confirmation=False
        )

# Global instance
dexter_engine = DexterEngine()
