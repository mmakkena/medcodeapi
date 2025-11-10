"""Procedure code synonyms model for alternative terms and descriptions"""

from sqlalchemy import Column, String, Text, Index, PrimaryKeyConstraint
from app.database import Base


class ProcedureCodeSynonym(Base):
    """Alternative terms and synonyms for CPT and HCPCS procedure codes

    Stores alternative medical terms, lay language descriptions,
    common abbreviations, and commonly used synonyms to improve
    search and code discovery for procedures.

    Examples:
    - CPT 99213: "level 3 office visit", "established patient moderate complexity"
    - CPT 36415: "venipuncture", "blood draw", "phlebotomy"
    - HCPCS J0585: "botox injection", "botulinum toxin"
    """

    __tablename__ = "procedure_code_synonyms"

    # Composite primary key (code + code_system + synonym)
    code = Column(String(10), primary_key=True, nullable=False,
                  comment="CPT or HCPCS code")
    code_system = Column(String(10), primary_key=True, nullable=False,
                        comment="CPT or HCPCS")
    synonym = Column(Text, primary_key=True, nullable=False,
                    comment="Alternative term or lay language description")

    __table_args__ = (
        # Composite primary key constraint
        PrimaryKeyConstraint('code', 'code_system', 'synonym',
                            name='pk_procedure_code_synonyms'),

        # Index for fast lookup by code and system
        Index("ix_procedure_synonyms_code_system", "code", "code_system"),

        # Full-text search index on synonyms for fuzzy matching (trigram index for fuzzy text search)
        Index("ix_procedure_synonyms_text", "synonym",
              postgresql_ops={"synonym": "gin_trgm_ops"},
              postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<ProcedureCodeSynonym {self.code} ({self.code_system}): {self.synonym[:50]}>"
