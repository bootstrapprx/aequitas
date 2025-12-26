"""
Dexter Read-Only Database Session

Provides mechanical guarantee that Dexter cannot write to the database.

Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.

CRITICAL INVARIANTS:
- Dexter can only SELECT (read)
- Any write operation (INSERT, UPDATE, DELETE) raises DexterWriteViolation
- All commits are blocked
- Flush operations are blocked

This is enforced at the session level, not by convention.
"""

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.exc import StatementError


class DexterWriteViolation(Exception):
    """
    Raised when Dexter attempts to write to the database.

    This is a CRITICAL VIOLATION of Canon IV.
    Dexter is observer-only and must never mutate data.
    """
    pass


class DexterReadOnlySession(Session):
    """
    Read-only SQLAlchemy session for Dexter.

    All write operations are blocked at the session level.
    This provides mechanical guarantee (not just convention).

    Usage:
        from app.db.dexter_session import get_dexter_db

        db = next(get_dexter_db())
        # Can read
        accounts = db.query(MasterAccount).all()

        # Cannot write (raises DexterWriteViolation)
        db.add(new_entry)  # BLOCKED
        db.commit()        # BLOCKED
        db.flush()         # BLOCKED
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Block flush operations
        @event.listens_for(self, "before_flush")
        def block_flush(session, flush_context, instances):
            raise DexterWriteViolation(
                "CANON VIOLATION: Dexter attempted to flush changes to database. "
                "Dexter is read-only (Canon IV). No write operations are permitted."
            )

    def commit(self):
        """Block all commits."""
        raise DexterWriteViolation(
            "CANON VIOLATION: Dexter attempted to commit to database. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def flush(self, *args, **kwargs):
        """Block all flushes."""
        raise DexterWriteViolation(
            "CANON VIOLATION: Dexter attempted to flush to database. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def add(self, instance, *args, **kwargs):
        """Block adding new instances."""
        raise DexterWriteViolation(
            f"CANON VIOLATION: Dexter attempted to add {type(instance).__name__} to database. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def add_all(self, instances):
        """Block adding multiple instances."""
        raise DexterWriteViolation(
            f"CANON VIOLATION: Dexter attempted to add {len(instances)} instances to database. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def delete(self, instance):
        """Block deleting instances."""
        raise DexterWriteViolation(
            f"CANON VIOLATION: Dexter attempted to delete {type(instance).__name__} from database. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def merge(self, instance, *args, **kwargs):
        """Block merging instances."""
        raise DexterWriteViolation(
            f"CANON VIOLATION: Dexter attempted to merge {type(instance).__name__}. "
            "Dexter is read-only (Canon IV). No write operations are permitted."
        )

    def execute(self, statement, *args, **kwargs):
        """
        Allow SELECT, block INSERT/UPDATE/DELETE.

        This intercepts raw SQL execution.
        """
        # Convert statement to string for inspection
        stmt_str = str(statement).strip().upper()

        # Block write operations
        forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE']
        for keyword in forbidden_keywords:
            if stmt_str.startswith(keyword):
                raise DexterWriteViolation(
                    f"CANON VIOLATION: Dexter attempted to execute {keyword} statement. "
                    "Dexter is read-only (Canon IV). Only SELECT queries are permitted."
                )

        # Allow SELECT and other read-only operations
        return super().execute(statement, *args, **kwargs)


# ============================================================================
# SESSION FACTORY FOR DEXTER
# ============================================================================

from app.db.session import engine
from sqlalchemy.orm import sessionmaker

DexterSessionLocal = sessionmaker(
    class_=DexterReadOnlySession,
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_dexter_db():
    """
    Dependency injection for Dexter endpoints.

    Yields a read-only database session.

    Usage:
        @router.get("/dexter/insights")
        def get_insights(db: Session = Depends(get_dexter_db)):
            # db is read-only
            accounts = db.query(MasterAccount).all()
            return {"accounts": len(accounts)}
    """
    db = DexterSessionLocal()
    try:
        yield db
    finally:
        db.close()
