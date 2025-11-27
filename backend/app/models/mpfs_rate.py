"""Medicare Physician Fee Schedule (MPFS) Rate model"""

import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, Index
from app.database import Base
from app.utils.db_types import GUID


class MPFSRate(Base):
    """
    Medicare Physician Fee Schedule (MPFS) Rate model.

    Stores the Relative Value Units (RVUs) for each CPT/HCPCS code.
    The actual payment is calculated as:
    Payment = [(Work RVU * Work GPCI) + (PE RVU * PE GPCI) + (MP RVU * MP GPCI)] * Conversion Factor

    There are two Practice Expense (PE) RVU values:
    - Facility: When service is performed in a facility (hospital, ASC)
    - Non-Facility: When service is performed in a non-facility (office)
    """

    __tablename__ = "mpfs_rates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Code identification
    hcpcs_code = Column(String(10), nullable=False, index=True)  # CPT or HCPCS code
    modifier = Column(String(5), nullable=True)  # TC, 26, 53, etc.
    description = Column(Text, nullable=True)

    # Status indicators
    status_code = Column(String(1), nullable=True)  # A=Active, D=Deleted, etc.
    pctc_indicator = Column(String(1), nullable=True)  # PC/TC indicator

    # Work RVU
    work_rvu = Column(Float, nullable=True, default=0.0)

    # Practice Expense (PE) RVUs
    non_facility_pe_rvu = Column(Float, nullable=True, default=0.0)  # Office setting
    facility_pe_rvu = Column(Float, nullable=True, default=0.0)      # Hospital/ASC setting

    # Malpractice RVU
    mp_rvu = Column(Float, nullable=True, default=0.0)

    # Total RVUs (pre-calculated for convenience)
    non_facility_total = Column(Float, nullable=True, default=0.0)
    facility_total = Column(Float, nullable=True, default=0.0)

    # Global Days
    global_days = Column(String(5), nullable=True)  # 000, 010, 090, XXX, YYY, ZZZ, MMM

    # Multiple Procedure Indicator
    mult_proc = Column(String(1), nullable=True)

    # Bilateral Surgery Indicator
    bilateral_surgery = Column(String(1), nullable=True)

    # Assistant Surgery Indicators
    assistant_surgery = Column(String(1), nullable=True)
    co_surgeons = Column(String(1), nullable=True)
    team_surgery = Column(String(1), nullable=True)

    # Endoscopic Base Code
    endo_base = Column(String(10), nullable=True)

    # Conversion Factor Indicator (0 or 1, for diagnostic vs. non-diagnostic)
    conv_factor_indicator = Column(String(1), nullable=True)

    # Physician Supervision
    physician_supervision = Column(String(2), nullable=True)

    # Diagnostic Imaging Family Indicator
    diag_imaging_family = Column(String(2), nullable=True)

    # Non-Facility PE Used for OPPS Payment
    non_fac_pe_used_for_opps = Column(Boolean, nullable=True, default=False)

    # Year/Quarter versioning
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=True, default=1)  # 1-4 for quarterly updates

    # Effective dates
    effective_date = Column(String(10), nullable=True)  # YYYY-MM-DD

    # Indexes for efficient lookups
    __table_args__ = (
        Index("ix_mpfs_code_year", "hcpcs_code", "year"),
        Index("ix_mpfs_code_mod_year", "hcpcs_code", "modifier", "year"),
    )

    def __repr__(self):
        return f"<MPFSRate {self.hcpcs_code} ({self.year})>"


class ConversionFactor(Base):
    """
    CMS Conversion Factor by year.

    The conversion factor converts total RVUs to dollar amounts.
    It's updated annually (usually decreasing due to SGR/MACRA adjustments).
    """

    __tablename__ = "conversion_factors"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    year = Column(Integer, nullable=False, unique=True, index=True)
    conversion_factor = Column(Float, nullable=False)

    # Some years have different factors for different categories
    # (anesthesia has its own conversion factor)
    anesthesia_conversion_factor = Column(Float, nullable=True)

    # Effective date (usually January 1)
    effective_date = Column(String(10), nullable=True)

    # Notes about changes
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ConversionFactor {self.year}: ${self.conversion_factor}>"
