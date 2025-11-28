"""
Knowledge Base Database Models

Models for CDI knowledge base data including:
- E/M Codes: Evaluation & Management code reference
- Investigation Protocols: Clinical investigation guidelines by condition
- CDI Guidelines: Document-based CDI guidance and best practices
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    JSON, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

from infrastructure.db.postgres import Base


class EMCode(Base):
    """
    E/M (Evaluation & Management) code reference table.

    Contains CPT E/M codes with MDM criteria, time requirements,
    and reimbursement information for coding guidance.
    """
    __tablename__ = "em_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False)  # e.g., "Office or Other Outpatient - New Patient"
    level = Column(Integer, nullable=False)  # 1-5
    description = Column(Text, nullable=False)
    setting = Column(String(50), nullable=False)  # outpatient, inpatient, ed, critical_care
    patient_type = Column(String(50), nullable=False)  # new, established, initial, subsequent
    mdm_level = Column(String(50))  # straightforward, low, moderate, high
    typical_time = Column(Integer)  # minutes
    time_range_min = Column(Integer)
    time_range_max = Column(Integer)
    reimbursement = Column(Float)  # estimated $ amount

    # JSON fields for complex nested data
    requirements = Column(JSON)  # history, examination, mdm requirements
    mdm_criteria = Column(JSON)  # problems, data, risk criteria

    # Metadata
    effective_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    __table_args__ = (
        Index('ix_em_codes_setting_patient_type', 'setting', 'patient_type'),
        Index('ix_em_codes_mdm_level', 'mdm_level'),
    )

    def __repr__(self):
        return f"<EMCode {self.code}: {self.description[:50]}>"


class InvestigationProtocol(Base):
    """
    Clinical investigation protocol for a specific condition.

    Contains evidence-based investigation recommendations including
    required tests, timing, rationale, and billing information.
    """
    __tablename__ = "investigation_protocols"

    id = Column(Integer, primary_key=True)
    condition = Column(String(200), nullable=False, index=True)
    severity_level = Column(String(100))  # e.g., sepsis, severe_sepsis, septic_shock
    test_name = Column(String(200), nullable=False)
    cpt_code = Column(String(10), index=True)
    timing = Column(String(200))  # e.g., "Within 1 hour", "Stat"
    rationale = Column(Text)
    estimated_cost = Column(Float)
    evidence_grade = Column(String(10))  # A, B, C
    guideline_source = Column(String(200))

    # Additional test categorization
    test_category = Column(String(100))  # required, source_directed, advanced_monitoring
    source_type = Column(String(100))  # respiratory, abdominal, skin, etc.

    # ICD-10 codes associated with the condition
    icd10_codes = Column(ARRAY(String))

    # Metadata
    is_required = Column(Boolean, default=False)
    is_sep1_requirement = Column(Boolean, default=False)  # CMS SEP-1 bundle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    __table_args__ = (
        Index('ix_investigation_condition_severity', 'condition', 'severity_level'),
        Index('ix_investigation_cpt', 'cpt_code'),
    )

    def __repr__(self):
        return f"<InvestigationProtocol {self.condition}/{self.test_name}>"


class CDIGuideline(Base):
    """
    CDI guideline/best practice document content.

    Contains chunked content from CDI reference documents
    with embeddings for semantic search.
    """
    __tablename__ = "cdi_guidelines"

    id = Column(Integer, primary_key=True)
    source_document = Column(String(500), nullable=False)  # PDF filename
    document_type = Column(String(100))  # practice_brief, toolkit, reference
    section_title = Column(String(500))
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)  # Position in document

    # Categorization
    category = Column(String(100))  # query_writing, documentation, coding, compliance
    subcategory = Column(String(100))
    tags = Column(ARRAY(String))

    # Metadata
    page_number = Column(Integer)
    source_url = Column(String(500))
    publication_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vector embedding for semantic search (768-dim MedCPT)
    embedding = Column(Vector(768))

    __table_args__ = (
        Index('ix_cdi_guidelines_category', 'category'),
        Index('ix_cdi_guidelines_document', 'source_document'),
    )

    def __repr__(self):
        return f"<CDIGuideline {self.source_document}:{self.chunk_index}>"


class DRGRule(Base):
    """
    DRG optimization rules and documentation requirements.

    Contains DRG-specific documentation guidance for
    capturing appropriate complexity and severity.
    """
    __tablename__ = "drg_rules"

    id = Column(Integer, primary_key=True)
    drg_code = Column(String(10), nullable=False, index=True)
    description = Column(Text, nullable=False)
    weight = Column(Float)
    condition = Column(String(200))  # Associated condition

    # Optimization information
    optimization_notes = Column(Text)
    required_documentation = Column(ARRAY(String))
    potential_upgrade_drg = Column(String(10))
    revenue_impact = Column(String(100))  # e.g., "$5,000-7,000"

    # Associated codes
    principal_dx_codes = Column(ARRAY(String))
    mcc_codes = Column(ARRAY(String))  # Major Complication/Comorbidity
    cc_codes = Column(ARRAY(String))   # Complication/Comorbidity

    # Metadata
    fiscal_year = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    def __repr__(self):
        return f"<DRGRule {self.drg_code}: {self.description[:50]}>"


class BillingNote(Base):
    """
    Billing notes and coding guidance.

    Contains condition-specific billing guidance and tips
    for accurate charge capture.
    """
    __tablename__ = "billing_notes"

    id = Column(Integer, primary_key=True)
    condition = Column(String(200), index=True)
    cpt_code = Column(String(10), index=True)
    note_type = Column(String(50))  # tip, warning, requirement
    content = Column(Text, nullable=False)

    # Metadata
    source = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vector embedding
    embedding = Column(Vector(768))

    def __repr__(self):
        return f"<BillingNote {self.condition}/{self.cpt_code}>"
