"""
Seed Basic Chart Templates - Simplified Approach

This script creates template scaffolds WITHOUT linking to master accounts.
Master account linkage happens during the mapping phase after companies
select their template.

This solves the immediate onboarding blocker by providing templates for selection.

Usage:
    docker compose -f docker-compose.dev.yml exec backend python app/data/seed_basic_templates.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.chart_template import ChartTemplate
import uuid


def seed_template_scaffolds(db: Session):
    """
    Seed basic template scaffolds for onboarding selection.

    These templates are metadata-only and don't contain accounts yet.
    Accounts will be created during company chart initialization.
    """

    print("\n" + "="*60)
    print("  SEEDING BASIC CHART TEMPLATES (SCAFFOLDS)")
    print("="*60 + "\n")

    templates_to_create = [
        {
            "name": "US GAAP Standard",
            "jurisdiction": "US",
            "version": "2025.1",
            "description": (
                "Standard Chart of Accounts for US businesses following Generally Accepted Accounting Principles (GAAP). "
                "Includes comprehensive account structure for balance sheet and income statement reporting. "
                "Suitable for small to medium-sized businesses across various industries."
            ),
            "is_active": True
        },
        {
            "name": "US GAAP Simplified",
            "jurisdiction": "US",
            "version": "2025.1",
            "description": (
                "Simplified Chart of Accounts for small businesses, startups, and sole proprietors. "
                "Contains essential accounts for basic bookkeeping and financial reporting. "
                "Ideal for businesses with straightforward transactions."
            ),
            "is_active": True
        },
        {
            "name": "IFRS Standard",
            "jurisdiction": "INTL",
            "version": "2025.1",
            "description": (
                "International Financial Reporting Standards (IFRS) compliant Chart of Accounts. "
                "Suitable for businesses operating in jurisdictions that follow IFRS, including "
                "the UK, EU, Australia, Canada, and many other countries."
            ),
            "is_active": True
        }
    ]

    created_count = 0
    updated_count = 0

    for template_data in templates_to_create:
        # Check if template already exists
        existing = db.query(ChartTemplate).filter(
            ChartTemplate.name == template_data["name"],
            ChartTemplate.jurisdiction == template_data["jurisdiction"]
        ).first()

        if existing:
            # Update existing template
            existing.version = template_data["version"]
            existing.description = template_data["description"]
            existing.is_active = template_data["is_active"]
            print(f"↻ Updated: {template_data['name']} (ID: {existing.id})")
            updated_count += 1
        else:
            # Create new template
            template = ChartTemplate(
                id=uuid.uuid4(),
                name=template_data["name"],
                jurisdiction=template_data["jurisdiction"],
                version=template_data["version"],
                description=template_data["description"],
                is_active=template_data["is_active"]
            )
            db.add(template)
            print(f"✓ Created: {template_data['name']}")
            created_count += 1

    # Commit changes
    try:
        db.commit()
        print("\n" + "="*60)
        print("  SEEDING COMPLETE")
        print("="*60)
        print(f"\n✓ Created: {created_count} template(s)")
        print(f"↻ Updated: {updated_count} template(s)")
        print(f"✓ Templates are ready for onboarding\n")

        # Print summary
        all_templates = db.query(ChartTemplate).filter(ChartTemplate.is_active == True).all()
        print("Active templates:")
        for i, tmpl in enumerate(all_templates, 1):
            print(f"  {i}. {tmpl.name} ({tmpl.jurisdiction}) - v{tmpl.version}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}\n")
        raise


def main():
    """Main entry point."""
    db = SessionLocal()
    try:
        seed_template_scaffolds(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
