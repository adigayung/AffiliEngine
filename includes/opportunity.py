"""
Opportunity Engine V5

Public API

Router cukup import:

from includes.opportunity import calculate_opportunity
"""

from .opportunity.engine import calculate_opportunity

__all__ = [
    "calculate_opportunity",
]