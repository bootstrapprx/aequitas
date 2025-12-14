"""
JournalEntry SQLAlchemy model.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md (Section 5.1: journal_entries)
- Phase 3A: Backend Model Alignment
"""
import uuid
from sqlalchemy import Column, String, DateTime, Date, func, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models.enums import EntryType, EntryStatus


class JournalEntry(Base):
    """
    SQLAlchemy model for journal entries.
    Represents the header of a double-entry accounting transaction.
    Each journal entry contains multiple lines (debits and credits) that must balance.
    """
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    fiscal_period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=False, index=True)

    # Entry identification
    entry_number = Column(String, nullable=False, index=True)  # Auto-generated: "JE-2024-001"
    entry_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    reference = Column(String, nullable=True)  # External reference (invoice #, check #, etc.)

    # Entry classification
    entry_type = Column(SQLEnum(EntryType, name="entrytype"), nullable=False, default=EntryType.STANDARD)
    status = Column(SQLEnum(EntryStatus, name="entrystatus"), nullable=False, default=EntryStatus.DRAFT, index=True)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    posted_at = Column(DateTime, nullable=True)
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    voided_at = Column(DateTime, nullable=True)
    voided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    void_reason = Column(Text, nullable=True)

    # Reversing entry linkage
    reverses_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)
    reversed_by_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)

    # Relationships
    company = relationship("Company", back_populates="journal_entries")
    fiscal_period = relationship("FiscalPeriod", back_populates="journal_entries")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

    creator = relationship("User", foreign_keys=[created_by])
    poster = relationship("User", foreign_keys=[posted_by])
    voider = relationship("User", foreign_keys=[voided_by])

    reverses = relationship("JournalEntry", foreign_keys=[reverses_entry_id], remote_side=[id])
    reversed_by = relationship("JournalEntry", foreign_keys=[reversed_by_entry_id], remote_side=[id])

    def __repr__(self):
        return f"<JournalEntry(entry_number='{self.entry_number}', date='{self.entry_date}', status='{self.status}')>"

    def is_posted(self) -> bool:
        """Check if the entry is posted"""
        return self.status == EntryStatus.POSTED

    def is_draft(self) -> bool:
        """Check if the entry is still a draft"""
        return self.status == EntryStatus.DRAFT

    def is_void(self) -> bool:
        """Check if the entry has been voided"""
        return self.status == EntryStatus.VOID

    def can_be_edited(self) -> bool:
        """Check if the entry can be edited (only drafts can be edited)"""
        return self.status == EntryStatus.DRAFT

    def can_be_posted(self) -> bool:
        """Check if the entry can be posted (must be draft and balanced)"""
        return self.status == EntryStatus.DRAFT

    def can_be_voided(self) -> bool:
        """Check if the entry can be voided (only posted entries can be voided)"""
        return self.status == EntryStatus.POSTED
