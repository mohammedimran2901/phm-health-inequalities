"""
Data acquisition modules for fetching health and socioeconomic data.
"""

from .fingertips_api import FingertipsAPI
from .imd_fetcher import IMDFetcher

__all__ = ['FingertipsAPI', 'IMDFetcher']