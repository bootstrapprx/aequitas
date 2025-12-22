# Chart Template Seeding Guide

This guide explains **three approaches** to seed and manage dynamic chart templates in Aequitas, with proper permission controls.

---

## Permission Model

All three approaches implement the same permission model:

| User Type | Permissions |
|-----------|-------------|
| **Regular Users** | Can **ADD** custom accounts to their company chart (where `allow_custom_children=True`)<br>**CANNOT** delete or modify mandatory accounts (`is_mandatory=True`) |
| **Superusers** | Can **ADD and SUBTRACT** (full CRUD on templates and all accounts)<br>Can create/modify/delete templates via admin API |

### Template Account Flags

- `is_mandatory`: If `true`, users **cannot delete** this account from their company chart
- `allow_custom_children`: If `true`, users **can add** custom child accounts under this account
- `sort_order`: Display order in the template
- `required_module`: Optional; account only created if company has this module enabled

---

## Approach 1: Python Script-Based Seeding (Recommended for Initial Setup)

**Best for:** Initial database setup, development, staging environments

### Overview

Use a Python script to programmatically seed templates with full control over account structure and relationships.

### Files

- **Script:** [`backend/app/data/seed_chart_templates.py`](backend/app/data/seed_chart_templates.py)

### Features

- ✅ Programmatic template creation with full Python control
- ✅ Deterministic and repeatable
- ✅ Easy to version control
- ✅ Checks for duplicates before inserting
- ✅ Clear console output with progress indicators

### Usage

```bash
# 1. Ensure master accounts are seeded first
cd backend
python app/data/seed_enriched_master_chart.py

# 2. Run the template seeder
python app/data/seed_chart_templates.py
```

### Output Example

```
============================================================
  SEEDING CHART TEMPLATES
============================================================

✓ Found 345 master accounts

Seeding templates...

✓ Created template: US GAAP Standard (ID: ...)
  ✓ Added 30 accounts to template
✓ Created template: US GAAP Simplified (ID: ...)
  ✓ Added 9 accounts to template
✓ Created template: IFRS Standard (ID: ...)
  ✓ Added 14 accounts to template

============================================================
  SEEDING COMPLETE
============================================================

✓ Successfully seeded 3 chart templates
✓ Templates are ready for use in onboarding

Templates created:
  1. US GAAP Standard (US) - v2025.1
  2. US GAAP Simplified (US) - v2025.1
  3. IFRS Standard (INTL) - v2025.1
```

### Templates Included

1. **US GAAP Standard** - Comprehensive template for US businesses (30 accounts)
2. **US GAAP Simplified** - Minimal template for startups and small businesses (9 accounts)
3. **IFRS Standard** - International template for IFRS jurisdictions (14 accounts)

### Customization

Edit [`backend/app/data/seed_chart_templates.py`](backend/app/data/seed_chart_templates.py):

```python
def seed_custom_template(db: Session) -> ChartTemplate:
    """Add your custom template here."""
    template = ChartTemplate(
        name="My Custom Template",
        jurisdiction="CA",
        version="1.0",
        description="Custom template for Canadian businesses",
        is_active=True
    )
    db.add(template)
    db.flush()

    # Define accounts...
    account_definitions = [
        ("1.10.10.10", "Cash", True, True, 1, None),
        # ... more accounts
    ]

    # Create template accounts...
    # (see existing functions for pattern)

    return template
```

---

## Approach 2: API-Based Dynamic Template Management (Recommended for Production)

**Best for:** Production environments, dynamic template management, superuser administration

### Overview

RESTful API endpoints allow superusers to create, update, and delete templates programmatically or via admin UI.

### Files

- **API Router:** [`backend/app/api/v1/admin/template_management.py`](backend/app/api/v1/admin/template_management.py)

### Features

- ✅ Full CRUD operations via REST API
- ✅ Superuser-only access (enforced via `check_superuser` dependency)
- ✅ Swagger/OpenAPI documentation
- ✅ Perfect for building admin UIs
- ✅ Validation and error handling built-in

### Setup

#### 1. Register the Router

Edit [`backend/app/main.py`](backend/app/main.py):

```python
# Add import
from app.api.v1.admin import template_management

# Register router (inside app initialization)
app.include_router(
    template_management.router,
    prefix="/api/v1/admin",
    tags=["admin", "templates"]
)
```

#### 2. Create Admin Router Package

Create [`backend/app/api/v1/admin/__init__.py`](backend/app/api/v1/admin/__init__.py):

```python
"""Admin API endpoints."""
```

### API Endpoints

All endpoints require **superuser authentication** (`Authorization: Bearer <token>`).

#### Template CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/templates` | Create a new template |
| `PUT` | `/api/v1/admin/templates/{template_id}` | Update template metadata |
| `DELETE` | `/api/v1/admin/templates/{template_id}` | Soft-delete template (set `is_active=False`) |

#### Template Account Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/templates/{template_id}/accounts` | List all accounts in template |
| `POST` | `/api/v1/admin/templates/{template_id}/accounts` | Add account to template |
| `PATCH` | `/api/v1/admin/templates/{template_id}/accounts/{account_id}` | Update account settings |
| `DELETE` | `/api/v1/admin/templates/{template_id}/accounts/{account_id}` | Remove account from template |

### Usage Examples

#### Create a Template

```bash
curl -X POST http://localhost:8000/api/v1/admin/templates \
  -H "Authorization: Bearer <superuser_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Canadian GAAP Standard",
    "jurisdiction": "CA",
    "version": "2025.1",
    "description": "Standard chart for Canadian businesses",
    "is_active": true
  }'
```

#### Add Account to Template

```bash
curl -X POST http://localhost:8000/api/v1/admin/templates/{template_id}/accounts \
  -H "Authorization: Bearer <superuser_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "master_account_id": "uuid-of-master-account",
    "code": "1.10.10.10",
    "name": "Cash",
    "is_mandatory": true,
    "allow_custom_children": true,
    "sort_order": 1
  }'
```

#### Update Template Account Settings

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/templates/{template_id}/accounts/{account_id} \
  -H "Authorization: Bearer <superuser_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_mandatory": false,
    "allow_custom_children": true,
    "sort_order": 10
  }'
```

#### Delete Template (Soft Delete)

```bash
curl -X DELETE http://localhost:8000/api/v1/admin/templates/{template_id} \
  -H "Authorization: Bearer <superuser_token>"
```

### Integration with Frontend

Build an admin UI in [`frontend/src/pages/admin/TemplateManagement.tsx`](frontend/src/pages/admin/TemplateManagement.tsx) that calls these endpoints.

---

## Approach 3: JSON Configuration Files with Hot-Reload (Recommended for Version Control)

**Best for:** Git-based workflows, easy editing, non-technical template management

### Overview

Define templates in JSON files that are automatically loaded into the database on startup.

### Files

- **Service:** [`backend/app/services/template_loader.py`](backend/app/services/template_loader.py)
- **Templates Directory:** [`backend/app/data/templates/`](backend/app/data/templates/)
- **Example Templates:**
  - [`us_gaap_standard.json`](backend/app/data/templates/us_gaap_standard.json)
  - [`us_gaap_simplified.json`](backend/app/data/templates/us_gaap_simplified.json)
  - [`ifrs_standard.json`](backend/app/data/templates/ifrs_standard.json)

### Features

- ✅ Easy to edit (JSON format)
- ✅ Version control friendly (Git-friendly text files)
- ✅ Hot-reload support (changes reflected on restart)
- ✅ Non-technical users can create templates
- ✅ Automatic sync on application startup

### JSON Structure

```json
{
  "template": {
    "name": "Template Name",
    "jurisdiction": "US",
    "version": "2025.1",
    "description": "Template description",
    "is_active": true
  },
  "accounts": [
    {
      "code": "1.10.10.10",
      "name": "Cash",
      "is_mandatory": true,
      "allow_custom_children": true,
      "sort_order": 1
    },
    {
      "code": "1.10.20.10",
      "name": "Accounts Receivable",
      "is_mandatory": true,
      "allow_custom_children": true,
      "sort_order": 2
    }
  ]
}
```

### Setup

#### 1. Enable Auto-Loading on Startup

Edit [`backend/app/main.py`](backend/app/main.py):

```python
from app.services.template_loader import TemplateLoader
from app.db.session import SessionLocal

@app.on_event("startup")
async def load_templates():
    """Load chart templates from JSON files on startup."""
    db = SessionLocal()
    try:
        loader = TemplateLoader(db)
        loader.sync_all_templates()
    finally:
        db.close()
```

#### 2. Restart the Application

```bash
make restart
# or
docker compose -f docker-compose.dev.yml restart backend
```

### Manual Sync

You can also manually sync templates without restarting:

```bash
cd backend
python app/services/template_loader.py
```

### Creating New Templates

1. Create a new JSON file in [`backend/app/data/templates/`](backend/app/data/templates/)
2. Follow the JSON structure above
3. Restart the backend (or run manual sync)
4. Template will be available in onboarding

### Example: Create UK GAAP Template

Create [`backend/app/data/templates/uk_gaap_standard.json`](backend/app/data/templates/uk_gaap_standard.json):

```json
{
  "template": {
    "name": "UK GAAP Standard",
    "jurisdiction": "UK",
    "version": "2025.1",
    "description": "Standard Chart of Accounts for UK businesses following UK GAAP (FRS 102)",
    "is_active": true
  },
  "accounts": [
    {
      "code": "1.10.10.10",
      "name": "Bank Current Account",
      "is_mandatory": true,
      "allow_custom_children": true,
      "sort_order": 1
    },
    {
      "code": "1.10.20.10",
      "name": "Trade Debtors",
      "is_mandatory": true,
      "allow_custom_children": true,
      "sort_order": 2
    },
    {
      "code": "2.10.10.10",
      "name": "Trade Creditors",
      "is_mandatory": true,
      "allow_custom_children": true,
      "sort_order": 10
    }
  ]
}
```

Then restart or run:

```bash
python app/services/template_loader.py
```

---

## Comparison of Approaches

| Feature | Approach 1<br>Python Script | Approach 2<br>API Management | Approach 3<br>JSON Files |
|---------|---------------------|----------------------|---------------------|
| **Ease of Use** | Medium (requires Python knowledge) | Easy (via API/UI) | Very Easy (JSON editing) |
| **Version Control** | ✅ Git-friendly Python | ❌ Database-only | ✅ Git-friendly JSON |
| **Dynamic Updates** | ❌ Requires re-run | ✅ Real-time via API | ⚠️ Requires restart |
| **Superuser Control** | ❌ Terminal access needed | ✅ Full API control | ⚠️ File system access |
| **Non-Technical Editing** | ❌ Python required | ✅ Via admin UI | ✅ JSON editing |
| **Automation** | ✅ CI/CD pipelines | ✅ API automation | ✅ File-based automation |
| **Best For** | Initial setup, dev | Production, admin UI | Git workflows, easy updates |

---

## Recommended Workflow

### Development Environment

1. **Initial Setup:** Use **Approach 1** (Python script) to seed base templates
2. **Iterative Changes:** Use **Approach 3** (JSON files) for quick template edits
3. **Commit:** Commit JSON files to Git for version control

### Production Environment

1. **Deployment:** Use **Approach 3** (JSON files) to load templates on startup
2. **Administration:** Expose **Approach 2** (API endpoints) for superuser template management
3. **Build Admin UI:** Create frontend admin panel that calls Approach 2 APIs

---

## Testing Templates

### Verify Templates Are Loaded

```bash
curl http://localhost:8000/api/v1/templates
```

Expected response:

```json
[
  {
    "id": "uuid",
    "name": "US GAAP Standard",
    "jurisdiction": "US",
    "version": "2025.1",
    "description": "Standard Chart of Accounts...",
    "is_active": true,
    "account_count": 30
  },
  {
    "id": "uuid",
    "name": "US GAAP Simplified",
    "jurisdiction": "US",
    "version": "2025.1",
    "description": "Simplified Chart of Accounts...",
    "is_active": true,
    "account_count": 9
  }
]
```

### Test Onboarding Flow

1. Navigate to: [http://localhost:5173/onboarding](http://localhost:5173/onboarding)
2. Complete Step 1 (Company Details)
3. Step 2 should now show the available templates
4. Select a template and continue

---

## Troubleshooting

### No Templates Showing in Onboarding

**Cause:** Templates not seeded in database

**Solution:**

```bash
# Check if templates exist
curl http://localhost:8000/api/v1/templates

# If empty, run seeder
cd backend
python app/data/seed_chart_templates.py
# or
python app/services/template_loader.py
```

### "Master account not found" Errors

**Cause:** Master chart not seeded

**Solution:**

```bash
cd backend
python app/data/seed_enriched_master_chart.py
# Then re-run template seeder
```

### Templates Not Updating

**Cause:** Using JSON approach but not restarting backend

**Solution:**

```bash
make restart
# or manually sync
python app/services/template_loader.py
```

---

## Permission Enforcement

### How Mandatory Accounts Work

When a user selects a template during onboarding:

1. **Template Application:** All template accounts (mandatory and optional) are copied to the company's chart
2. **Deletion Protection:** Accounts with `is_mandatory=True` **cannot be deleted** by regular users
3. **Custom Children:** If `allow_custom_children=True`, users **can add** sub-accounts under that account
4. **Superuser Override:** Superusers can delete any account, including mandatory ones

### Implementation

**Backend Enforcement** (in account deletion endpoint):

```python
@router.delete("/companies/{company_id}/accounts/{account_id}")
def delete_company_account(
    company_id: UUID,
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(CompanyAccount).filter(
        CompanyAccount.id == account_id,
        CompanyAccount.company_id == company_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if account is mandatory
    if account.template_account_id:
        template_account = db.query(ChartTemplateAccount).filter(
            ChartTemplateAccount.id == account.template_account_id
        ).first()

        if template_account and template_account.is_mandatory:
            # Only superusers can delete mandatory accounts
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete mandatory template account. Contact administrator."
                )

    # Proceed with deletion...
    db.delete(account)
    db.commit()
```

---

## Next Steps

1. **Choose your approach** based on your workflow (see comparison table)
2. **Seed initial templates** using your chosen approach
3. **Test onboarding flow** to verify templates appear correctly
4. **Customize templates** to match your jurisdiction requirements
5. **(Optional) Build admin UI** for Approach 2 if needed

---

## Questions?

- **Issue Tracker:** [https://github.com/anthropics/aequitas/issues](https://github.com/anthropics/aequitas/issues)
- **Documentation:** See [`CLAUDE.md`](CLAUDE.md) for full project architecture

---

**Author:** Claude Code
**Last Updated:** 2025-12-22
**Version:** 1.0
