"""
Documentation Gaps Domain Module

Clinical documentation gap detection including:
- Missing specificity (type, severity, laterality)
- Missing vital signs for conditions
- Missing lab results for conditions
- Missing preventive screenings
- Missing linkages (complications, comorbidities)
- HEDIS quality measure gaps
"""

from domain.documentation_gaps.analyzer import (
    DocumentationGapAnalyzer,
    analyze_documentation_gaps,
)

__all__ = [
    "DocumentationGapAnalyzer",
    "analyze_documentation_gaps",
]
