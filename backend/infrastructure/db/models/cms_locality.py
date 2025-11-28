"""CMS Locality model for ZIP code to GPCI mapping"""

import uuid
from sqlalchemy import Column, String, Float, Integer, Index
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID


class CMSLocality(Base):
    """
    CMS Locality model mapping ZIP codes to geographic practice cost indices (GPCI).

    CMS divides the US into geographic localities, each with different GPCI values
    that affect Medicare reimbursement rates.

    GPCI components:
    - work_gpci: Physician work geographic adjustment
    - pe_gpci: Practice expense geographic adjustment
    - mp_gpci: Malpractice geographic adjustment
    """

    __tablename__ = "cms_localities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Locality identification
    mac_code = Column(String(5), nullable=False)  # Medicare Administrative Contractor
    locality_code = Column(String(10), nullable=False)  # CMS locality number
    locality_name = Column(String(255), nullable=False)  # Human-readable name
    state = Column(String(2), nullable=True, index=True)  # State abbreviation

    # GPCI values (Geographic Practice Cost Index)
    work_gpci = Column(Float, nullable=False, default=1.0)  # Work GPCI
    pe_gpci = Column(Float, nullable=False, default=1.0)    # Practice Expense GPCI
    mp_gpci = Column(Float, nullable=False, default=1.0)    # Malpractice GPCI

    # Year for versioning
    year = Column(Integer, nullable=False, index=True)

    # Indexes for efficient lookups
    __table_args__ = (
        Index("ix_cms_locality_code_year", "locality_code", "year"),
        Index("ix_cms_locality_mac_locality", "mac_code", "locality_code"),
    )

    def __repr__(self):
        return f"<CMSLocality {self.locality_code} - {self.locality_name} ({self.year})>"


class ZIPToLocality(Base):
    """
    Mapping from ZIP codes to CMS localities.

    A single ZIP code may span multiple localities (rare), so we store
    the primary locality mapping for each ZIP.
    """

    __tablename__ = "zip_to_locality"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    zip_code = Column(String(5), nullable=False, index=True)
    locality_code = Column(String(10), nullable=False, index=True)
    state = Column(String(2), nullable=True)
    carrier_code = Column(String(5), nullable=True)  # MAC/Carrier code

    # Year for versioning (ZIP mappings can change)
    year = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        Index("ix_zip_locality_year", "zip_code", "year"),
    )

    def __repr__(self):
        return f"<ZIPToLocality {self.zip_code} -> {self.locality_code}>"
