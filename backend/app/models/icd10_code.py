"""ICD-10 code model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, Date, DateTime, Index, CheckConstraint
from app.database import Base
from app.utils.db_types import GUID, TSVECTOR, VECTOR


class ICD10Code(Base):
    """ICD-10 diagnosis code model with semantic search support"""

    __tablename__ = "icd10_codes"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, index=True)
    code_system = Column(String(15), nullable=False, default='ICD10-CM')
    short_desc = Column(Text, nullable=True)
    long_desc = Column(Text, nullable=True)
    chapter = Column(String(120), nullable=True)
    block_range = Column(String(20), nullable=True)
    category = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version_year = Column(Integer, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    embedding = Column(VECTOR(768), nullable=True)  # 768-dim MedCPT embeddings
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Legacy field for backward compatibility
    description = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search

    # Indexes for search performance
    __table_args__ = (
        # Unique constraint on code + code_system combination
        Index("ix_icd10_code_system", "code", "code_system", unique=True),
        # Full-text search indexes
        Index("ix_icd10_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_icd10_description_trgm", "short_desc", "long_desc",
              postgresql_ops={"short_desc": "gin_trgm_ops", "long_desc": "gin_trgm_ops"},
              postgresql_using="gin"),
        # Vector similarity search index (IVFFlat)
        Index("ix_icd10_embedding_ivfflat", "embedding",
              postgresql_using="ivfflat",
              postgresql_with={"lists": 100},
              postgresql_ops={"embedding": "vector_cosine_ops"}),
        # Check constraint for code_system
        CheckConstraint("code_system IN ('ICD10', 'ICD10-CM', 'ICD10-PCS')",
                       name="ck_icd10_code_system"),
    )

    def __repr__(self):
        return f"<ICD10Code {self.code} ({self.code_system}) - {self.short_desc or self.description or ''}>"
