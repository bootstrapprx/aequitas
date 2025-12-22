"""
Template Loader Service - Approach 3: JSON-based configuration with hot-reload

This service loads chart templates from JSON files in the templates directory
and syncs them to the database.

PERMISSION MODEL:
- Regular users: Can ADD accounts to their company chart (not subtract/delete mandatory accounts)
- Superusers: Can ADD and SUBTRACT via admin API

FEATURES:
- Hot-reload: Reads JSON files from disk on startup
- Version control: JSON files can be tracked in Git
- Easy editing: Non-technical users can edit JSON files
- Automatic sync: Updates database on application startup

Directory: backend/app/data/templates/
File format: {template_name}.json

JSON Structure:
{
  "template": {
    "name": "Template Name",
    "jurisdiction": "US",
    "version": "1.0",
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
    }
  ]
}

Usage:
    from app.services.template_loader import TemplateLoader

    # In main.py startup event:
    @app.on_event("startup")
    async def load_templates():
        db = SessionLocal()
        loader = TemplateLoader(db)
        loader.sync_all_templates()
        db.close()
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount
from app.db.models.master_account import MasterAccount


class TemplateLoader:
    """Loads and syncs chart templates from JSON files to database."""

    def __init__(self, db: Session):
        self.db = db
        self.templates_dir = Path(__file__).parent.parent / "data" / "templates"

        # Ensure templates directory exists
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created templates directory: {self.templates_dir}")

    def list_template_files(self) -> List[Path]:
        """List all JSON template files in the templates directory."""
        if not self.templates_dir.exists():
            return []
        return list(self.templates_dir.glob("*.json"))

    def load_template_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a single template JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {file_path.name}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            return {}

    def get_master_account_by_code(self, code: str) -> MasterAccount | None:
        """Fetch master account by code."""
        return self.db.query(MasterAccount).filter(MasterAccount.code == code).first()

    def sync_template(self, template_data: Dict[str, Any]) -> ChartTemplate | None:
        """
        Sync a single template from JSON data to the database.

        Creates or updates the template and its accounts.
        """
        if not template_data or "template" not in template_data:
            print("❌ Invalid template data: missing 'template' key")
            return None

        template_info = template_data["template"]
        accounts_data = template_data.get("accounts", [])

        # Required fields
        name = template_info.get("name")
        jurisdiction = template_info.get("jurisdiction")
        version = template_info.get("version")

        if not all([name, jurisdiction, version]):
            print(f"❌ Invalid template: missing required fields (name, jurisdiction, version)")
            return None

        # Check if template exists
        existing_template = self.db.query(ChartTemplate).filter(
            ChartTemplate.name == name,
            ChartTemplate.jurisdiction == jurisdiction
        ).first()

        if existing_template:
            # Update existing template
            existing_template.version = version
            existing_template.description = template_info.get("description")
            existing_template.is_active = template_info.get("is_active", True)
            template = existing_template
            print(f"  ↻ Updated existing template: {name}")
        else:
            # Create new template
            template = ChartTemplate(
                name=name,
                jurisdiction=jurisdiction,
                version=version,
                description=template_info.get("description"),
                is_active=template_info.get("is_active", True)
            )
            self.db.add(template)
            self.db.flush()  # Get the ID
            print(f"  ✓ Created new template: {name}")

        # Sync accounts
        existing_codes = set()
        if existing_template:
            # Get existing account codes for this template
            existing_accounts = self.db.query(ChartTemplateAccount).filter(
                ChartTemplateAccount.template_id == template.id
            ).all()
            existing_codes = {acc.code for acc in existing_accounts}

        added_count = 0
        skipped_count = 0
        updated_count = 0

        for acc_data in accounts_data:
            code = acc_data.get("code")
            name_acc = acc_data.get("name")

            if not code or not name_acc:
                print(f"    ⚠ Skipping account: missing code or name")
                continue

            # Find master account
            master_account = self.get_master_account_by_code(code)
            if not master_account:
                print(f"    ⚠ Skipping account {code}: master account not found")
                continue

            # Check if account already exists in template
            existing_acc = self.db.query(ChartTemplateAccount).filter(
                ChartTemplateAccount.template_id == template.id,
                ChartTemplateAccount.code == code
            ).first()

            if existing_acc:
                # Update existing account
                existing_acc.name = name_acc
                existing_acc.is_mandatory = acc_data.get("is_mandatory", False)
                existing_acc.allow_custom_children = acc_data.get("allow_custom_children", False)
                existing_acc.sort_order = acc_data.get("sort_order", 0)
                updated_count += 1
            else:
                # Create new account
                template_account = ChartTemplateAccount(
                    template_id=template.id,
                    master_account_id=master_account.id,
                    parent_id=None,  # Flat structure for simplicity
                    code=code,
                    name=name_acc,
                    is_mandatory=acc_data.get("is_mandatory", False),
                    allow_custom_children=acc_data.get("allow_custom_children", False),
                    sort_order=acc_data.get("sort_order", 0),
                    required_module=None
                )
                self.db.add(template_account)
                added_count += 1

        print(f"    Accounts: +{added_count} added, ~{updated_count} updated")

        return template

    def sync_all_templates(self) -> int:
        """
        Sync all template JSON files to the database.

        Returns the number of templates synced.
        """
        print("\n" + "="*60)
        print("  SYNCING CHART TEMPLATES FROM JSON FILES")
        print("="*60 + "\n")

        # Check for master accounts
        master_count = self.db.query(MasterAccount).count()
        if master_count == 0:
            print("❌ ERROR: No master accounts found!")
            print("   Please run the master chart seeder first:")
            print("   python app/data/seed_enriched_master_chart.py\n")
            return 0

        print(f"✓ Found {master_count} master accounts")

        # Find all template files
        template_files = self.list_template_files()

        if not template_files:
            print(f"⚠ No template files found in {self.templates_dir}")
            print(f"  Create JSON files in this directory to define templates.\n")
            return 0

        print(f"✓ Found {len(template_files)} template file(s)\n")

        synced_count = 0

        for template_file in template_files:
            print(f"Processing: {template_file.name}")
            template_data = self.load_template_from_file(template_file)

            if not template_data:
                continue

            template = self.sync_template(template_data)
            if template:
                synced_count += 1

        # Commit all changes
        try:
            self.db.commit()
            print("\n" + "="*60)
            print("  SYNC COMPLETE")
            print("="*60)
            print(f"\n✓ Successfully synced {synced_count} template(s)\n")
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ ERROR during commit: {str(e)}\n")
            raise

        return synced_count

    def reload_template(self, template_name: str) -> ChartTemplate | None:
        """
        Reload a specific template from its JSON file.

        Useful for hot-reloading during development.
        """
        template_file = self.templates_dir / f"{template_name}.json"

        if not template_file.exists():
            print(f"❌ Template file not found: {template_file}")
            return None

        print(f"Reloading template: {template_name}")
        template_data = self.load_template_from_file(template_file)

        if not template_data:
            return None

        template = self.sync_template(template_data)

        if template:
            try:
                self.db.commit()
                print(f"✓ Successfully reloaded template: {template_name}\n")
            except Exception as e:
                self.db.rollback()
                print(f"❌ ERROR during commit: {str(e)}\n")
                raise

        return template


# Standalone script entry point
if __name__ == "__main__":
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        loader = TemplateLoader(db)
        loader.sync_all_templates()
    finally:
        db.close()
