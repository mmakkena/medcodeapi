"""ICD-10 code relations model"""

import sqlalchemy as sa
from sqlalchemy import Column, String, BigInteger, Index, Integer
from infrastructure.db.postgres import Base


class ICD10Relation(Base):
    """Relationships between ICD-10 codes

    Captures hierarchical and semantic relationships:
    - parent-child (hierarchical)
    - includes/excludes (scope)
    - see-also (related)
    - replaced-by (versioning)
    - complication-of
    - manifestation-of
    """

    __tablename__ = "icd10_relations"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    related_code = Column(String(10), nullable=False, index=True)
    relation_type = Column(String(30), nullable=False)  # e.g., 'parent', 'child', 'see-also', 'excludes', 'includes'

    __table_args__ = (
        # Composite index for efficient lookups
        Index("ix_icd10_relations_code_type", "code", "relation_type"),
        Index("ix_icd10_relations_related_type", "related_code", "relation_type"),
    )

    def __repr__(self):
        return f"<ICD10Relation {self.code} --{self.relation_type}-> {self.related_code}>"
