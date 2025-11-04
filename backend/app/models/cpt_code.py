"""CPT code model"""

import uuid
from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from app.database import Base


class CPTCode(Base):
    """CPT procedure code model"""

    __tablename__ = "cpt_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search

    # Indexes for search performance
    __table_args__ = (
        Index("ix_cpt_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_cpt_description", "description", postgresql_ops={"description": "gin_trgm_ops"}, postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<CPTCode {self.code} - {self.description[:50]}>"
