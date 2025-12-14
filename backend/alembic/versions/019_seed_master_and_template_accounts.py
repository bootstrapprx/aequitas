"""Seed master_accounts and chart_template_accounts tables

Revision ID: 019
Revises: 018
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 1 of 5

PURPOSE:
Populate master chart of accounts and chart template accounts:
1. Load US-GAAP master chart (345 accounts) into master_accounts
2. Fix duplicate code issue (7 headers have duplicate codes in details)
3. Establish parent-child relationships using parent_id
4. Seed chart_template_accounts for all active templates
5. Mark mandatory accounts (Asset, Liability, Equity headers + critical details)

BACKGROUND:
Phase 2A created the template structure (migrations 014-018).
However, master_accounts and chart_template_accounts remain empty.

This migration seeds both tables from the enriched master chart CSV,
handling the data quality issue where header codes are duplicated in detail accounts.

BREAKING: No - data seeding only
REQUIRES: Migration 018 complete, enriched_master_chart.csv available

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: Template Account Seeding
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import csv
import os
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Seed master_accounts and chart_template_accounts tables.

    STRATEGY:
    1. Load enriched master chart CSV
    2. Fix duplicate codes (detail accounts conflicting with headers)
    3. Insert master accounts in two passes (headers first, then details)
    4. Establish parent relationships using parent_id
    5. Seed template accounts for each active template
    """

    print("=" * 80)
    print("MIGRATION 019: Seeding Master Chart and Template Accounts")
    print("=" * 80)

    connection = op.get_bind()

    # ========================================================================
    # STEP 1: Load and validate CSV data
    # ========================================================================

    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'data')
    csv_path = os.path.join(data_dir, 'enriched_master_chart.csv')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Master chart CSV not found at {csv_path}")

    print(f"Loading master chart from: {csv_path}")

    accounts_data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        accounts_data = list(reader)

    print(f"  Loaded {len(accounts_data)} accounts from CSV")

    # ========================================================================
    # STEP 2: Fix duplicate code issue
    # ========================================================================
    # Headers: 10000, 20000, 30000, 40000, 50000, 60000, 80000
    # Detail accounts with same codes will be renumbered
    # ========================================================================

    print("  Fixing duplicate codes...")

    # Separate headers and details
    headers = [acc for acc in accounts_data if acc['type'] == 'Header']
    details = [acc for acc in accounts_data if acc['type'] == 'Detail']

    print(f"  - Headers: {len(headers)}")
    print(f"  - Details: {len(details)}")

    # Build set of header codes
    header_codes = {h['code'] for h in headers}

    # Fix detail accounts that conflict with header codes
    # Strategy: Use hierarchical code based on position
    # E.g., 10000 (Header) -> detail account becomes 1.10.10.10
    code_mapping = {}  # old_code -> new_code
    next_detail_code = {}  # category -> next available code

    for detail in details:
        old_code = detail['code']

        if old_code in header_codes:
            # This detail account conflicts with a header
            # Generate unique code based on category and sequence
            category_code = old_code[0]  # First digit (1, 2, 3, 4, 5, 6, 8)

            if category_code not in next_detail_code:
                next_detail_code[category_code] = 1

            # Generate hierarchical code: X.YY.ZZ.AA format
            new_code = f"{category_code}.{next_detail_code[category_code]:02d}.10.10"
            code_mapping[old_code] = new_code
            detail['original_code'] = old_code
            detail['code'] = new_code
            next_detail_code[category_code] += 1
        elif old_code in code_mapping.values():
            # This detail code conflicts with a previously generated code
            # Increment sequence
            category_code = old_code[0]
            if category_code not in next_detail_code:
                next_detail_code[category_code] = 1

            new_code = f"{category_code}.{next_detail_code[category_code]:02d}.10.10"
            code_mapping[old_code] = new_code
            detail['original_code'] = old_code
            detail['code'] = new_code
            next_detail_code[category_code] += 1

    print(f"  - Fixed {len(code_mapping)} duplicate codes")

    # Update parent_code references for affected accounts
    for detail in details:
        if detail.get('parent_code') and detail['parent_code'] in code_mapping:
            detail['parent_code'] = code_mapping[detail['parent_code']]

    # Combine back
    all_accounts = headers + details

    # ========================================================================
    # STEP 3: Insert master accounts (headers first)
    # ========================================================================
    print("  Inserting master accounts...")

    # Create mapping of code -> UUID for parent relationships
    account_id_map = {}

    # Insert headers first (so they exist when details reference them)
    headers_inserted = 0
    for header in headers:
        account_id = str(uuid.uuid4())
        account_id_map[header['code']] = account_id

        # Parse tags (may be JSON array string or empty)
        tags = []
        if header.get('tags'):
            tag_str = header['tags'].strip('[]').replace('"', '').replace("'", "")
            tags = [t.strip() for t in tag_str.split(',') if t.strip()]

        # Parse default_vendors
        vendors = []
        if header.get('default_vendors'):
            vendor_str = header['default_vendors'].strip('[]').replace('"', '').replace("'", "")
            vendors = [v.strip() for v in vendor_str.split(',') if v.strip()]

        connection.execute(sa.text("""
            INSERT INTO master_accounts (
                id, code, description, start_date, end_date, type, parent_code, level,
                category, notes, long_description, fs_mapping, tags, default_vendors,
                normal_balance, version, parent_id
            ) VALUES (
                :id, :code, :description, :start_date, :end_date, :type, :parent_code, :level,
                :category, :notes, :long_description, :fs_mapping, :tags, :default_vendors,
                :normal_balance, :version, NULL
            )
        """), {
            'id': account_id,
            'code': header['code'],
            'description': header['description'],
            'start_date': datetime(2024, 1, 1).date(),
            'end_date': None,
            'type': 'H',
            'parent_code': header.get('parent_code') or None,
            'level': 1,
            'category': header.get('category', header['description']),
            'notes': None,
            'long_description': header.get('long_description'),
            'fs_mapping': header.get('fs_mapping'),
            'tags': tags if tags else None,
            'default_vendors': vendors if vendors else None,
            'normal_balance': header.get('normal_balance'),
            'version': '2024.1'
        })
        headers_inserted += 1

    print(f"  - Inserted {headers_inserted} header accounts")

    # Insert details (with parent_id references)
    details_inserted = 0
    for detail in details:
        account_id = str(uuid.uuid4())
        account_id_map[detail['code']] = account_id

        # Resolve parent_id
        parent_id = None
        if detail.get('parent_code'):
            parent_id = account_id_map.get(detail['parent_code'])

        # Parse tags
        tags = []
        if detail.get('tags'):
            tag_str = detail['tags'].strip('[]').replace('"', '').replace("'", "")
            tags = [t.strip() for t in tag_str.split(',') if t.strip()]

        # Parse vendors
        vendors = []
        if detail.get('default_vendors'):
            vendor_str = detail['default_vendors'].strip('[]').replace('"', '').replace("'", "")
            vendors = [v.strip() for v in vendor_str.split(',') if v.strip()]

        connection.execute(sa.text("""
            INSERT INTO master_accounts (
                id, code, description, start_date, end_date, type, parent_code, level,
                category, notes, long_description, fs_mapping, tags, default_vendors,
                normal_balance, version, parent_id
            ) VALUES (
                :id, :code, :description, :start_date, :end_date, :type, :parent_code, :level,
                :category, :notes, :long_description, :fs_mapping, :tags, :default_vendors,
                :normal_balance, :version, :parent_id
            )
        """), {
            'id': account_id,
            'code': detail['code'],
            'description': detail['description'],
            'start_date': datetime(2024, 1, 1).date(),
            'end_date': None,
            'type': 'D',
            'parent_code': detail.get('parent_code') or None,
            'level': 2,  # Simplified: all details are level 2
            'category': detail.get('category', 'General'),
            'notes': detail.get('original_code', None),  # Store original code if changed
            'long_description': detail.get('long_description'),
            'fs_mapping': detail.get('fs_mapping'),
            'tags': tags if tags else None,
            'default_vendors': vendors if vendors else None,
            'normal_balance': detail.get('normal_balance'),
            'version': '2024.1',
            'parent_id': parent_id
        })
        details_inserted += 1

    print(f"  - Inserted {details_inserted} detail accounts")
    print(f"  - Total master accounts: {headers_inserted + details_inserted}")

    # ========================================================================
    # STEP 4: Seed chart_template_accounts for active templates
    # ========================================================================
    print("  Seeding chart template accounts...")

    # Get all active templates
    templates_result = connection.execute(sa.text("""
        SELECT id, name, jurisdiction, version
        FROM chart_templates
        WHERE is_active = true
        ORDER BY jurisdiction, version
    """))

    templates = templates_result.fetchall()

    total_template_accounts_created = 0

    for template in templates:
        template_id = template[0]
        template_name = template[1]
        jurisdiction = template[2]
        version = template[3]

        print(f"  - Seeding template: {template_name} ({jurisdiction} {version})")

        # Determine which master accounts to include
        # For US-GAAP templates: all accounts
        # For IFRS: might need filtering (future enhancement)
        # For SMB: subset of accounts (future enhancement)

        if 'SMB' in version:
            # Small business: essential accounts only (~30-50)
            master_accounts_to_include = connection.execute(sa.text("""
                SELECT id, code, description, type, category, normal_balance, parent_id
                FROM master_accounts
                WHERE type = 'H'  -- All headers
                   OR code IN (
                       SELECT code FROM master_accounts
                       WHERE type = 'D'
                       AND (
                           description ILIKE '%cash%'
                           OR description ILIKE '%receivable%'
                           OR description ILIKE '%payable%'
                           OR description ILIKE '%retained%'
                           OR description ILIKE '%revenue%'
                           OR description ILIKE '%expense%'
                           OR description ILIKE '%inventory%'
                       )
                       LIMIT 43  -- 7 headers + 43 details = 50 total
                   )
                ORDER BY type DESC, code
            """))
        else:
            # Full template: all accounts
            master_accounts_to_include = connection.execute(sa.text("""
                SELECT id, code, description, type, category, normal_balance, parent_id
                FROM master_accounts
                ORDER BY type DESC, code
            """))

        accounts_for_template = master_accounts_to_include.fetchall()

        # Create template_account_id mapping
        template_account_map = {}
        sort_order = 0

        for master_acc in accounts_for_template:
            master_id = master_acc[0]
            code = master_acc[1]
            description = master_acc[2]
            acc_type = master_acc[3]
            category = master_acc[4]
            normal_balance = master_acc[5]
            master_parent_id = master_acc[6]

            # Resolve parent_id for template account (if parent exists in template)
            template_parent_id = None
            if master_parent_id and master_parent_id in [a[0] for a in accounts_for_template]:
                # Find the template account that corresponds to this master parent
                template_parent_id_result = connection.execute(sa.text("""
                    SELECT id FROM chart_template_accounts
                    WHERE template_id = :template_id
                      AND master_account_id = :master_parent_id
                """), {'template_id': template_id, 'master_parent_id': master_parent_id})
                template_parent_row = template_parent_id_result.fetchone()
                if template_parent_row:
                    template_parent_id = template_parent_row[0]

            # Determine if mandatory
            is_mandatory = (
                acc_type == 'H'  # All headers mandatory
                or 'cash' in description.lower()
                or 'retained' in description.lower()
                or 'receivable' in description.lower() and 'account' in description.lower()
                or 'payable' in description.lower() and 'account' in description.lower()
            )

            # Allow custom children for headers and certain detail accounts
            allow_custom_children = (
                acc_type == 'H'  # Headers allow custom children
                or 'other' in description.lower()
            )

            # Insert template account
            template_account_id = str(uuid.uuid4())
            template_account_map[master_id] = template_account_id

            connection.execute(sa.text("""
                INSERT INTO chart_template_accounts (
                    id, template_id, master_account_id, parent_id, code, name,
                    is_mandatory, allow_custom_children, sort_order, created_at
                ) VALUES (
                    :id, :template_id, :master_account_id, :parent_id, :code, :name,
                    :is_mandatory, :allow_custom_children, :sort_order, :created_at
                )
            """), {
                'id': template_account_id,
                'template_id': template_id,
                'master_account_id': master_id,
                'parent_id': template_parent_id,
                'code': code,
                'name': description,
                'is_mandatory': is_mandatory,
                'allow_custom_children': allow_custom_children,
                'sort_order': sort_order,
                'created_at': datetime.now()
            })

            sort_order += 1

        print(f"    -> Inserted {len(accounts_for_template)} accounts")
        total_template_accounts_created += len(accounts_for_template)

    print(f"  - Total template accounts created: {total_template_accounts_created}")

    # ========================================================================
    # STEP 5: Final validation
    # ========================================================================

    master_count = connection.execute(sa.text("SELECT COUNT(*) FROM master_accounts")).fetchone()[0]
    template_account_count = connection.execute(sa.text("SELECT COUNT(*) FROM chart_template_accounts")).fetchone()[0]

    print("")
    print("=" * 80)
    print("MIGRATION 019: Complete")
    print("=" * 80)
    print(f"Master accounts: {master_count}")
    print(f"Template accounts: {template_account_count}")
    print(f"Active templates seeded: {len(templates)}")
    print("=" * 80)


def downgrade() -> None:
    """
    Remove all seeded master accounts and template accounts.

    WARNING: This destroys all master chart data and template definitions.
    Only use for rollback during migration issues.
    """

    print("=" * 80)
    print("MIGRATION 019: Rolling back...")
    print("=" * 80)

    connection = op.get_bind()

    # Delete in reverse order (template accounts first, then master accounts)
    connection.execute(sa.text("DELETE FROM chart_template_accounts"))
    connection.execute(sa.text("DELETE FROM master_accounts"))

    print("  - Deleted all chart_template_accounts")
    print("  - Deleted all master_accounts")
    print("=" * 80)
    print("MIGRATION 019: Rollback complete")
    print("=" * 80)
