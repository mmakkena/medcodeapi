"""ICD-10 AI facets model for reasoning metadata"""

from sqlalchemy import Column, String, Boolean, PrimaryKeyConstraint
from infrastructure.db.postgres import Base
from domain.common.db_types import JSONB


class ICD10AIFacet(Base):
    """AI reasoning facets for ICD-10 codes

    Stores metadata about body systems, acuity, severity, chronicity,
    and other clinical attributes useful for AI reasoning and clinical decision support.
    """

    __tablename__ = "icd10_ai_facets"

    code = Column(String(10), nullable=False)
    code_system = Column(String(15), nullable=False)
    concept_type = Column(String(40), nullable=True)  # e.g., 'diagnosis', 'procedure', 'symptom'
    body_system = Column(String(40), nullable=True)  # e.g., 'cardiovascular', 'respiratory', 'endocrine'
    acuity = Column(String(40), nullable=True)  # e.g., 'acute', 'chronic', 'subacute'
    severity = Column(String(40), nullable=True)  # e.g., 'mild', 'moderate', 'severe', 'life-threatening'
    chronicity = Column(String(40), nullable=True)  # e.g., 'acute', 'chronic', 'recurrent'
    laterality = Column(String(40), nullable=True)  # e.g., 'left', 'right', 'bilateral', 'unspecified'
    onset_context = Column(String(40), nullable=True)  # e.g., 'congenital', 'acquired', 'traumatic'
    age_band = Column(String(40), nullable=True)  # e.g., 'pediatric', 'adult', 'geriatric', 'neonatal'
    sex_specific = Column(String(10), nullable=True)  # e.g., 'male', 'female', 'both'
    risk_flag = Column(Boolean, default=False, nullable=True)  # High-risk condition flag
    extra = Column(JSONB, nullable=True)  # Additional flexible metadata in JSON format

    __table_args__ = (
        PrimaryKeyConstraint('code', 'code_system', name='pk_icd10_ai_facets'),
    )

    def __repr__(self):
        return f"<ICD10AIFacet {self.code} ({self.code_system}) - {self.body_system}/{self.concept_type}>"
