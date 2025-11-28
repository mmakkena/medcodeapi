"""
Query Generation Domain Module

CDI query generation for physicians including:
- Non-leading question generation (ACDIS compliant)
- Multiple query types (clarification, specificity, linkage)
- Gap-driven query prioritization
- Query validation and quality scoring
"""

from domain.query_generation.generator import (
    CDIQueryGenerator,
    generate_cdi_queries,
)

__all__ = [
    "CDIQueryGenerator",
    "generate_cdi_queries",
]
