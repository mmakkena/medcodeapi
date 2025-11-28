"""ICD-10 synonyms model"""

from sqlalchemy import Column, String, Text, Index
from infrastructure.db.postgres import Base


class ICD10Synonym(Base):
    """Alternative terms and synonyms for ICD-10 codes

    Stores alternative medical terms, lay language descriptions,
    and commonly used synonyms to improve search and code discovery.
    """

    __tablename__ = "icd10_synonyms"

    code = Column(String(10), primary_key=True, nullable=False)
    synonym = Column(Text, primary_key=True, nullable=False)

    __table_args__ = (
        # Index for fast lookup by code
        Index("ix_icd10_synonyms_code", "code"),
        # Full-text search index on synonyms
        Index("ix_icd10_synonyms_text", "synonym",
              postgresql_ops={"synonym": "gin_trgm_ops"},
              postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<ICD10Synonym {self.code}: {self.synonym[:50]}>"
