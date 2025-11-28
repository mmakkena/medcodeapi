"""
Revenue Optimization Domain Module

Revenue analysis and optimization including:
- E/M coding analysis (2021 guidelines)
- HCC risk adjustment opportunities
- DRG optimization
- Missing test/procedure revenue
- Documentation gap revenue impact
"""

from domain.revenue_optimization.optimizer import (
    RevenueOptimizer,
    analyze_revenue_opportunities,
    HistoryComponents,
    ExamComponents,
    MDMComponents,
)

__all__ = [
    "RevenueOptimizer",
    "analyze_revenue_opportunities",
    "HistoryComponents",
    "ExamComponents",
    "MDMComponents",
]
