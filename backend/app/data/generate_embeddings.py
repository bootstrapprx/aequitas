"""
Generate Embeddings for Master Chart and Company Accounts

This script generates semantic embeddings for all accounts in the database.
Run this after enabling pgvector extension and adding embedding columns.

Usage:
    python -m app.data.generate_embeddings

Options:
    --master-only: Only generate embeddings for master chart
    --company-only: Only generate embeddings for company accounts
    --company-id: Generate embeddings for specific company
"""

import sys
import argparse
from typing import Optional
from uuid import UUID

from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount
from app.db.models.company_account import CompanyAccount
from app.services.embedding_service import get_embedding_service, is_embeddings_available


def generate_master_chart_embeddings(db, force: bool = False) -> dict:
    """
    Generate embeddings for all master chart accounts.

    Args:
        db: Database session
        force: If True, regenerate even if embedding exists

    Returns:
        Dictionary with statistics
    """
    if not is_embeddings_available():
        return {
            "status": "error",
            "message": "Embeddings not available. Install sentence-transformers."
        }

    embedding_service = get_embedding_service()

    # Get all master accounts
    query = db.query(MasterAccount)
    if not force:
        query = query.filter(MasterAccount.embedding == None)

    accounts = query.all()

    if not accounts:
        return {
            "status": "success",
            "message": "No accounts to process",
            "processed": 0
        }

    print(f"Generating embeddings for {len(accounts)} master accounts...")

    processed = 0
    errors = 0

    for i, account in enumerate(accounts, 1):
        try:
            # Prepare account data for embedding
            account_data = {
                "description": account.description,
                "long_description": account.long_description,
                "tags": account.tags,
                "category": account.category
            }

            # Generate embedding
            embedding = embedding_service.generate_account_embedding(account_data)

            # Update account
            account.embedding = embedding
            processed += 1

            if i % 50 == 0:
                print(f"  Processed {i}/{len(accounts)}...")
                db.commit()

        except Exception as e:
            print(f"  Error processing account {account.code}: {e}")
            errors += 1

    # Final commit
    db.commit()

    print(f"✓ Generated embeddings for {processed} master accounts")
    if errors > 0:
        print(f"⚠ {errors} errors encountered")

    return {
        "status": "success",
        "processed": processed,
        "errors": errors,
        "total": len(accounts)
    }


def generate_company_embeddings(
    db,
    company_id: Optional[UUID] = None,
    force: bool = False
) -> dict:
    """
    Generate embeddings for company accounts.

    Args:
        db: Database session
        company_id: If provided, only process this company
        force: If True, regenerate even if embedding exists

    Returns:
        Dictionary with statistics
    """
    if not is_embeddings_available():
        return {
            "status": "error",
            "message": "Embeddings not available. Install sentence-transformers."
        }

    embedding_service = get_embedding_service()

    # Get company accounts
    query = db.query(CompanyAccount)
    if company_id:
        query = query.filter(CompanyAccount.company_id == company_id)
    if not force:
        query = query.filter(CompanyAccount.embedding == None)

    accounts = query.all()

    if not accounts:
        return {
            "status": "success",
            "message": "No accounts to process",
            "processed": 0
        }

    print(f"Generating embeddings for {len(accounts)} company accounts...")

    processed = 0
    errors = 0

    for i, account in enumerate(accounts, 1):
        try:
            # Prepare account data for embedding
            account_data = {
                "description": account.description,
                "category": account.json_data.get("category") if account.json_data else None
            }

            # Generate embedding
            embedding = embedding_service.generate_account_embedding(account_data)

            # Update account
            account.embedding = embedding
            processed += 1

            if i % 50 == 0:
                print(f"  Processed {i}/{len(accounts)}...")
                db.commit()

        except Exception as e:
            print(f"  Error processing account {account.code}: {e}")
            errors += 1

    # Final commit
    db.commit()

    print(f"✓ Generated embeddings for {processed} company accounts")
    if errors > 0:
        print(f"⚠ {errors} errors encountered")

    return {
        "status": "success",
        "processed": processed,
        "errors": errors,
        "total": len(accounts)
    }


def main():
    """Main entry point for embedding generation."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for master chart and company accounts"
    )
    parser.add_argument(
        "--master-only",
        action="store_true",
        help="Only generate embeddings for master chart"
    )
    parser.add_argument(
        "--company-only",
        action="store_true",
        help="Only generate embeddings for company accounts"
    )
    parser.add_argument(
        "--company-id",
        type=str,
        help="Generate embeddings for specific company (UUID)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even if they exist"
    )

    args = parser.parse_args()

    # Check if embeddings are available
    if not is_embeddings_available():
        print("❌ Error: sentence-transformers not installed")
        print("   Install with: pip install sentence-transformers")
        sys.exit(1)

    db = SessionLocal()

    try:
        print("\n" + "="*60)
        print("EMBEDDING GENERATION")
        print("="*60 + "\n")

        # Generate master chart embeddings
        if not args.company_only:
            print("1. Master Chart Embeddings")
            print("-" * 40)
            master_result = generate_master_chart_embeddings(db, force=args.force)
            print()

        # Generate company embeddings
        if not args.master_only:
            print("2. Company Account Embeddings")
            print("-" * 40)
            company_id = UUID(args.company_id) if args.company_id else None
            company_result = generate_company_embeddings(
                db,
                company_id=company_id,
                force=args.force
            )
            print()

        print("="*60)
        print("EMBEDDING GENERATION COMPLETE")
        print("="*60)

        # Remind about reindexing
        print("\n⚠ IMPORTANT: Reindex pgvector indexes for optimal performance:")
        print("   REINDEX INDEX master_accounts_embedding_idx;")
        print("   REINDEX INDEX company_accounts_embedding_idx;")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
