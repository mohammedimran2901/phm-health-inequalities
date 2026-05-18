"""
Analytics module for health inequality calculations.

Provides Core20PLUS5 framework implementation and inequality metrics.
"""

from .core20plus5 import Core20PLUS5Analyzer
from .inequality_metrics import calculate_slope_index_inequality, calculate_gap_analysis

__all__ = ['Core20PLUS5Analyzer', 'calculate_slope_index_inequality', 'calculate_gap_analysis']