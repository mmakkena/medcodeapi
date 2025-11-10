"""Procedure code facets model for AI reasoning and clinical metadata"""

from sqlalchemy import Column, String, Integer, Boolean, PrimaryKeyConstraint, Index
from app.database import Base
from app.utils.db_types import JSONB


class ProcedureCodeFacet(Base):
    """AI reasoning facets for CPT and HCPCS procedure codes

    Stores metadata about body regions, complexity, service location,
    and other clinical attributes useful for AI reasoning, clinical
    decision support, and advanced search/filtering.

    These facets enable:
    - Faceted search (e.g., "find all moderate complexity E/M codes")
    - Clinical context matching (e.g., "surgical procedures on thorax")
    - Resource estimation (duration, complexity, anesthesia needs)
    - Billing intelligence (appropriate code selection)
    """

    __tablename__ = "procedure_code_facets"

    # Composite primary key
    code = Column(String(10), nullable=False,
                  comment="CPT or HCPCS code")
    code_system = Column(String(10), nullable=False,
                        comment="CPT or HCPCS")

    # Anatomical and body system classification
    body_region = Column(String(50), nullable=True,
                        comment="head_neck, thorax, abdomen, pelvis, spine, upper_extremity, lower_extremity, integumentary, multiple")
    body_system = Column(String(50), nullable=True,
                        comment="cardiovascular, respiratory, digestive, musculoskeletal, nervous, endocrine, etc.")

    # Procedure classification
    procedure_category = Column(String(50), nullable=True,
                               comment="evaluation, surgical, diagnostic_imaging, laboratory, therapeutic, preventive")
    procedure_type = Column(String(30), nullable=True,
                           comment="diagnostic, therapeutic, preventive, screening, palliative")

    # Complexity and resource intensity
    complexity_level = Column(String(20), nullable=True,
                             comment="simple, moderate, complex, highly_complex")
    typical_duration_mins = Column(Integer, nullable=True,
                                  comment="Typical procedure duration in minutes")
    relative_complexity_score = Column(Integer, nullable=True,
                                      comment="1-10 scale for procedure complexity")

    # Anesthesia information
    anesthesia_type = Column(String(30), nullable=True,
                            comment="none, local, regional, monitored, general")
    anesthesia_base_units = Column(Integer, nullable=True,
                                   comment="Base anesthesia units for billing")

    # Service setting and context
    service_location = Column(String(40), nullable=True,
                             comment="office, hospital_inpatient, hospital_outpatient, emergency, ambulatory_surgical_center, home, telehealth")
    provider_type = Column(String(50), nullable=True,
                          comment="physician, surgeon, nurse_practitioner, physician_assistant, therapist, technician, anesthesiologist")

    # Clinical and billing attributes
    is_bilateral = Column(Boolean, default=False,
                         comment="Whether procedure can be performed bilaterally")
    requires_modifier = Column(Boolean, default=False,
                              comment="Whether code commonly requires modifiers")
    age_specific = Column(Boolean, default=False,
                         comment="Whether code is age-restricted")
    gender_specific = Column(String(10), nullable=True,
                            comment="male, female, both, unspecified")

    # Special procedure flags
    is_add_on_code = Column(Boolean, default=False,
                           comment="CPT add-on code (cannot be billed alone)")
    is_unlisted_code = Column(Boolean, default=False,
                             comment="Unlisted procedure code")
    requires_special_report = Column(Boolean, default=False,
                                    comment="Requires special documentation")

    # E/M specific fields (for Evaluation and Management codes)
    em_level = Column(String(20), nullable=True,
                     comment="For E/M codes: level 1-5, critical_care, consultation")
    em_patient_type = Column(String(30), nullable=True,
                            comment="new_patient, established_patient, inpatient, outpatient")

    # Surgical procedure fields
    surgical_approach = Column(String(40), nullable=True,
                              comment="open, laparoscopic, endoscopic, percutaneous, robotic")
    is_major_surgery = Column(Boolean, default=False,
                             comment="Whether classified as major surgical procedure")

    # Imaging/Radiology fields
    imaging_modality = Column(String(40), nullable=True,
                             comment="xray, ct, mri, ultrasound, nuclear_medicine, pet")
    uses_contrast = Column(Boolean, default=False,
                          comment="Whether imaging uses contrast material")

    # Additional flexible metadata
    extra = Column(JSONB, nullable=True,
                  comment="Additional flexible metadata in JSON format")

    __table_args__ = (
        # Composite primary key
        PrimaryKeyConstraint('code', 'code_system',
                            name='pk_procedure_code_facets'),

        # Indexes for faceted search
        Index("ix_procedure_facets_body_region", "body_region"),
        Index("ix_procedure_facets_complexity", "complexity_level"),
        Index("ix_procedure_facets_category", "procedure_category"),
        Index("ix_procedure_facets_location", "service_location"),
        Index("ix_procedure_facets_em_level", "em_level"),

        # Composite indexes for common query patterns
        Index("ix_procedure_facets_body_system_category",
              "body_system", "procedure_category"),
        Index("ix_procedure_facets_category_complexity",
              "procedure_category", "complexity_level"),
    )

    def __repr__(self):
        return f"<ProcedureCodeFacet {self.code} ({self.code_system}) - {self.body_region}/{self.procedure_category}>"
