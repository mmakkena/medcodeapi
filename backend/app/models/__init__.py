"""Database models"""

from app.models.user import User
from app.models.api_key import APIKey
from app.models.plan import Plan
from app.models.subscription import StripeSubscription
from app.models.usage_log import UsageLog
from app.models.support_ticket import SupportTicket

# ICD-10 models
from app.models.icd10_code import ICD10Code
from app.models.icd10_ai_facet import ICD10AIFacet
from app.models.icd10_synonym import ICD10Synonym
from app.models.icd10_relation import ICD10Relation

# CPT/HCPCS models (legacy and new)
from app.models.cpt_code import CPTCode  # Legacy simple model
from app.models.procedure_code import ProcedureCode
from app.models.procedure_code_synonym import ProcedureCodeSynonym
from app.models.procedure_code_facet import ProcedureCodeFacet

# Cross-system mappings
from app.models.code_mapping import CodeMapping

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
]
