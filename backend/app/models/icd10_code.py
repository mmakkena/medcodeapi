"""ICD-10 code model"""

import uuid
from sqlalchemy import Column, String, Text, Index
from app.database import Base
from app.utils.db_types import GUID, TSVECTOR


class ICD10Code(Base):
    """ICD-10 diagnosis code model"""

    __tablename__ = "icd10_codes"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search

    # Indexes for search performance
    __table_args__ = (
        Index("ix_icd10_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_icd10_description", "description", postgresql_ops={"description": "gin_trgm_ops"}, postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<ICD10Code {self.code} - {self.description[:50]}>"
