"""
Dexter Observer Service

Read-only service for detecting patterns, anomalies, and insights.

Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.

CRITICAL CONSTRAINTS:
- Read-only access (uses DexterReadOnlySession)
- No write operations
- No autonomous actions
- All outputs are advisory
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.db.models.journal_entry import JournalEntry
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.company_account import CompanyAccount
from app.db.models.fiscal_period import FiscalPeriod


class DexterInsightType:
    """Insight type constants."""
    RECURRING_PATTERN = "recurring_pattern"
    ANOMALY = "anomaly"
    MISSING_ENTRY = "missing_entry"
    ACCOUNT_USAGE = "account_usage"
    BALANCE_TREND = "balance_trend"


class DexterObserverService:
    """
    Read-only service for detecting patterns and surfacing insights.

    All methods are read-only. No data is mutated.
    Service must be instantiated with DexterReadOnlySession.

    Usage:
        from app.db.dexter_session import get_dexter_db

        db = next(get_dexter_db())
        service = DexterObserverService(db)
        insights = service.get_insights_for_company(company_id)
    """

    def __init__(self, db: Session):
        """
        Initialize with read-only database session.

        Args:
            db: DexterReadOnlySession (enforces read-only)
        """
        self.db = db

    # ========================================================================
    # PATTERN DETECTION
    # ========================================================================

    def detect_recurring_patterns(
        self,
        company_id: UUID,
        lookback_months: int = 3
    ) -> List[Dict]:
        """
        Detect recurring journal entry patterns.

        Looks for entries with:
        - Similar descriptions (fuzzy match)
        - Regular frequency (monthly, weekly)
        - Similar amounts

        Returns:
            List of pattern observations (read-only)

        Example:
            [
                {
                    "type": "recurring_pattern",
                    "description": "AWS Hosting",
                    "frequency": "monthly",
                    "avg_amount": 485.00,
                    "account_code": "60000",
                    "vendor": "AWS",
                    "last_occurrence": "2025-11-05"
                }
            ]
        """
        patterns = []

        # Query posted entries from last N months
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_months * 30)

        entries = self.db.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True,
            JournalEntry.entry_date >= cutoff_date
        ).all()

        # Group by description (normalized)
        description_groups = {}
        for entry in entries:
            # Normalize description (lowercase, strip)
            normalized = entry.description.lower().strip()

            if normalized not in description_groups:
                description_groups[normalized] = []

            description_groups[normalized].append(entry)

        # Find patterns (3+ occurrences)
        for desc, entry_list in description_groups.items():
            if len(entry_list) >= 3:
                # Calculate average amount (sum of debits or credits)
                amounts = []
                account_codes = set()

                for entry in entry_list:
                    for line in entry.lines:
                        amounts.append(abs(float(line.debit or 0) + float(line.credit or 0)))
                        account_codes.add(line.company_account.code if line.company_account else None)

                avg_amount = sum(amounts) / len(amounts) if amounts else 0

                patterns.append({
                    "type": DexterInsightType.RECURRING_PATTERN,
                    "description": entry_list[0].description,  # Original case
                    "frequency": "monthly" if len(entry_list) >= lookback_months else "periodic",
                    "occurrences": len(entry_list),
                    "avg_amount": round(avg_amount, 2),
                    "account_codes": list(account_codes),
                    "last_occurrence": max(e.entry_date for e in entry_list).isoformat()
                })

        return patterns

    def detect_anomalies(
        self,
        company_id: UUID,
        account_code: Optional[str] = None,
        threshold_stddev: float = 2.0
    ) -> List[Dict]:
        """
        Detect unusual transactions (amounts significantly above/below average).

        Uses standard deviation to detect outliers.

        Args:
            company_id: Company to analyze
            account_code: Optional filter for specific account
            threshold_stddev: Number of std deviations to flag (default: 2.0)

        Returns:
            List of anomaly observations (read-only)

        Example:
            [
                {
                    "type": "anomaly",
                    "account_code": "62000",
                    "account_name": "Utilities Expense",
                    "amount": 450.00,
                    "avg_amount": 120.00,
                    "std_dev": 25.00,
                    "deviation_factor": 13.2,
                    "entry_date": "2025-12-15",
                    "entry_id": "uuid"
                }
            ]
        """
        anomalies = []

        # Query posted entries with amounts
        query = self.db.query(JournalEntryLine).join(
            JournalEntry
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True
        )

        if account_code:
            query = query.join(CompanyAccount).filter(
                CompanyAccount.code == account_code
            )

        lines = query.all()

        if not lines:
            return []

        # Group by account
        account_groups = {}
        for line in lines:
            if not line.company_account:
                continue

            acc_code = line.company_account.code
            if acc_code not in account_groups:
                account_groups[acc_code] = {
                    "name": line.company_account.name,
                    "amounts": [],
                    "lines": []
                }

            amount = abs(float(line.debit or 0) + float(line.credit or 0))
            account_groups[acc_code]["amounts"].append(amount)
            account_groups[acc_code]["lines"].append((amount, line))

        # Detect outliers per account
        for acc_code, data in account_groups.items():
            amounts = data["amounts"]

            if len(amounts) < 3:
                continue  # Need at least 3 data points

            # Calculate mean and std dev
            mean = sum(amounts) / len(amounts)
            variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5

            if std_dev == 0:
                continue  # All amounts identical

            # Find outliers
            for amount, line in data["lines"]:
                deviation = abs(amount - mean) / std_dev

                if deviation >= threshold_stddev:
                    anomalies.append({
                        "type": DexterInsightType.ANOMALY,
                        "account_code": acc_code,
                        "account_name": data["name"],
                        "amount": round(amount, 2),
                        "avg_amount": round(mean, 2),
                        "std_dev": round(std_dev, 2),
                        "deviation_factor": round(deviation, 1),
                        "entry_date": line.journal_entry.entry_date.isoformat(),
                        "entry_id": str(line.journal_entry.id),
                        "description": line.journal_entry.description
                    })

        return anomalies

    def detect_missing_entries(
        self,
        company_id: UUID,
        current_period_id: UUID
    ) -> List[Dict]:
        """
        Detect expected entries that are missing this period.

        Compares current period to previous periods to find
        recurring entries that haven't occurred yet.

        Args:
            company_id: Company to analyze
            current_period_id: Current fiscal period

        Returns:
            List of missing entry observations (read-only)

        Example:
            [
                {
                    "type": "missing_entry",
                    "expected_description": "Payroll",
                    "typical_day_of_month": 15,
                    "avg_amount": 5000.00,
                    "account_code": "61000",
                    "last_occurrence": "2025-11-15"
                }
            ]
        """
        missing = []

        # Get current period
        current_period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == current_period_id
        ).first()

        if not current_period:
            return []

        # Get previous periods (last 3)
        previous_periods = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.company_id == company_id,
            FiscalPeriod.end_date < current_period.start_date
        ).order_by(desc(FiscalPeriod.end_date)).limit(3).all()

        if not previous_periods:
            return []

        # Get recurring patterns from previous periods
        for period in previous_periods:
            entries = self.db.query(JournalEntry).filter(
                JournalEntry.company_id == company_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= period.start_date,
                JournalEntry.entry_date <= period.end_date
            ).all()

            # Check if similar entries exist in current period
            for entry in entries:
                # Look for matching description in current period
                current_match = self.db.query(JournalEntry).filter(
                    JournalEntry.company_id == company_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= current_period.start_date,
                    JournalEntry.entry_date <= current_period.end_date,
                    func.lower(JournalEntry.description).like(f"%{entry.description.lower()}%")
                ).first()

                if not current_match:
                    # Missing entry detected
                    # Calculate average amount
                    amounts = []
                    for line in entry.lines:
                        amounts.append(abs(float(line.debit or 0) + float(line.credit or 0)))

                    avg_amount = sum(amounts) / len(amounts) if amounts else 0

                    missing.append({
                        "type": DexterInsightType.MISSING_ENTRY,
                        "expected_description": entry.description,
                        "typical_day_of_month": entry.entry_date.day,
                        "avg_amount": round(avg_amount, 2),
                        "last_occurrence": entry.entry_date.isoformat()
                    })

        return missing

    def analyze_account_usage(
        self,
        company_id: UUID,
        period_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Analyze which accounts are used most frequently.

        Args:
            company_id: Company to analyze
            period_id: Optional fiscal period filter

        Returns:
            List of account usage statistics (read-only)

        Example:
            [
                {
                    "type": "account_usage",
                    "account_code": "60000",
                    "account_name": "General Operating Expenses",
                    "transaction_count": 12,
                    "total_debits": 4500.00,
                    "total_credits": 0.00
                }
            ]
        """
        query = self.db.query(
            CompanyAccount.code,
            CompanyAccount.name,
            func.count(JournalEntryLine.id).label('transaction_count'),
            func.sum(JournalEntryLine.debit).label('total_debits'),
            func.sum(JournalEntryLine.credit).label('total_credits')
        ).join(
            JournalEntryLine
        ).join(
            JournalEntry
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True
        )

        if period_id:
            period = self.db.query(FiscalPeriod).filter(FiscalPeriod.id == period_id).first()
            if period:
                query = query.filter(
                    JournalEntry.entry_date >= period.start_date,
                    JournalEntry.entry_date <= period.end_date
                )

        results = query.group_by(
            CompanyAccount.code,
            CompanyAccount.name
        ).order_by(
            desc('transaction_count')
        ).limit(10).all()

        usage = []
        for row in results:
            usage.append({
                "type": DexterInsightType.ACCOUNT_USAGE,
                "account_code": row.code,
                "account_name": row.name,
                "transaction_count": row.transaction_count,
                "total_debits": float(row.total_debits or 0),
                "total_credits": float(row.total_credits or 0)
            })

        return usage

    # ========================================================================
    # AGGREGATED INSIGHTS
    # ========================================================================

    def get_insights_for_company(
        self,
        company_id: UUID,
        current_period_id: Optional[UUID] = None,
        max_insights: int = 10
    ) -> Dict:
        """
        Get all insights for a company.

        Combines patterns, anomalies, missing entries, and usage stats.

        Args:
            company_id: Company to analyze
            current_period_id: Optional current fiscal period
            max_insights: Maximum number of insights to return

        Returns:
            Dictionary of insights by type (read-only)

        Example:
            {
                "patterns": [...],
                "anomalies": [...],
                "missing_entries": [...],
                "account_usage": [...],
                "total_count": 15
            }
        """
        insights = {
            "patterns": self.detect_recurring_patterns(company_id),
            "anomalies": self.detect_anomalies(company_id),
            "missing_entries": [],
            "account_usage": self.analyze_account_usage(company_id, current_period_id)
        }

        if current_period_id:
            insights["missing_entries"] = self.detect_missing_entries(
                company_id,
                current_period_id
            )

        # Count total insights
        total = (
            len(insights["patterns"]) +
            len(insights["anomalies"]) +
            len(insights["missing_entries"])
        )

        insights["total_count"] = total

        # Limit total insights
        if total > max_insights:
            # Prioritize: anomalies > missing > patterns
            insights["patterns"] = insights["patterns"][:3]
            insights["anomalies"] = insights["anomalies"][:4]
            insights["missing_entries"] = insights["missing_entries"][:3]

        return insights
