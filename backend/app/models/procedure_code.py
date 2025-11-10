"""Procedure code model for CPT and HCPCS codes with semantic search support"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, Date, DateTime, Index, CheckConstraint, UniqueConstraint
from app.database import Base
from app.utils.db_types import GUID, TSVECTOR, VECTOR


class ProcedureCode(Base):
    """CPT and HCPCS procedure code model with semantic search and licensing support

    Supports:
    - CPT codes (Category I, II, III) - AMA proprietary
    - HCPCS Level II codes - CMS public domain
    - Dual description strategy: paraphrased (free) + official (licensed)
    - Semantic search via MedCPT embeddings (768 dimensions)
    - Multi-year version support
    - License status tracking for AMA compliance
    """

    __tablename__ = "procedure_codes"

    # Primary identifiers
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, index=True)
    code_system = Column(String(10), nullable=False, default='CPT')

    # Dual description strategy for licensing compliance
    paraphrased_desc = Column(Text, nullable=True,
                             comment="Free paraphrased description (no license required)")
    short_desc = Column(Text, nullable=True,
                       comment="Official short descriptor (AMA licensed for CPT)")
    long_desc = Column(Text, nullable=True,
                      comment="Official long descriptor (AMA licensed for CPT)")

    # Classification and categorization
    category = Column(String(50), nullable=True,
                     comment="E/M, Surgery, Radiology, Pathology, Medicine, etc.")
    procedure_type = Column(String(30), nullable=True,
                           comment="diagnostic, therapeutic, preventive, screening")

    # Versioning and lifecycle management
    version_year = Column(Integer, nullable=False, default=2025,
                         comment="CPT version year (e.g., 2024, 2025)")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether code is currently active")
    effective_date = Column(Date, nullable=True,
                           comment="Date when code becomes effective")
    expiry_date = Column(Date, nullable=True,
                        comment="Date when code is retired/expires")

    # Licensing and compliance
    license_status = Column(String(20), default='free', nullable=False,
                           comment="free (paraphrased) or AMA_licensed (official text)")

    # Usage and billing metadata
    relative_value_units = Column(Text, nullable=True,
                                  comment="RVU information (work, practice expense, malpractice)")
    global_period = Column(String(10), nullable=True,
                          comment="Global surgery period (000, 010, 090, XXX, YYY, ZZZ, MMM)")
    modifier_51_exempt = Column(Boolean, default=False,
                               comment="Whether code is exempt from multiple procedure reduction")

    # Semantic search
    embedding = Column(VECTOR(768), nullable=True,
                      comment="MedCPT 768-dimensional embedding for semantic search")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Legacy fields for backward compatibility
    search_vector = Column(TSVECTOR, nullable=True,
                          comment="PostgreSQL full-text search vector")

    # Indexes for optimal search performance
    __table_args__ = (
        # Unique constraint: same code can exist across multiple years and systems
        UniqueConstraint('code', 'code_system', 'version_year',
                        name='uq_procedure_code_system_year'),

        # Compound index for common queries
        Index("ix_procedure_code_system", "code", "code_system"),

        # Full-text search indexes (GIN trigram)
        Index("ix_procedure_text_gin", "paraphrased_desc", "short_desc",
              postgresql_ops={"paraphrased_desc": "gin_trgm_ops", "short_desc": "gin_trgm_ops"},
              postgresql_using="gin",
              comment="Trigram index for fuzzy text search"),

        # Vector similarity search index (IVFFlat with cosine distance)
        Index("ix_procedure_embedding_ivfflat", "embedding",
              postgresql_using="ivfflat",
              postgresql_with={"lists": 100},
              postgresql_ops={"embedding": "vector_cosine_ops"},
              comment="IVFFlat index for fast vector similarity search"),

        # Full-text search vector index
        Index("ix_procedure_search_vector", "search_vector",
              postgresql_using="gin"),

        # Check constraints
        CheckConstraint("code_system IN ('CPT', 'HCPCS')",
                       name="ck_procedure_code_system"),
        CheckConstraint("license_status IN ('free', 'AMA_licensed')",
                       name="ck_procedure_license_status"),
    )

    def __repr__(self):
        desc = self.short_desc or self.paraphrased_desc or ''
        return f"<ProcedureCode {self.code} ({self.code_system}) - {desc[:50]}>"

    def get_display_description(self) -> str:
        """Return appropriate description based on license status

        Returns:
            - Official description if licensed
            - Paraphrased description if free
            - Fallback to any available description
        """
        if self.license_status == 'AMA_licensed' and self.short_desc:
            return self.short_desc
        elif self.paraphrased_desc:
            return self.paraphrased_desc
        else:
            return self.short_desc or self.long_desc or ''
