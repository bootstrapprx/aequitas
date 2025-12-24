"""Quick script to check what accounts exist in the database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount

db = SessionLocal()
try:
    print("\nAsset accounts (1xxxx):")
    for acc in db.query(MasterAccount).filter(MasterAccount.code.like('1%')).order_by(MasterAccount.code).limit(30).all():
        print(f"  {acc.code}: {acc.description} ({acc.category})")

    print("\nLiability accounts (2xxxx):")
    for acc in db.query(MasterAccount).filter(MasterAccount.code.like('2%')).order_by(MasterAccount.code).limit(20).all():
        print(f"  {acc.code}: {acc.description} ({acc.category})")

    print("\nEquity accounts (3xxxx):")
    for acc in db.query(MasterAccount).filter(MasterAccount.code.like('3%')).order_by(MasterAccount.code).limit(20).all():
        print(f"  {acc.code}: {acc.description} ({acc.category})")

    print("\nRevenue accounts (4xxxx):")
    for acc in db.query(MasterAccount).filter(MasterAccount.code.like('4%')).order_by(MasterAccount.code).limit(20).all():
        print(f"  {acc.code}: {acc.description} ({acc.category})")

    print("\nExpense accounts (6xxxx):")
    for acc in db.query(MasterAccount).filter(MasterAccount.code.like('6%')).order_by(MasterAccount.code).limit(20).all():
        print(f"  {acc.code}: {acc.description} ({acc.category})")

finally:
    db.close()
