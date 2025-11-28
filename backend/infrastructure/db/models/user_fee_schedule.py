"""User fee schedule models for Contract Analyzer feature"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID, JSONB


class SavedCodeList(Base):
    """
    User's saved list of CPT codes (favorites/bookmarks).

    Allows users to create custom lists like "Cardiology Top 20" or
    "Common Office Visits" for quick access.
    """

    __tablename__ = "saved_code_lists"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # List of codes stored as JSON array
    # Format: [{"code": "99213", "notes": "optional user notes"}, ...]
    codes = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", backref="saved_code_lists")

    def __repr__(self):
        return f"<SavedCodeList {self.name}>"


class UserFeeScheduleUpload(Base):
    """
    Uploaded private fee schedule for contract analysis.

    Users upload their payer contract rates to compare against Medicare baseline.
    """

    __tablename__ = "user_fee_schedule_uploads"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Upload metadata
    name = Column(String(255), nullable=False)  # e.g., "Blue Cross 2024 Contract"
    payer_name = Column(String(255), nullable=True)  # Insurance company name
    contract_year = Column(Integer, nullable=True)

    # File info
    original_filename = Column(String(255), nullable=True)
    upload_status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, error
    error_message = Column(Text, nullable=True)

    # Analysis settings
    comparison_year = Column(Integer, nullable=False)  # CMS year to compare against
    comparison_zip = Column(String(5), nullable=True)  # ZIP code for locality

    # Summary stats (calculated after analysis)
    total_codes = Column(Integer, nullable=True)
    codes_below_medicare = Column(Integer, nullable=True)
    codes_above_medicare = Column(Integer, nullable=True)
    total_variance = Column(Float, nullable=True)  # Total $ variance

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", backref="fee_schedule_uploads")
    line_items = relationship("UserFeeScheduleLineItem", back_populates="upload", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserFeeScheduleUpload {self.name}>"


class UserFeeScheduleLineItem(Base):
    """
    Individual line item from uploaded fee schedule.

    Stores each CPT code and its contracted rate for comparison.
    """

    __tablename__ = "user_fee_schedule_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    upload_id = Column(GUID, ForeignKey("user_fee_schedule_uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Code info
    cpt_code = Column(String(10), nullable=False, index=True)
    modifier = Column(String(5), nullable=True)
    description = Column(Text, nullable=True)

    # User's contracted rate
    contracted_rate = Column(Float, nullable=False)

    # Volume (optional, for revenue impact calculation)
    annual_volume = Column(Integer, nullable=True)

    # Calculated comparison values (populated after analysis)
    medicare_rate = Column(Float, nullable=True)  # CMS rate for comparison
    variance = Column(Float, nullable=True)  # contracted_rate - medicare_rate
    variance_pct = Column(Float, nullable=True)  # variance as percentage
    is_below_medicare = Column(Integer, nullable=True, default=0)  # 1 if below, 0 if above/equal
    revenue_impact = Column(Float, nullable=True)  # variance * annual_volume

    # Relationship
    upload = relationship("UserFeeScheduleUpload", back_populates="line_items")

    __table_args__ = (
        Index("ix_fee_schedule_item_upload_code", "upload_id", "cpt_code"),
    )

    def __repr__(self):
        return f"<UserFeeScheduleLineItem {self.cpt_code}: ${self.contracted_rate}>"
