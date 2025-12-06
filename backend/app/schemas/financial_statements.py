from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID
from typing import List, Optional
from decimal import Decimal


# ===== Balance Sheet Schemas =====

class BalanceSheetAccount(BaseModel):
    """Schema for a single account in balance sheet"""
    code: str
    description: str
    amount: Decimal
    level: int
    is_header: bool = False


class BalanceSheetSection(BaseModel):
    """Schema for a section in balance sheet (Assets, Liabilities, Equity)"""
    name: str
    accounts: List[BalanceSheetAccount]
    total: Decimal


class BalanceSheetResponse(BaseModel):
    """Schema for balance sheet report"""
    company_id: UUID
    company_name: str
    as_of_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    is_balanced: bool


# ===== Income Statement (P&L) Schemas =====

class IncomeStatementAccount(BaseModel):
    """Schema for a single account in income statement"""
    code: str
    description: str
    amount: Decimal
    level: int
    is_header: bool = False


class IncomeStatementSection(BaseModel):
    """Schema for a section in income statement"""
    name: str
    accounts: List[IncomeStatementAccount]
    total: Decimal


class IncomeStatementResponse(BaseModel):
    """Schema for income statement (P&L) report"""
    company_id: UUID
    company_name: str
    period_start: date
    period_end: date
    revenue: IncomeStatementSection
    cost_of_goods_sold: IncomeStatementSection
    expenses: IncomeStatementSection
    other_income: IncomeStatementSection
    total_revenue: Decimal
    total_cogs: Decimal
    gross_profit: Decimal
    gross_profit_margin: Optional[Decimal] = None
    total_expenses: Decimal
    total_other_income: Decimal
    net_income: Decimal
    net_profit_margin: Optional[Decimal] = None


# ===== Cash Flow Statement Schemas =====

class CashFlowAccount(BaseModel):
    """Schema for a single account in cash flow statement"""
    code: str
    description: str
    amount: Decimal
    level: int
    is_header: bool = False


class CashFlowSection(BaseModel):
    """Schema for a section in cash flow statement"""
    name: str
    accounts: List[CashFlowAccount]
    total: Decimal


class CashFlowStatementResponse(BaseModel):
    """Schema for cash flow statement (indirect method)"""
    company_id: UUID
    company_name: str
    period_start: date
    period_end: date
    operating_activities: CashFlowSection
    investing_activities: CashFlowSection
    financing_activities: CashFlowSection
    net_cash_from_operations: Decimal
    net_cash_from_investing: Decimal
    net_cash_from_financing: Decimal
    net_change_in_cash: Decimal
    beginning_cash_balance: Decimal
    ending_cash_balance: Decimal


# ===== Consolidated Financial Statements =====

class ConsolidatedBalanceSheet(BaseModel):
    """Schema for consolidated balance sheet across multiple companies"""
    company_ids: List[UUID]
    as_of_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    eliminations: Optional[Decimal] = Field(None, description="Inter-company eliminations")


class ConsolidatedIncomeStatement(BaseModel):
    """Schema for consolidated income statement across multiple companies"""
    company_ids: List[UUID]
    period_start: date
    period_end: date
    revenue: IncomeStatementSection
    cost_of_goods_sold: IncomeStatementSection
    expenses: IncomeStatementSection
    other_income: IncomeStatementSection
    total_revenue: Decimal
    total_cogs: Decimal
    gross_profit: Decimal
    total_expenses: Decimal
    total_other_income: Decimal
    net_income: Decimal
    eliminations: Optional[Decimal] = Field(None, description="Inter-company eliminations")


# ===== Financial Metrics =====

class FinancialMetrics(BaseModel):
    """Schema for key financial metrics"""
    company_id: UUID
    period_start: date
    period_end: date

    # Profitability ratios
    gross_profit_margin: Optional[Decimal] = None
    net_profit_margin: Optional[Decimal] = None
    return_on_assets: Optional[Decimal] = None
    return_on_equity: Optional[Decimal] = None

    # Liquidity ratios
    current_ratio: Optional[Decimal] = None
    quick_ratio: Optional[Decimal] = None

    # Leverage ratios
    debt_to_equity: Optional[Decimal] = None
    debt_to_assets: Optional[Decimal] = None

    # Efficiency ratios
    asset_turnover: Optional[Decimal] = None
