# Master Chart of Accounts - Implementation Guide

## Overview

The Aequitas Master Chart of Accounts is a comprehensive, AI-ready, IFRS/US-GAAP compliant chart with **345 accounts** designed to be the cornerstone of the accounting system.

**Key Features:**
- ✅ **345 accounts** (7 headers + 338 details)
- ✅ **IFRS/US-GAAP compliant** with regulatory references
- ✅ **AI-optimized** for DEXTER interaction
- ✅ **Vendor mappings** for 59 expense accounts
- ✅ **Semantic tags** for intelligent classification
- ✅ **Persistent memory** loaded by default on startup

---

## Architecture

### 1. Data Model (`master_account.py`)

**Core Fields:**
- `code`: Unique 5-digit account code
- `description`: Short account name
- `type`: "H" (Header) or "D" (Detail)
- `category`: Asset, Liability, Equity, Revenue, Expense, COGS, Other
- `level`: Hierarchical level (1-3)
- `parent_code`: Parent account code for hierarchy

**Enriched Fields (AI-Ready):**
- `long_description`: Professional IFRS/GAAP explanation
- `fs_mapping`: "Balance Sheet" or "Income Statement"
- `tags`: Array of keywords for AI classification
- `default_vendors`: Array of common vendor names
- `regulatory_mapping`: JSON with IFRS/IPSAS/ASC references
- `normal_balance`: "Debit" or "Credit"
- `cash_flow_classification`: "Operating", "Investing", or "Financing"
- `cost_center`: Default cost center assignment

**AI Methods:**
```python
account.to_ai_context()          # Simplified dict for AI
account.matches_keywords(keywords) # Keyword matching
account.matches_vendor(vendor)    # Vendor matching
```

### 2. Seed Script (`seed_enriched_master_chart.py`)

**Functions:**
- `load_enriched_master_chart(db, force_reload=False)` - Load all 345 accounts
- `get_master_chart_as_objects(db)` - Get Python objects
- `get_master_chart_for_ai(db)` - Get AI-friendly format
- `search_accounts_by_keywords(db, keywords)` - Keyword search
- `search_accounts_by_vendor(db, vendor_name)` - Vendor search

**Usage:**
```bash
# Load master chart
python -m app.data.seed_enriched_master_chart

# Or from code
from app.data.seed_enriched_master_chart import load_enriched_master_chart
load_enriched_master_chart(db)
```

### 3. Master Chart Service (`master_chart_service.py`)

**Main Service Class:**
```python
from app.services.master_chart_service import MasterChartService

service = MasterChartService(db)

# Get all accounts
accounts = service.get_all_accounts(include_headers=False)

# Get AI-friendly format
ai_accounts = service.get_accounts_for_ai()

# Search by keywords
matches = service.search_by_keywords(['software', 'computer'])

# Search by vendor
matches = service.search_by_vendor('AWS')

# Suggest accounts for transaction
suggestions = service.suggest_accounts(
    description="Monthly AWS hosting fees",
    vendor="Amazon Web Services",
    limit=5
)

# Get statistics
stats = service.get_master_chart_stats()
```

### 4. DEXTER Integration (`dexter/master_chart_integration.py`)

**DEXTER-Specific Functions:**
```python
from app.services.dexter.master_chart_integration import DexterMasterChartIntegration

dexter_mc = DexterMasterChartIntegration(db)

# Get context for AI prompts
context = dexter_mc.get_master_chart_context()

# Suggest accounts for transaction
suggestions = dexter_mc.suggest_accounts_for_transaction(
    description="Office supplies from Staples",
    vendor="Staples",
    limit=5
)

# Build comprehensive AI prompt
prompt_context = dexter_mc.build_ai_prompt_context(
    transaction_description="Paid for cloud storage",
    vendor="Dropbox"
)

# Explain an account
explanation = dexter_mc.explain_account("60100")

# Ingest master chart into vector store
await dexter_mc.ingest_master_chart_for_learning(learning_engine)
```

---

## Default Loading

The master chart is **automatically loaded** on application startup via `init_db.py`:

```python
# backend/app/db/init_db.py
def init_db(db: Session) -> None:
    # 1. Initialize superuser
    # 2. Initialize Master Chart (if not exists)
    master_chart_count = db.query(MasterAccount).count()
    if master_chart_count == 0:
        load_enriched_master_chart(db)
```

**This ensures:**
- ✅ Master chart always available
- ✅ No manual seeding required
- ✅ Persistent memory for DEXTER
- ✅ Consistent data across environments

---

## Database Migration

Run the migration to add enriched fields:

```bash
# Using psql
psql -U postgres -d aequitas -f backend/MIGRATION_ENRICHED_MASTER_CHART.sql

# Or using Alembic (if configured)
alembic revision --autogenerate -m "Add enriched master chart fields"
alembic upgrade head
```

---

## Data Files

**Location:** `backend/app/data/`

| File | Size | Description |
|------|------|-------------|
| `enriched_master_chart.csv` | 822 KB | Complete enriched master chart |
| `enriched_master_chart.json` | 975 KB | JSON format for programmatic use |
| `us_gaap_master_chart.csv` | 543 KB | Basic master chart (legacy) |
| `us_gaap_master_chart.json` | 608 KB | Basic JSON format (legacy) |

**CSV Columns:**
- code, description, start_date, end_date, type, parent_code, level, category, notes
- long_description, fs_mapping, tags, default_vendors, regulatory_mapping
- normal_balance, cash_flow_classification, cost_center

---

## Statistics

### Account Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Asset | 144 | 41.7% |
| Expense | 60 | 17.4% |
| Liability | 56 | 16.2% |
| Cost of Goods Sold | 44 | 12.8% |
| Equity | 16 | 4.6% |
| Revenue | 13 | 3.8% |
| Other | 5 | 1.4% |
| **Total Details** | **338** | **98.0%** |
| Headers | 7 | 2.0% |
| **Grand Total** | **345** | **100%** |

### Enrichment Coverage

- **Vendor Mappings:** 59 accounts (17.1%)
- **AI Tags:** 345 accounts (100%)
- **Long Descriptions:** 338 accounts (100%)
- **Regulatory References:** 345 accounts (100%)

### Financial Statement Mapping

- **Balance Sheet:** 219 accounts (63.3%)
- **Income Statement:** 126 accounts (36.5%)

---

## Usage Examples

### Example 1: Get Expense Accounts

```python
from app.services.master_chart_service import MasterChartService

service = MasterChartService(db)
expense_accounts = service.get_accounts_by_category("Expense")

for acc in expense_accounts[:5]:
    print(f"{acc.code}: {acc.description}")
```

### Example 2: Find Account for Vendor

```python
# User enters: "Paid $500 to AWS for hosting"
suggestions = service.suggest_accounts(
    description="hosting fees",
    vendor="AWS",
    amount=500.00
)

for sug in suggestions:
    acc = sug['account']
    print(f"{acc['code']}: {acc['description']} ({sug['confidence']:.0%})")
```

### Example 3: DEXTER Chat Context

```python
from app.services.dexter.master_chart_integration import DexterMasterChartIntegration

dexter_mc = DexterMasterChartIntegration(db)

# User asks: "What account should I use for software subscriptions?"
context = dexter_mc.build_ai_prompt_context(
    transaction_description="software subscription"
)

# Feed context to DEXTER's LLM
prompt = f"""
{context}

User Question: What account should I use for software subscriptions?
Dexter:
"""
```

### Example 4: Vendor-Based Rules

```python
# Get all vendor-to-account mappings
vendor_map = dexter_mc.get_vendor_account_mappings()

# Example output:
# {
#   "AWS": ["60100", "60150"],
#   "Microsoft": ["60100", "60150"],
#   "Salesforce": ["60100"],
#   ...
# }

# Use for automatic categorization
vendor = "AWS"
if vendor in vendor_map:
    suggested_codes = vendor_map[vendor]
    print(f"Suggested accounts for {vendor}: {suggested_codes}")
```

---

## Testing

### Run Seed Script with Tests

```bash
cd backend
python -m app.data.seed_enriched_master_chart
```

**Expected Output:**
```
Loading enriched master chart from .../enriched_master_chart.csv...
Found 345 accounts in CSV...
  Loaded 50 accounts...
  Loaded 100 accounts...
  ...
  Loaded 345 accounts...
  First pass complete: 345 accounts loaded, 0 skipped
  Setting parent relationships...
  Set 338 parent relationships

✓ Successfully loaded 345 accounts

============================================================
ENRICHED MASTER CHART SUMMARY
============================================================
  Header accounts: 7
  Detail accounts: 338
  Total accounts: 345

  Accounts by Category:
    Asset: 144
    Expense: 60
    Liability: 56
    Cost of Goods Sold: 44
    Equity: 16
    Revenue: 13
    Other: 5

  Enrichment Coverage:
    Accounts with vendor mappings: 59
    Accounts with AI tags: 345
    Accounts with long descriptions: 338
============================================================

============================================================
TESTING AI INTERACTION FUNCTIONS
============================================================

1. Testing keyword search for 'software'...
   Found 5 matching accounts:
   - 60100: Computer and Internet Expenses
   - 60150: Software and Technology
   ...

2. Testing vendor search for 'AWS'...
   Found 2 matching accounts:
   - 60100: Computer and Internet Expenses
     Vendors: AWS, Google Cloud, Microsoft Azure
   ...

3. Testing AI context generation...
   Generated AI context for 345 accounts
   Sample account:
   {
     "code": "10100",
     "description": "Cash",
     "long_description": "...",
     ...
   }

============================================================
AI INTERACTION TESTS COMPLETE
============================================================
```

### Test Master Chart Service

```python
from app.services.master_chart_service import MasterChartService
from app.db.session import SessionLocal

db = SessionLocal()
service = MasterChartService(db)

# Test 1: Get statistics
stats = service.get_master_chart_stats()
assert stats['total_accounts'] == 345
assert stats['detail_accounts'] == 338

# Test 2: Search by keywords
matches = service.search_by_keywords(['software'])
assert len(matches) > 0

# Test 3: Search by vendor
matches = service.search_by_vendor('AWS')
assert len(matches) > 0

# Test 4: Suggest accounts
suggestions = service.suggest_accounts(
    description="cloud hosting",
    vendor="AWS"
)
assert len(suggestions) > 0
assert suggestions[0]['confidence'] > 0.5

print("✓ All tests passed!")
```

---

## Troubleshooting

### Issue: Master chart not loading

**Solution:**
```bash
# Check if accounts exist
psql -U postgres -d aequitas -c "SELECT COUNT(*) FROM master_accounts;"

# If 0, manually load
cd backend
python -m app.data.seed_enriched_master_chart
```

### Issue: Missing enriched fields

**Solution:**
```bash
# Run migration
psql -U postgres -d aequitas -f backend/MIGRATION_ENRICHED_MASTER_CHART.sql

# Reload data
python -m app.data.seed_enriched_master_chart --force-reload
```

### Issue: DEXTER not finding accounts

**Solution:**
```python
# Rebuild vector embeddings
from app.services.dexter.master_chart_integration import DexterMasterChartIntegration
from app.services.dexter.learning_engine import LearningEngine

dexter_mc = DexterMasterChartIntegration(db)
learning_engine = LearningEngine(db)

await dexter_mc.ingest_master_chart_for_learning(learning_engine)
```

---

## Best Practices

### 1. Always Use the Service Layer

❌ **Don't:**
```python
accounts = db.query(MasterAccount).all()
```

✅ **Do:**
```python
from app.services.master_chart_service import MasterChartService
service = MasterChartService(db)
accounts = service.get_all_accounts()
```

### 2. Use AI-Friendly Methods for DEXTER

❌ **Don't:**
```python
accounts = [acc.as_dict() for acc in accounts]
```

✅ **Do:**
```python
accounts = service.get_accounts_for_ai()
# or
accounts = [acc.to_ai_context() for acc in accounts]
```

### 3. Leverage Vendor Mappings

```python
# When user enters a transaction with a vendor
if vendor_name:
    suggestions = service.suggest_accounts(
        description=description,
        vendor=vendor_name  # This boosts confidence!
    )
```

### 4. Cache Master Chart in Memory (Optional)

```python
# For high-performance scenarios
class MasterChartCache:
    _accounts = None
    
    @classmethod
    def get_accounts(cls, db):
        if cls._accounts is None:
            service = MasterChartService(db)
            cls._accounts = service.get_all_accounts()
        return cls._accounts
```

---

## Roadmap

### Phase 1: ✅ Complete
- [x] Enhanced data model
- [x] Enriched CSV with 345 accounts
- [x] Seed script with AI functions
- [x] Master Chart Service
- [x] DEXTER Integration
- [x] Default loading on startup

### Phase 2: 🚧 In Progress
- [ ] Vector embeddings for all accounts
- [ ] Machine learning for confidence scoring
- [ ] Historical learning from user corrections

### Phase 3: 📋 Planned
- [ ] Multi-language support
- [ ] Industry-specific chart variants
- [ ] Custom account creation with AI suggestions
- [ ] Real-time account suggestion API

---

## Support

For questions or issues:
1. Check this documentation
2. Review `ENRICHED_CHART_README.md`
3. Run test suite: `python -m app.data.seed_enriched_master_chart`
4. Open GitHub issue with `master-chart` label

---

**Master Chart of Accounts** - The cornerstone of Aequitas ⚖️
