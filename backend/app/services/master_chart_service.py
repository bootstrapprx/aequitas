"""
Master Chart Service
Provides easy access to the master chart of accounts for AI and application use.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.models.master_account import MasterAccount


class MasterChartService:
    """
    Service for interacting with the Master Chart of Accounts.
    Optimized for AI (DEXTER) interaction and intelligent account suggestion.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_accounts(self, include_headers: bool = False) -> List[MasterAccount]:
        """
        Get all master accounts.
        
        Args:
            include_headers: If True, include header accounts. Default False (detail accounts only).
        
        Returns:
            List of MasterAccount objects
        """
        query = self.db.query(MasterAccount)
        if not include_headers:
            query = query.filter(MasterAccount.type == 'D')
        return query.order_by(MasterAccount.code).all()
    
    def get_accounts_for_ai(self, include_headers: bool = False) -> List[Dict[str, Any]]:
        """
        Get all master accounts in AI-friendly format for DEXTER.
        
        Args:
            include_headers: If True, include header accounts. Default False.
        
        Returns:
            List of simplified dicts optimized for AI processing
        """
        accounts = self.get_all_accounts(include_headers=include_headers)
        return [account.to_ai_context() for account in accounts]
    
    def get_account_by_code(self, code: str) -> Optional[MasterAccount]:
        """
        Get a specific account by its code.
        
        Args:
            code: Account code (e.g., "10100")
        
        Returns:
            MasterAccount object or None if not found
        """
        return self.db.query(MasterAccount).filter(MasterAccount.code == code).first()
    
    def get_accounts_by_category(self, category: str) -> List[MasterAccount]:
        """
        Get all accounts in a specific category.
        
        Args:
            category: Category name (e.g., "Asset", "Expense", "Revenue")
        
        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.category == category,
                MasterAccount.type == 'D'
            )
        ).order_by(MasterAccount.code).all()
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[MasterAccount]:
        """
        Search master accounts by keywords.
        Searches in description, long_description, tags, and default_vendors.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results to return
        
        Returns:
            List of matching MasterAccount objects
        """
        if not keywords:
            return []
        
        # Get all detail accounts
        accounts = self.db.query(MasterAccount).filter(MasterAccount.type == 'D').all()
        
        # Filter by keywords using the model's method
        matches = [acc for acc in accounts if acc.matches_keywords(keywords)]
        
        # Return top matches (could add scoring later)
        return matches[:limit]
    
    def search_by_vendor(self, vendor_name: str) -> List[MasterAccount]:
        """
        Find accounts associated with a specific vendor.
        Useful for automatic account suggestion based on vendor.
        
        Args:
            vendor_name: Vendor name to search for
        
        Returns:
            List of matching MasterAccount objects
        """
        if not vendor_name:
            return []
        
        # Get accounts with vendor mappings
        accounts = self.db.query(MasterAccount).filter(
            MasterAccount.default_vendors.isnot(None)
        ).all()
        
        # Filter by vendor using the model's method
        matches = [acc for acc in accounts if acc.matches_vendor(vendor_name)]
        
        return matches
    
    def suggest_accounts(
        self, 
        description: str, 
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest accounts based on transaction description and optional vendor.
        This is the main method DEXTER should use for account suggestions.
        
        Args:
            description: Transaction description
            vendor: Optional vendor name
            amount: Optional transaction amount (for future heuristics)
            limit: Maximum number of suggestions to return
        
        Returns:
            List of suggested accounts with confidence scores
        """
        suggestions = []
        
        # 1. If vendor is provided, check vendor mappings first
        if vendor:
            vendor_matches = self.search_by_vendor(vendor)
            for acc in vendor_matches[:limit]:
                suggestions.append({
                    "account": acc.to_ai_context(),
                    "confidence": 0.9,  # High confidence for vendor matches
                    "reason": f"Vendor '{vendor}' commonly uses this account",
                    "match_type": "vendor"
                })
        
        # 2. Search by keywords from description
        if len(suggestions) < limit:
            keywords = description.lower().split()
            keyword_matches = self.search_by_keywords(keywords, limit=limit*2)
            
            for acc in keyword_matches:
                # Skip if already in suggestions
                if any(s["account"]["code"] == acc.code for s in suggestions):
                    continue
                
                suggestions.append({
                    "account": acc.to_ai_context(),
                    "confidence": 0.7,  # Medium confidence for keyword matches
                    "reason": f"Description matches account keywords",
                    "match_type": "keyword"
                })
                
                if len(suggestions) >= limit:
                    break
        
        # 3. Sort by confidence and return top results
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:limit]
    
    def get_category_summary(self) -> Dict[str, int]:
        """
        Get a summary of accounts by category.
        
        Returns:
            Dict mapping category names to account counts
        """
        from sqlalchemy import func
        
        results = self.db.query(
            MasterAccount.category,
            func.count(MasterAccount.id)
        ).filter(
            MasterAccount.type == 'D'
        ).group_by(
            MasterAccount.category
        ).all()
        
        return {category: count for category, count in results}
    
    def get_accounts_by_fs_mapping(self, fs_type: str) -> List[MasterAccount]:
        """
        Get accounts by financial statement mapping.
        
        Args:
            fs_type: "Balance Sheet" or "Income Statement"
        
        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.fs_mapping == fs_type,
                MasterAccount.type == 'D'
            )
        ).order_by(MasterAccount.code).all()
    
    def get_expense_accounts_with_vendors(self) -> List[MasterAccount]:
        """
        Get all expense accounts that have vendor mappings.
        Useful for building vendor-to-account rules.
        
        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.category == 'Expense',
                MasterAccount.default_vendors.isnot(None),
                MasterAccount.type == 'D'
            )
        ).order_by(MasterAccount.code).all()
    
    def get_accounts_by_normal_balance(self, balance_type: str) -> List[MasterAccount]:
        """
        Get accounts by normal balance type.
        
        Args:
            balance_type: "Debit" or "Credit"
        
        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.normal_balance == balance_type,
                MasterAccount.type == 'D'
            )
        ).order_by(MasterAccount.code).all()
    
    def get_master_chart_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the master chart.
        Useful for dashboard and reporting.
        
        Returns:
            Dict with various statistics
        """
        total_accounts = self.db.query(MasterAccount).count()
        headers = self.db.query(MasterAccount).filter(MasterAccount.type == 'H').count()
        details = self.db.query(MasterAccount).filter(MasterAccount.type == 'D').count()
        
        with_vendors = self.db.query(MasterAccount).filter(
            MasterAccount.default_vendors.isnot(None)
        ).count()
        
        with_tags = self.db.query(MasterAccount).filter(
            MasterAccount.tags.isnot(None)
        ).count()
        
        category_summary = self.get_category_summary()
        
        return {
            "total_accounts": total_accounts,
            "header_accounts": headers,
            "detail_accounts": details,
            "accounts_with_vendors": with_vendors,
            "accounts_with_tags": with_tags,
            "category_breakdown": category_summary,
            "enrichment_coverage": {
                "vendor_mappings": f"{(with_vendors/details*100):.1f}%" if details > 0 else "0%",
                "ai_tags": f"{(with_tags/details*100):.1f}%" if details > 0 else "0%",
            }
        }
