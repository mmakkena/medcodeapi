"""Code mapping model for cross-system code mappings"""

import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Text, Numeric, Date, BigInteger
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID


class CodeMapping(Base):
    """Cross-system code mappings

    Maps between different medical coding systems:
    - ICD-10/ICD-10-CM/ICD-10-PCS
    - SNOMED CT
    - LOINC
    - CPT/HCPCS
    - Custom/proprietary systems
    """

    __tablename__ = "code_mappings"

    id = Column(BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True, autoincrement=True)
    from_system = Column(String(20), nullable=False, index=True)  # e.g., 'ICD10-CM', 'SNOMED', 'LOINC'
    from_code = Column(String(20), nullable=False, index=True)
    to_system = Column(String(20), nullable=False, index=True)  # Target system
    to_code = Column(String(40), nullable=False, index=True)
    map_type = Column(String(30), nullable=False)  # e.g., 'exact', 'narrow', 'broad', 'billing', 'related'
    confidence = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00 confidence score
    source_name = Column(String(120), nullable=True)  # Source of mapping (e.g., 'CMS', 'WHO', 'NLM')
    source_version = Column(String(40), nullable=True)  # Version of source mapping data
    source_url = Column(Text, nullable=True)  # URL to source documentation
    reviewed_by = Column(String(120), nullable=True)  # Clinical reviewer name/ID
    review_note = Column(Text, nullable=True)  # Notes from clinical review
    effective_date = Column(Date, nullable=True)  # When mapping becomes effective
    expiry_date = Column(Date, nullable=True)  # When mapping expires/is deprecated

    def __repr__(self):
        return f"<CodeMapping {self.from_system}:{self.from_code} -> {self.to_system}:{self.to_code} ({self.map_type})>"
