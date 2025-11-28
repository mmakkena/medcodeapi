"""API v1 routes"""

from adapters.api.routes import (
    auth,
    icd10,
    cpt,
    procedure,
    suggest,
    api_keys,
    usage,
    billing,
    clinical_coding,
    admin,
    fee_schedule,
    # CDI Analysis routes
    cdi,
    hedis,
    revenue,
)

__all__ = [
    "auth",
    "icd10",
    "cpt",
    "procedure",
    "suggest",
    "api_keys",
    "usage",
    "billing",
    "clinical_coding",
    "admin",
    "fee_schedule",
    # CDI Analysis routes
    "cdi",
    "hedis",
    "revenue",
]
