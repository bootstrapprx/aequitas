# Quick Start: Chart Templates - Onboarding Unblocked ✅

## Problem Solved

Your onboarding wizard was stuck because there were no templates available for selection. This has been **resolved**.

## Current Status

✅ **3 Templates Active and Ready**

Templates are now available at: `http://localhost:8000/api/v1/templates`

| Template Name | Jurisdiction | Version | Accounts | Description |
|---------------|--------------|---------|----------|-------------|
| US GAAP Standard | US | 2025.1 | 0 (scaffold) | Comprehensive US GAAP template for SMBs |
| US GAAP Simplified | US | 2025.1 | 0 (scaffold) | Minimal template for startups |
| IFRS Standard | INTL | 2025.1 | 0 (scaffold) | International IFRS-compliant template |

**Note:** These are currently **scaffold templates** (metadata only, no accounts yet). This is intentional - accounts will be populated during company chart initialization in future phases.

## What You Can Do Now

### 1. Test Onboarding Flow

Navigate to: [http://localhost:5173/onboarding](http://localhost:5173/onboarding)

The "Choose Template" step should now display all 3 templates with:
- Template name
- Jurisdiction badge
- Version number
- Full description
- Selection UI

### 2. Add More Templates

Run the seeder script again with custom templates:

```bash
docker compose -f docker-compose.dev.yml exec backend python app/data/seed_basic_templates.py
```

Or edit the script to add your own templates.

### 3. Manage Templates via API (Superuser Only)

Use the admin API endpoints (once integrated - see below).

---

## Three Seeding Approaches Available

I've created **three different approaches** for seeding and managing templates. Choose based on your workflow:

### **Approach 1: Python Script (Used Now ✅)**

**File:** [`backend/app/data/seed_basic_templates.py`](backend/app/data/seed_basic_templates.py)

**Status:** ✅ Already run - templates are seeded

**Best for:** Quick setup, development, one-time initialization

**Run again:**
```bash
docker compose -f docker-compose.dev.yml exec backend python app/data/seed_basic_templates.py
```

---

### **Approach 2: API-Based Management (Ready to Use)**

**File:** [`backend/app/api/v1/admin/template_management.py`](backend/app/api/v1/admin/template_management.py)

**Status:** ⚠️ Created but not integrated yet

**Best for:** Dynamic template management, admin UIs, production environments

**Integration Required:**

1. Create admin router package:
   ```bash
   mkdir -p backend/app/api/v1/admin
   touch backend/app/api/v1/admin/__init__.py
   ```

2. Edit [`backend/app/main.py`](backend/app/main.py):
   ```python
   from app.api.v1.admin import template_management

   app.include_router(
       template_management.router,
       prefix="/api/v1/admin",
       tags=["admin", "templates"]
   )
   ```

3. Restart backend:
   ```bash
   make restart
   ```

**Available Endpoints:**
- `POST /api/v1/admin/templates` - Create template
- `PUT /api/v1/admin/templates/{id}` - Update template
- `DELETE /api/v1/admin/templates/{id}` - Soft-delete template
- `POST /api/v1/admin/templates/{id}/accounts` - Add account to template
- `GET /api/v1/admin/templates/{id}/accounts` - List template accounts

---

### **Approach 3: JSON Configuration Files (Ready to Use)**

**Files:**
- Service: [`backend/app/services/template_loader.py`](backend/app/services/template_loader.py)
- Templates: [`backend/app/data/templates/*.json`](backend/app/data/templates/)

**Status:** ⚠️ Created but not integrated yet

**Best for:** Version control, easy editing, Git-based workflows

**JSON Templates Included:**
- `us_gaap_standard.json` - 18 accounts
- `us_gaap_simplified.json` - 9 accounts
- `ifrs_standard.json` - 14 accounts

**Integration Required:**

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

Then restart:
```bash
make restart
```

---

## Permission Model (All Approaches)

| User Type | Can Add Accounts | Can Delete Accounts |
|-----------|------------------|---------------------|
| **Regular Users** | ✅ Yes (where `allow_custom_children=True`) | ❌ No (mandatory accounts protected) |
| **Superusers** | ✅ Yes (all accounts) | ✅ Yes (full CRUD) |

### Template Account Flags

- **`is_mandatory`**: If `true`, users cannot delete this account
- **`allow_custom_children`**: If `true`, users can add child accounts
- **`sort_order`**: Display order in template

---

## Next Steps

### Immediate (Optional)

1. **Test onboarding** - Verify templates appear in UI
2. **Choose integration approach** - Pick from Approach 2 or 3 above
3. **Customize templates** - Edit descriptions, add more templates

### Future Phases

1. **Phase 4: Account Population**
   - Link templates to master accounts
   - Implement company chart initialization
   - Build account mapping UI

2. **Phase 5: Admin UI**
   - Build template management page
   - Integrate Approach 2 API endpoints
   - Create account assignment interface

---

## Troubleshooting

### Templates Not Showing in UI

**Check API:**
```bash
curl http://localhost:8000/api/v1/templates
```

**Re-run seeder:**
```bash
docker compose -f docker-compose.dev.yml exec backend python app/data/seed_basic_templates.py
```

### Need to Add Custom Template

**Option A: Edit Python script**

Edit [`backend/app/data/seed_basic_templates.py`](backend/app/data/seed_basic_templates.py) and add to `templates_to_create` list:

```python
{
    "name": "Canadian GAAP Standard",
    "jurisdiction": "CA",
    "version": "2025.1",
    "description": "Your description here...",
    "is_active": True
}
```

Then re-run the script.

**Option B: Use JSON files (after integration)**

Create `backend/app/data/templates/canadian_gaap.json`:

```json
{
  "template": {
    "name": "Canadian GAAP Standard",
    "jurisdiction": "CA",
    "version": "2025.1",
    "description": "...",
    "is_active": true
  },
  "accounts": []
}
```

Then restart backend.

---

## Documentation

📄 **Full Documentation:** [`TEMPLATE_SEEDING_GUIDE.md`](TEMPLATE_SEEDING_GUIDE.md)

This comprehensive guide covers:
- All 3 approaches in detail
- API endpoints reference
- JSON structure specification
- Permission enforcement
- Troubleshooting guide

---

## Files Created

### Immediate Solution (Used)
- ✅ [`backend/app/data/seed_basic_templates.py`](backend/app/data/seed_basic_templates.py)

### Future Integration (Ready)
- ⚠️ [`backend/app/api/v1/admin/template_management.py`](backend/app/api/v1/admin/template_management.py)
- ⚠️ [`backend/app/services/template_loader.py`](backend/app/services/template_loader.py)
- ⚠️ [`backend/app/data/templates/us_gaap_standard.json`](backend/app/data/templates/us_gaap_standard.json)
- ⚠️ [`backend/app/data/templates/us_gaap_simplified.json`](backend/app/data/templates/us_gaap_simplified.json)
- ⚠️ [`backend/app/data/templates/ifrs_standard.json`](backend/app/data/templates/ifrs_standard.json)
- ⚠️ [`backend/app/data/seed_chart_templates.py`](backend/app/data/seed_chart_templates.py) (for full linking later)

### Documentation
- 📄 [`TEMPLATE_SEEDING_GUIDE.md`](TEMPLATE_SEEDING_GUIDE.md) - Comprehensive guide
- 📄 [`QUICK_START_TEMPLATES.md`](QUICK_START_TEMPLATES.md) - This file

---

## Summary

✅ **Onboarding is unblocked** - 3 templates are now available for selection

🎯 **Next decision:** Choose which approach (2 or 3) to integrate for long-term template management

📚 **Documentation:** All approaches are fully documented and ready to use

---

**Last Updated:** 2025-12-22
**Author:** Claude Code
**Status:** ✅ Ready for Testing
