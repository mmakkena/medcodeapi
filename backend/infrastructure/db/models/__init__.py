"""Database models"""

from infrastructure.db.models.user import User
from infrastructure.db.models.api_key import APIKey
from infrastructure.db.models.plan import Plan
from infrastructure.db.models.subscription import StripeSubscription
from infrastructure.db.models.usage_log import UsageLog
from infrastructure.db.models.support_ticket import SupportTicket

# ICD-10 models
from infrastructure.db.models.icd10_code import ICD10Code
from infrastructure.db.models.icd10_ai_facet import ICD10AIFacet
from infrastructure.db.models.icd10_synonym import ICD10Synonym
from infrastructure.db.models.icd10_relation import ICD10Relation

# CPT/HCPCS models (legacy and new)
from infrastructure.db.models.cpt_code import CPTCode  # Legacy simple model
from infrastructure.db.models.procedure_code import ProcedureCode
from infrastructure.db.models.procedure_code_synonym import ProcedureCodeSynonym
from infrastructure.db.models.procedure_code_facet import ProcedureCodeFacet

# Cross-system mappings
from infrastructure.db.models.code_mapping import CodeMapping

# CMS Fee Schedule models
from infrastructure.db.models.cms_locality import CMSLocality, ZIPToLocality
from infrastructure.db.models.mpfs_rate import MPFSRate, ConversionFactor
from infrastructure.db.models.user_fee_schedule import SavedCodeList, UserFeeScheduleUpload, UserFeeScheduleLineItem

# Knowledge Base models
from infrastructure.db.models.knowledge_base import (
    EMCode,
    InvestigationProtocol,
    CDIGuideline,
    DRGRule,
    BillingNote,
)

__all__ = [
    "User",
    "APIKey",
    "Plan",
    "StripeSubscription",
    "UsageLog",
    "SupportTicket",
    # ICD-10 models
    "ICD10Code",
    "ICD10AIFacet",
    "ICD10Synonym",
    "ICD10Relation",
    # CPT/HCPCS models
    "CPTCode",
    "ProcedureCode",
    "ProcedureCodeSynonym",
    "ProcedureCodeFacet",
    # Cross-system mappings
    "CodeMapping",
    # CMS Fee Schedule models
    "CMSLocality",
    "ZIPToLocality",
    "MPFSRate",
    "ConversionFactor",
    "SavedCodeList",
    "UserFeeScheduleUpload",
    "UserFeeScheduleLineItem",
    # Knowledge Base models
    "EMCode",
    "InvestigationProtocol",
    "CDIGuideline",
    "DRGRule",
    "BillingNote",
]
