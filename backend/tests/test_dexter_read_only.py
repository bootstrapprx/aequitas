"""
Tests for Dexter Read-Only Enforcement

Verifies that Dexter cannot write to database under any circumstance.

Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.

CRITICAL INVARIANTS TESTED:
- Dexter session blocks all write operations
- Tone enforcer blocks forbidden phrases
- Observer service is truly read-only
"""

import pytest
from uuid import uuid4
from sqlalchemy.exc import StatementError

from app.db.dexter_session import (
    DexterReadOnlySession,
    DexterWriteViolation,
    get_dexter_db
)
from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry
from app.services.dexter_observer_service import DexterObserverService
from app.services.dexter_tone_enforcer import (
    DexterToneEnforcer,
    DexterToneViolation,
    ToneViolationType
)


# ============================================================================
# DATABASE WRITE BLOCKING TESTS
# ============================================================================

class TestDexterSessionWriteBlocking:
    """Test that DexterReadOnlySession blocks all write operations."""

    def test_blocks_add(self):
        """Test that add() is blocked."""
        db = next(get_dexter_db())

        account = MasterAccount(
            id=uuid4(),
            code="TEST001",
            description="Test Account"
        )

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.add(account)

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to add" in str(exc_info.value)
        db.close()

    def test_blocks_add_all(self):
        """Test that add_all() is blocked."""
        db = next(get_dexter_db())

        accounts = [
            MasterAccount(id=uuid4(), code="TEST001", description="Test 1"),
            MasterAccount(id=uuid4(), code="TEST002", description="Test 2"),
        ]

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.add_all(accounts)

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to add" in str(exc_info.value)
        db.close()

    def test_blocks_commit(self):
        """Test that commit() is blocked."""
        db = next(get_dexter_db())

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.commit()

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to commit" in str(exc_info.value)
        db.close()

    def test_blocks_flush(self):
        """Test that flush() is blocked."""
        db = next(get_dexter_db())

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.flush()

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to flush" in str(exc_info.value)
        db.close()

    def test_blocks_delete(self):
        """Test that delete() is blocked."""
        db = next(get_dexter_db())

        # Create a dummy instance (won't actually be in session)
        account = MasterAccount(id=uuid4(), code="TEST001", description="Test")

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.delete(account)

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to delete" in str(exc_info.value)
        db.close()

    def test_blocks_merge(self):
        """Test that merge() is blocked."""
        db = next(get_dexter_db())

        account = MasterAccount(id=uuid4(), code="TEST001", description="Test")

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.merge(account)

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "Dexter attempted to merge" in str(exc_info.value)
        db.close()

    def test_blocks_insert_statement(self):
        """Test that raw INSERT statements are blocked."""
        db = next(get_dexter_db())

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.execute("INSERT INTO master_accounts (code, description) VALUES ('TEST001', 'Test')")

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "INSERT" in str(exc_info.value)
        db.close()

    def test_blocks_update_statement(self):
        """Test that raw UPDATE statements are blocked."""
        db = next(get_dexter_db())

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.execute("UPDATE master_accounts SET description = 'Modified' WHERE code = '10000'")

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "UPDATE" in str(exc_info.value)
        db.close()

    def test_blocks_delete_statement(self):
        """Test that raw DELETE statements are blocked."""
        db = next(get_dexter_db())

        with pytest.raises(DexterWriteViolation) as exc_info:
            db.execute("DELETE FROM master_accounts WHERE code = '10000'")

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "DELETE" in str(exc_info.value)
        db.close()

    def test_allows_select_statement(self):
        """Test that SELECT statements ARE allowed."""
        db = next(get_dexter_db())

        # This should NOT raise an exception
        result = db.execute("SELECT COUNT(*) FROM master_accounts")
        count = result.scalar()

        assert count is not None
        assert count >= 0
        db.close()

    def test_allows_query(self):
        """Test that ORM queries ARE allowed."""
        db = next(get_dexter_db())

        # This should NOT raise an exception
        accounts = db.query(MasterAccount).all()

        assert isinstance(accounts, list)
        db.close()


# ============================================================================
# TONE ENFORCEMENT TESTS
# ============================================================================

class TestDexterToneEnforcement:
    """Test that tone enforcer blocks forbidden phrases."""

    def setup_method(self):
        """Set up enforcer for each test."""
        self.enforcer = DexterToneEnforcer()

    def test_blocks_imperative_you_should(self):
        """Test that 'you should' is blocked."""
        message = "You should post this entry now."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert len(violations) > 0
        assert violations[0]["type"] == ToneViolationType.IMPERATIVE
        assert "you should" in violations[0]["phrase"]

    def test_blocks_imperative_you_must(self):
        """Test that 'you must' is blocked."""
        message = "You must close this period immediately."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.IMPERATIVE for v in violations)

    def test_blocks_urgency_urgent(self):
        """Test that 'urgent' is blocked."""
        message = "Urgent: Fix this now!"

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.URGENCY for v in violations)

    def test_blocks_urgency_critical(self):
        """Test that 'critical' is blocked."""
        message = "Critical: Review immediately."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.URGENCY for v in violations)

    def test_blocks_authority_i_recommend(self):
        """Test that 'I recommend' is blocked."""
        message = "I recommend you close the period."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.AUTHORITY for v in violations)

    def test_blocks_auto_action_i_posted(self):
        """Test that 'I posted' is blocked (CRITICAL)."""
        message = "I posted this entry for you."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.AUTO_ACTION for v in violations)

    def test_blocks_auto_action_i_created(self):
        """Test that 'I created' is blocked (CRITICAL)."""
        message = "I created this journal entry based on patterns."

        is_valid, violations = self.enforcer.check(message)

        assert not is_valid
        assert any(v["type"] == ToneViolationType.AUTO_ACTION for v in violations)

    def test_allows_i_noticed(self):
        """Test that 'I noticed' IS allowed (approved advisory phrase)."""
        message = "I noticed you frequently post to AWS Hosting."

        is_valid, violations = self.enforcer.check(message)

        assert is_valid
        assert len(violations) == 0

    def test_allows_you_may_want_to(self):
        """Test that 'you may want to' IS allowed."""
        message = "You may want to review this entry."

        is_valid, violations = self.enforcer.check(message)

        assert is_valid
        assert len(violations) == 0

    def test_allows_dismissible(self):
        """Test that messages with 'Dismiss' are allowed."""
        message = "I noticed a pattern. [Create Template] [Dismiss]"

        is_valid, violations = self.enforcer.check(message)

        assert is_valid
        assert len(violations) == 0

    def test_validate_raises_exception(self):
        """Test that validate() raises exception for invalid messages."""
        message = "You should post this immediately."

        with pytest.raises(DexterToneViolation) as exc_info:
            self.enforcer.validate(message)

        assert "CANON VIOLATION" in str(exc_info.value)
        assert "you should" in str(exc_info.value).lower()

    def test_format_insight_with_approved_tone(self):
        """Test that format_insight() generates valid messages."""
        message = self.enforcer.format_insight(
            observation="you frequently post to AWS Hosting",
            context="This may indicate a recurring expense",
            action_label="Create Template"
        )

        # Should not raise exception
        self.enforcer.validate(message)

        assert "I noticed" in message
        assert "AWS Hosting" in message
        assert "Create Template" in message
        assert "Dismiss" in message


# ============================================================================
# OBSERVER SERVICE READ-ONLY TESTS
# ============================================================================

class TestDexterObserverServiceReadOnly:
    """Test that DexterObserverService is truly read-only."""

    def test_detect_patterns_does_not_mutate_db(self):
        """Test that detect_recurring_patterns() does not modify database."""
        db_before = SessionLocal()
        initial_count = db_before.query(JournalEntry).count()
        db_before.close()

        # Use Dexter session
        dexter_db = next(get_dexter_db())
        service = DexterObserverService(dexter_db)

        # This should be read-only
        try:
            patterns = service.detect_recurring_patterns(
                company_id=uuid4(),
                lookback_months=3
            )
        except Exception:
            pass  # May fail if company doesn't exist, that's fine

        dexter_db.close()

        # Verify database unchanged
        db_after = SessionLocal()
        final_count = db_after.query(JournalEntry).count()
        db_after.close()

        assert initial_count == final_count

    def test_detect_anomalies_does_not_mutate_db(self):
        """Test that detect_anomalies() does not modify database."""
        db_before = SessionLocal()
        initial_count = db_before.query(JournalEntry).count()
        db_before.close()

        # Use Dexter session
        dexter_db = next(get_dexter_db())
        service = DexterObserverService(dexter_db)

        try:
            anomalies = service.detect_anomalies(
                company_id=uuid4(),
                threshold_stddev=2.0
            )
        except Exception:
            pass

        dexter_db.close()

        # Verify database unchanged
        db_after = SessionLocal()
        final_count = db_after.query(JournalEntry).count()
        db_after.close()

        assert initial_count == final_count


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestDexterCanonCompliance:
    """Integration tests for Canon IV compliance."""

    def test_dexter_cannot_create_journal_entry(self):
        """
        CRITICAL TEST: Verify Dexter absolutely cannot create journal entries.

        This is the most important test. If this fails, Canon IV is violated.
        """
        dexter_db = next(get_dexter_db())

        entry = JournalEntry(
            id=uuid4(),
            company_id=uuid4(),
            description="Test Entry",
            is_posted=False
        )

        with pytest.raises(DexterWriteViolation):
            dexter_db.add(entry)
            dexter_db.commit()

        dexter_db.close()

    def test_dexter_cannot_post_entry(self):
        """
        CRITICAL TEST: Verify Dexter cannot post entries.

        Even if an entry exists, Dexter cannot change is_posted.
        """
        dexter_db = next(get_dexter_db())

        # Attempt to execute UPDATE (should be blocked)
        with pytest.raises(DexterWriteViolation):
            dexter_db.execute(
                "UPDATE journal_entries SET is_posted = true WHERE id = :id",
                {"id": str(uuid4())}
            )

        dexter_db.close()

    def test_dexter_can_only_observe(self):
        """Test that Dexter can read but not write."""
        dexter_db = next(get_dexter_db())

        # Reading should work
        accounts = dexter_db.query(MasterAccount).limit(5).all()
        assert isinstance(accounts, list)

        # Writing should fail
        with pytest.raises(DexterWriteViolation):
            dexter_db.add(MasterAccount(
                id=uuid4(),
                code="TEST",
                description="Test"
            ))

        dexter_db.close()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
