"""
DEXTER Master Chart Integration
Provides DEXTER AI with intelligent access to the enriched master chart.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.master_chart_service import MasterChartService

logger = logging.getLogger(__name__)


class DexterMasterChartIntegration:
    """
    Integration layer between DEXTER AI and the Master Chart of Accounts.
    Provides intelligent account suggestion and context for AI operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.master_chart_service = MasterChartService(db)
    
    def get_master_chart_context(self, include_headers: bool = False) -> str:
        """
        Get master chart as formatted text context for AI prompts.
        
        Args:
            include_headers: Whether to include header accounts
        
        Returns:
            Formatted string with master chart information
        """
        accounts = self.master_chart_service.get_accounts_for_ai(include_headers=include_headers)
        
        context_lines = ["MASTER CHART OF ACCOUNTS:\n"]
        
        for acc in accounts[:50]:  # Limit to first 50 for context window
            line = f"- {acc['code']}: {acc['description']} ({acc['category']})"
            if acc.get('tags'):
                line += f" [Tags: {', '.join(acc['tags'][:3])}]"
            context_lines.append(line)
        
        if len(accounts) > 50:
            context_lines.append(f"\n... and {len(accounts) - 50} more accounts")
        
        return "\n".join(context_lines)
    
    def suggest_accounts_for_transaction(
        self,
        description: str,
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest accounts for a transaction using intelligent matching.
        
        Args:
            description: Transaction description
            vendor: Optional vendor name
            amount: Optional transaction amount
            limit: Maximum number of suggestions
        
        Returns:
            List of account suggestions with confidence scores
        """
        logger.info(f"DEXTER requesting account suggestions for: '{description}' (vendor: {vendor})")
        
        suggestions = self.master_chart_service.suggest_accounts(
            description=description,
            vendor=vendor,
            amount=amount,
            limit=limit
        )
        
        logger.info(f"DEXTER found {len(suggestions)} suggestions")
        return suggestions
    
    def get_account_details_for_ai(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed account information for AI context.
        
        Args:
            code: Account code
        
        Returns:
            Account details dict or None if not found
        """
        account = self.master_chart_service.get_account_by_code(code)
        if not account:
            return None
        
        return account.to_ai_context()
    
    def search_accounts_by_description(self, description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search accounts by description keywords.
        
        Args:
            description: Search query
            limit: Maximum results
        
        Returns:
            List of matching accounts
        """
        keywords = description.lower().split()
        matches = self.master_chart_service.search_by_keywords(keywords, limit=limit)
        return [acc.to_ai_context() for acc in matches]
    
    def get_vendor_account_mappings(self) -> Dict[str, List[str]]:
        """
        Get all vendor-to-account mappings for DEXTER's knowledge base.
        
        Returns:
            Dict mapping vendor names to account codes
        """
        expense_accounts = self.master_chart_service.get_expense_accounts_with_vendors()
        
        vendor_map = {}
        for acc in expense_accounts:
            if acc.default_vendors:
                for vendor in acc.default_vendors:
                    if vendor not in vendor_map:
                        vendor_map[vendor] = []
                    vendor_map[vendor].append(acc.code)
        
        return vendor_map
    
    def get_category_accounts(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all accounts in a specific category for AI context.
        
        Args:
            category: Category name (Asset, Liability, Equity, Revenue, Expense, COGS)
        
        Returns:
            List of accounts in that category
        """
        accounts = self.master_chart_service.get_accounts_by_category(category)
        return [acc.to_ai_context() for acc in accounts]
    
    def build_ai_prompt_context(
        self,
        transaction_description: Optional[str] = None,
        vendor: Optional[str] = None,
        include_suggestions: bool = True
    ) -> str:
        """
        Build a comprehensive context string for AI prompts.
        
        Args:
            transaction_description: Optional transaction to get suggestions for
            vendor: Optional vendor name
            include_suggestions: Whether to include account suggestions
        
        Returns:
            Formatted context string for AI
        """
        context_parts = []
        
        # 1. Master chart overview
        stats = self.master_chart_service.get_master_chart_stats()
        context_parts.append(f"""
MASTER CHART OVERVIEW:
- Total Accounts: {stats['total_accounts']} ({stats['detail_accounts']} detail accounts)
- Categories: {', '.join(stats['category_breakdown'].keys())}
- Vendor Mappings: {stats['accounts_with_vendors']} accounts
- AI Tags Coverage: {stats['enrichment_coverage']['ai_tags']}
""")
        
        # 2. If transaction provided, add suggestions
        if transaction_description and include_suggestions:
            suggestions = self.suggest_accounts_for_transaction(
                description=transaction_description,
                vendor=vendor,
                limit=3
            )
            
            if suggestions:
                context_parts.append("\nSUGGESTED ACCOUNTS:")
                for i, sug in enumerate(suggestions, 1):
                    acc = sug['account']
                    context_parts.append(
                        f"{i}. {acc['code']}: {acc['description']} "
                        f"(Confidence: {sug['confidence']:.0%}, Reason: {sug['reason']})"
                    )
        
        # 3. If vendor provided, show vendor mappings
        if vendor:
            vendor_accounts = self.master_chart_service.search_by_vendor(vendor)
            if vendor_accounts:
                context_parts.append(f"\nACCOUNTS FOR VENDOR '{vendor}':")
                for acc in vendor_accounts[:3]:
                    context_parts.append(f"- {acc.code}: {acc.description}")
        
        return "\n".join(context_parts)
    
    async def ingest_master_chart_for_learning(self, learning_engine):
        """
        Ingest the master chart into DEXTER's vector store for semantic search.
        
        Args:
            learning_engine: DexterLearningEngine instance
        """
        logger.info("Ingesting Master Chart into DEXTER's vector store...")
        
        accounts = self.master_chart_service.get_all_accounts(include_headers=False)
        
        for account in accounts:
            # Create rich text representation for embedding
            text_parts = [
                f"Account Code: {account.code}",
                f"Name: {account.description}",
                f"Category: {account.category}",
            ]
            
            if account.long_description:
                text_parts.append(f"Description: {account.long_description}")
            
            if account.tags:
                text_parts.append(f"Tags: {', '.join(account.tags)}")
            
            if account.default_vendors:
                text_parts.append(f"Common Vendors: {', '.join(account.default_vendors)}")
            
            text = " | ".join(text_parts)
            
            # Generate embedding
            vector = await learning_engine.get_embedding(text)
            
            # Store in vector database
            learning_engine.vector_store.add_embedding(
                company_ucid="MASTER",  # Special UCID for master chart
                entity_type="master_account",
                content=text,
                vector=vector,
                metadata={
                    "code": account.code,
                    "description": account.description,
                    "category": account.category,
                    "id": str(account.id)
                }
            )
        
        logger.info(f"Ingested {len(accounts)} master accounts into vector store")
    
    def explain_account(self, code: str) -> Optional[str]:
        """
        Get a natural language explanation of an account for DEXTER to use.
        
        Args:
            code: Account code
        
        Returns:
            Natural language explanation or None
        """
        account = self.master_chart_service.get_account_by_code(code)
        if not account:
            return None
        
        explanation_parts = [
            f"Account {account.code} - {account.description}",
            f"Category: {account.category}",
            f"Type: {'Header' if account.type == 'H' else 'Detail'}",
        ]
        
        if account.long_description:
            explanation_parts.append(f"\n{account.long_description}")
        
        if account.normal_balance:
            explanation_parts.append(f"\nNormal Balance: {account.normal_balance}")
        
        if account.fs_mapping:
            explanation_parts.append(f"Appears on: {account.fs_mapping}")
        
        if account.tags:
            explanation_parts.append(f"\nRelated Concepts: {', '.join(account.tags)}")
        
        if account.default_vendors:
            explanation_parts.append(f"\nCommonly used for: {', '.join(account.default_vendors[:5])}")
        
        return "\n".join(explanation_parts)
