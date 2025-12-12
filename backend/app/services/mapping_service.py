"""
Mapping Service
Centralized service for managing account mappings between company accounts and master chart

Handles:
- Mapping suggestions (AI-powered)
- Mapping confirmations
- Bulk mapping operations
- Group propagation
- Semantic matching with pgvector (when available)

UPDATED: 2025-12-11
- Added semantic search support with pgvector
- Enhanced suggestion engine with embedding-based similarity
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from uuid import UUID

from app.db.models.account_mapping import AccountMapping
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.schemas.account_mapping import AccountMappingCreate, AccountMapping as AccountMappingSchema
from app.services.master_chart_service import MasterChartService

# Optional: Embedding service for semantic search
try:
    from app.services.embedding_service import get_embedding_service, is_embeddings_available
    EMBEDDINGS_ENABLED = True
except ImportError:
    EMBEDDINGS_ENABLED = False
    get_embedding_service = None
    is_embeddings_available = lambda: False


class MappingService:
    """
    Centralized service for account mapping operations

    Provides:
    - AI-powered mapping suggestions
    - Mapping confirmation/rejection workflow
    - Bulk mapping operations
    - Group-based mapping propagation
    - Statistics and reporting
    """

    def __init__(self, db: Session):
        self.db = db
        self.master_chart_service = MasterChartService(db)

    # ========================================
    # CRUD OPERATIONS
    # ========================================

    def get_mapping_by_id(self, mapping_id: UUID) -> Optional[AccountMapping]:
        """Get a single mapping by ID"""
        return self.db.query(AccountMapping).filter(
            AccountMapping.id == mapping_id
        ).first()

    def get_mappings_for_company(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[AccountMapping]:
        """
        Get all mappings for a company

        Args:
            company_id: Company UUID
            status: Filter by status (suggested, confirmed, rejected, manual_review)
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            List of AccountMapping objects
        """
        query = self.db.query(AccountMapping).join(
            CompanyAccount,
            AccountMapping.company_account_id == CompanyAccount.id
        ).filter(
            CompanyAccount.company_id == company_id
        )

        if status:
            query = query.filter(AccountMapping.status == status)

        if min_confidence is not None:
            query = query.filter(AccountMapping.confidence >= min_confidence)

        return query.all()

    def get_mapping_for_account(
        self,
        company_account_id: UUID
    ) -> Optional[AccountMapping]:
        """Get the current mapping for a company account"""
        return self.db.query(AccountMapping).filter(
            AccountMapping.company_account_id == company_account_id
        ).order_by(AccountMapping.created_at.desc()).first()

    def create_mapping(
        self,
        company_account_id: UUID,
        master_code: str,
        confidence: float,
        status: str = "suggested",
        notes: Optional[str] = None,
        propagated_from: Optional[UUID] = None
    ) -> AccountMapping:
        """
        Create a new account mapping

        Args:
            company_account_id: Company account UUID
            master_code: Master account code
            confidence: Confidence score (0.0 to 1.0)
            status: Mapping status (suggested, confirmed, rejected, manual_review)
            notes: Optional notes
            propagated_from: Source company if propagated from group

        Returns:
            Created AccountMapping object
        """
        # Verify company account exists
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()
        if not company_account:
            raise ValueError(f"Company account {company_account_id} not found")

        # Verify master code exists
        master_account = self.master_chart_service.get_account_by_code(master_code)
        if not master_account:
            raise ValueError(f"Master account {master_code} not found")

        # Validate confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        # Create mapping
        mapping = AccountMapping(
            company_account_id=company_account_id,
            master_code=master_code,
            confidence=confidence,
            status=status,
            notes=notes,
            propagated_from=propagated_from
        )

        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)

        return mapping

    def update_mapping(
        self,
        mapping_id: UUID,
        master_code: Optional[str] = None,
        confidence: Optional[float] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[AccountMapping]:
        """Update an existing mapping"""
        mapping = self.get_mapping_by_id(mapping_id)
        if not mapping:
            return None

        if master_code is not None:
            # Verify new master code exists
            master_account = self.master_chart_service.get_account_by_code(master_code)
            if not master_account:
                raise ValueError(f"Master account {master_code} not found")
            mapping.master_code = master_code

        if confidence is not None:
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0")
            mapping.confidence = confidence

        if status is not None:
            mapping.status = status

        if notes is not None:
            mapping.notes = notes

        self.db.commit()
        self.db.refresh(mapping)

        return mapping

    def delete_mapping(self, mapping_id: UUID) -> bool:
        """Delete a mapping"""
        mapping = self.get_mapping_by_id(mapping_id)
        if not mapping:
            return False

        self.db.delete(mapping)
        self.db.commit()
        return True

    # ========================================
    # SUGGESTION ENGINE
    # ========================================

    def suggest_mapping(
        self,
        company_account_id: UUID,
        auto_create: bool = True
    ) -> Dict[str, Any]:
        """
        Suggest a master account mapping for a company account

        Uses master chart service's AI-powered suggestion engine

        Args:
            company_account_id: Company account UUID
            auto_create: If True, automatically create mapping suggestion in DB

        Returns:
            Dictionary with suggestion details
        """
        # Get company account
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()
        if not company_account:
            raise ValueError(f"Company account {company_account_id} not found")

        # Use master chart service to suggest accounts
        suggestions = self.master_chart_service.suggest_accounts(
            description=company_account.description,
            vendor=None,  # TODO: Add vendor tracking to CompanyAccount
            limit=5
        )

        if not suggestions:
            return {
                "company_account_id": str(company_account_id),
                "suggestions": [],
                "top_match": None
            }

        # Get top suggestion
        top_match = suggestions[0] if suggestions else None

        # Auto-create mapping if requested
        if auto_create and top_match:
            # Check if mapping already exists
            existing = self.get_mapping_for_account(company_account_id)
            if not existing:
                self.create_mapping(
                    company_account_id=company_account_id,
                    master_code=top_match["account"]["code"],
                    confidence=top_match["confidence"],
                    status="suggested",
                    notes=f"Auto-suggested: {top_match['reason']}"
                )

        return {
            "company_account_id": str(company_account_id),
            "company_account_name": company_account.description,
            "suggestions": suggestions,
            "top_match": top_match
        }

    def suggest_mappings_for_company(
        self,
        company_id: UUID,
        auto_create: bool = True,
        only_unmapped: bool = True
    ) -> Dict[str, Any]:
        """
        Generate mapping suggestions for all accounts in a company

        Args:
            company_id: Company UUID
            auto_create: If True, automatically create mapping suggestions
            only_unmapped: If True, only suggest for accounts without existing mappings

        Returns:
            Dictionary with suggestion statistics and results
        """
        # Get all company accounts
        company_accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active == True
        ).all()

        results = {
            "company_id": str(company_id),
            "total_accounts": len(company_accounts),
            "processed": 0,
            "suggested": 0,
            "skipped": 0,
            "suggestions": []
        }

        for account in company_accounts:
            # Skip if already has mapping and only_unmapped is True
            if only_unmapped:
                existing = self.get_mapping_for_account(account.id)
                if existing:
                    results["skipped"] += 1
                    continue

            # Generate suggestion
            suggestion = self.suggest_mapping(
                company_account_id=account.id,
                auto_create=auto_create
            )

            results["processed"] += 1
            if suggestion["top_match"]:
                results["suggested"] += 1
                results["suggestions"].append(suggestion)

        return results

    # ========================================
    # CONFIRMATION WORKFLOW
    # ========================================

    def confirm_mapping(
        self,
        mapping_id: UUID,
        notes: Optional[str] = None
    ) -> AccountMapping:
        """Confirm a suggested mapping"""
        return self.update_mapping(
            mapping_id=mapping_id,
            status="confirmed",
            notes=notes
        )

    def reject_mapping(
        self,
        mapping_id: UUID,
        notes: Optional[str] = None
    ) -> AccountMapping:
        """Reject a suggested mapping"""
        return self.update_mapping(
            mapping_id=mapping_id,
            status="rejected",
            notes=notes
        )

    def flag_for_review(
        self,
        mapping_id: UUID,
        notes: Optional[str] = None
    ) -> AccountMapping:
        """Flag a mapping for manual review"""
        return self.update_mapping(
            mapping_id=mapping_id,
            status="manual_review",
            notes=notes
        )

    # ========================================
    # BULK OPERATIONS
    # ========================================

    def confirm_all_high_confidence(
        self,
        company_id: UUID,
        confidence_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Automatically confirm all mappings above a confidence threshold

        Args:
            company_id: Company UUID
            confidence_threshold: Minimum confidence to auto-confirm (default: 0.85)

        Returns:
            Statistics about confirmed mappings
        """
        mappings = self.get_mappings_for_company(
            company_id=company_id,
            status="suggested",
            min_confidence=confidence_threshold
        )

        confirmed_count = 0
        for mapping in mappings:
            self.confirm_mapping(
                mapping_id=mapping.id,
                notes=f"Auto-confirmed (confidence >= {confidence_threshold})"
            )
            confirmed_count += 1

        return {
            "company_id": str(company_id),
            "confidence_threshold": confidence_threshold,
            "confirmed_count": confirmed_count
        }

    # ========================================
    # STATISTICS & REPORTING
    # ========================================

    def get_mapping_stats(self, company_id: UUID) -> Dict[str, Any]:
        """
        Get mapping statistics for a company

        Returns:
            Dictionary with mapping statistics
        """
        # Get all company accounts
        total_accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active == True
        ).count()

        # Get mappings by status
        mappings = self.get_mappings_for_company(company_id)

        suggested = sum(1 for m in mappings if m.status == "suggested")
        confirmed = sum(1 for m in mappings if m.status == "confirmed")
        rejected = sum(1 for m in mappings if m.status == "rejected")
        manual_review = sum(1 for m in mappings if m.status == "manual_review")

        unmapped = total_accounts - len(mappings)

        # Calculate average confidence
        avg_confidence = sum(m.confidence for m in mappings) / len(mappings) if mappings else 0.0

        return {
            "company_id": str(company_id),
            "total_accounts": total_accounts,
            "total_mappings": len(mappings),
            "unmapped": unmapped,
            "by_status": {
                "suggested": suggested,
                "confirmed": confirmed,
                "rejected": rejected,
                "manual_review": manual_review
            },
            "average_confidence": round(avg_confidence, 2),
            "completion_percentage": round((len(mappings) / total_accounts * 100), 2) if total_accounts > 0 else 0.0
        }

    # ========================================
    # SEMANTIC SEARCH (pgvector-based)
    # ========================================

    def find_similar_master_accounts(
        self,
        company_account_id: UUID,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find similar master accounts using semantic search (pgvector).

        Args:
            company_account_id: Company account to find matches for
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold (0-1)

        Returns:
            List of dictionaries with master account and similarity score
        """
        if not EMBEDDINGS_ENABLED or not is_embeddings_available():
            return []

        # Get company account
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()

        if not company_account or not company_account.embedding:
            return []

        # Query for similar accounts using pgvector cosine distance
        # <=> is the cosine distance operator in pgvector
        query = text("""
            SELECT
                code,
                description,
                category,
                1 - (embedding <=> :query_embedding) AS similarity
            FROM master_accounts
            WHERE embedding IS NOT NULL
                AND (1 - (embedding <=> :query_embedding)) >= :min_similarity
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)

        results = self.db.execute(
            query,
            {
                "query_embedding": company_account.embedding,
                "min_similarity": min_similarity,
                "limit": limit
            }
        ).fetchall()

        return [
            {
                "code": row.code,
                "description": row.description,
                "category": row.category,
                "similarity": float(row.similarity)
            }
            for row in results
        ]

    def suggest_mapping_with_embeddings(
        self,
        company_account_id: UUID,
        auto_create: bool = True,
        use_semantic: bool = True,
        semantic_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        Enhanced mapping suggestion that combines AI and semantic search.

        Args:
            company_account_id: Company account UUID
            auto_create: If True, automatically create mapping suggestion
            use_semantic: If True, blend semantic search results with AI suggestions
            semantic_weight: Weight for semantic results (0-1), AI gets (1-semantic_weight)

        Returns:
            Dictionary with blended suggestions
        """
        # Get standard AI suggestions
        ai_suggestions = self.suggest_mapping(
            company_account_id=company_account_id,
            auto_create=False  # We'll create manually after blending
        )

        if not use_semantic or not EMBEDDINGS_ENABLED:
            # Fall back to AI-only suggestions
            if auto_create and ai_suggestions.get("top_match"):
                self._create_suggestion_from_match(company_account_id, ai_suggestions["top_match"])
            return ai_suggestions

        # Get semantic search results
        semantic_results = self.find_similar_master_accounts(
            company_account_id=company_account_id,
            limit=5
        )

        if not semantic_results:
            # Fall back to AI-only if no semantic results
            if auto_create and ai_suggestions.get("top_match"):
                self._create_suggestion_from_match(company_account_id, ai_suggestions["top_match"])
            return ai_suggestions

        # Blend results (combine AI confidence with semantic similarity)
        blended_results = self._blend_suggestions(
            ai_suggestions.get("suggestions", []),
            semantic_results,
            semantic_weight
        )

        result = {
            "company_account_id": str(company_account_id),
            "company_account_name": ai_suggestions.get("company_account_name", ""),
            "suggestions": blended_results,
            "top_match": blended_results[0] if blended_results else None,
            "method": "blended" if blended_results else "ai_only"
        }

        # Auto-create mapping if requested
        if auto_create and result["top_match"]:
            self._create_suggestion_from_match(company_account_id, result["top_match"])

        return result

    def _blend_suggestions(
        self,
        ai_suggestions: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        semantic_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Blend AI and semantic suggestions using weighted scoring.

        Args:
            ai_suggestions: AI-generated suggestions with confidence scores
            semantic_results: Semantic search results with similarity scores
            semantic_weight: Weight for semantic (0-1)

        Returns:
            Sorted list of blended suggestions
        """
        ai_weight = 1.0 - semantic_weight

        # Create lookup for AI scores
        ai_scores = {}
        for sugg in ai_suggestions:
            account = sugg.get("account", {})
            code = account.get("code")
            if code:
                ai_scores[code] = sugg.get("confidence", 0.0)

        # Create lookup for semantic scores
        semantic_scores = {
            res["code"]: res["similarity"]
            for res in semantic_results
        }

        # Combine all unique codes
        all_codes = set(ai_scores.keys()) | set(semantic_scores.keys())

        # Calculate blended scores
        blended = []
        for code in all_codes:
            ai_score = ai_scores.get(code, 0.0)
            semantic_score = semantic_scores.get(code, 0.0)

            blended_score = (ai_weight * ai_score) + (semantic_weight * semantic_score)

            # Get account details
            master_account = self.master_chart_service.get_account_by_code(code)
            if master_account:
                blended.append({
                    "account": {
                        "code": master_account.code,
                        "description": master_account.description,
                        "category": master_account.category
                    },
                    "confidence": blended_score,
                    "ai_confidence": ai_score,
                    "semantic_similarity": semantic_score,
                    "reason": f"Blended: AI={ai_score:.2f}, Semantic={semantic_score:.2f}"
                })

        # Sort by blended score
        blended.sort(key=lambda x: x["confidence"], reverse=True)

        return blended[:5]  # Return top 5

    def _create_suggestion_from_match(
        self,
        company_account_id: UUID,
        match: Dict[str, Any]
    ):
        """Helper to create mapping suggestion from a match."""
        # Check if mapping already exists
        existing = self.get_mapping_for_account(company_account_id)
        if existing:
            return

        account = match.get("account", {})
        self.create_mapping(
            company_account_id=company_account_id,
            master_code=account.get("code"),
            confidence=match.get("confidence", 0.0),
            status="suggested",
            notes=match.get("reason", "Auto-suggested")
        )

    # ========================================
    # GROUP PROPAGATION (for multi-company)
    # ========================================

    def propagate_mappings_to_group(
        self,
        source_company_id: UUID,
        target_company_ids: List[UUID],
        only_confirmed: bool = True
    ) -> Dict[str, Any]:
        """
        Propagate mappings from one company to others in a group

        Args:
            source_company_id: Source company UUID
            target_company_ids: List of target company UUIDs
            only_confirmed: If True, only propagate confirmed mappings

        Returns:
            Statistics about propagation
        """
        # Get source mappings
        source_mappings = self.get_mappings_for_company(
            company_id=source_company_id,
            status="confirmed" if only_confirmed else None
        )

        results = {
            "source_company_id": str(source_company_id),
            "target_companies": len(target_company_ids),
            "source_mappings": len(source_mappings),
            "propagated": 0,
            "skipped": 0
        }

        for target_company_id in target_company_ids:
            for source_mapping in source_mappings:
                # Get source company account details
                source_account = self.db.query(CompanyAccount).filter(
                    CompanyAccount.id == source_mapping.company_account_id
                ).first()

                if not source_account:
                    continue

                # Find matching account in target company (by code)
                target_account = self.db.query(CompanyAccount).filter(
                    CompanyAccount.company_id == target_company_id,
                    CompanyAccount.code == source_account.code
                ).first()

                if not target_account:
                    results["skipped"] += 1
                    continue

                # Check if target already has a mapping
                existing = self.get_mapping_for_account(target_account.id)
                if existing:
                    results["skipped"] += 1
                    continue

                # Create propagated mapping
                self.create_mapping(
                    company_account_id=target_account.id,
                    master_code=source_mapping.master_code,
                    confidence=source_mapping.confidence,
                    status="suggested",  # Propagated mappings start as suggested
                    notes=f"Propagated from {source_company_id}",
                    propagated_from=source_company_id
                )
                results["propagated"] += 1

        return results
