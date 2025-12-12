import uuid
from sqlalchemy import Column, String, Date, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

# pgvector support
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    Vector = None

class MasterAccount(Base):
    """
    SQLAlchemy model for the Master Chart of Accounts.
    Enhanced with IFRS/US-GAAP compliance fields for AI interaction.
    """
    __tablename__ = "master_accounts"

    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    type = Column(String(1), nullable=False)  # "H" for Header, "D" for Detail
    parent_code = Column(String, nullable=True)
    level = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    # Enhanced fields for AI and compliance
    long_description = Column(Text, nullable=True)  # Professional IFRS/GAAP explanation
    fs_mapping = Column(String, nullable=True)  # "Balance Sheet" or "Income Statement"
    tags = Column(ARRAY(String), nullable=True)  # AI-friendly keywords for classification
    default_vendors = Column(ARRAY(String), nullable=True)  # Common vendor associations
    regulatory_mapping = Column(JSON, nullable=True)  # IFRS/IPSAS/ASC references
    
    # Additional metadata
    normal_balance = Column(String, nullable=True)  # "Debit" or "Credit"
    cash_flow_classification = Column(String, nullable=True)  # "Operating", "Investing", "Financing"
    cost_center = Column(String, nullable=True)  # Default cost center assignment

    # Semantic search support (pgvector)
    # 384 dimensions for all-MiniLM-L6-v2 model
    # Stores embedding for semantic similarity search
    embedding = Column(Vector(384), nullable=True) if VECTOR_AVAILABLE else Column(ARRAY(float), nullable=True)

    # Hierarchy relationships
    parent_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id"), nullable=True)
    
    # Self-referential relationship for parent-child hierarchy.
    # remote_side=[id] is necessary for SQLAlchemy to understand the self-join.
    parent = relationship("MasterAccount", remote_side=[id], back_populates="children")
    
    # cascade="all, delete-orphan" ensures that children are deleted when the parent is.
    children = relationship("MasterAccount", back_populates="parent", cascade="all, delete-orphan")

    # Relationships
    company_accounts = relationship("CompanyAccount", back_populates="master_account")

    def __repr__(self):
        return f"<MasterAccount(code='{self.code}', description='{self.description}', category='{self.category}')>"

    def as_dict(self):
        """Return object data in easily serializable format"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def to_ai_context(self):
        """
        Return a simplified dict optimized for AI (DEXTER) interaction.
        Includes all relevant fields for intelligent account classification.
        """
        return {
            "code": self.code,
            "description": self.description,
            "long_description": self.long_description,
            "category": self.category,
            "type": self.type,
            "tags": self.tags or [],
            "default_vendors": self.default_vendors or [],
            "fs_mapping": self.fs_mapping,
            "normal_balance": self.normal_balance,
            "regulatory_mapping": self.regulatory_mapping or {},
            "parent_code": self.parent_code,
            "level": self.level,
        }
    
    def matches_keywords(self, keywords: list[str]) -> bool:
        """
        Check if this account matches any of the given keywords.
        Useful for AI-powered search and classification.
        """
        if not keywords:
            return False
        
        searchable_text = " ".join([
            self.description.lower(),
            self.long_description.lower() if self.long_description else "",
            " ".join(self.tags).lower() if self.tags else "",
            " ".join(self.default_vendors).lower() if self.default_vendors else "",
        ])
        
        return any(keyword.lower() in searchable_text for keyword in keywords)
    
    def matches_vendor(self, vendor_name: str) -> bool:
        """
        Check if this account is associated with a given vendor.
        Useful for automatic account suggestion based on vendor.
        """
        if not self.default_vendors or not vendor_name:
            return False
        
        vendor_lower = vendor_name.lower()
        return any(vendor_lower in v.lower() for v in self.default_vendors)
