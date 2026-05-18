"""
Core20PLUS5 Framework Implementation.

The NHS Core20PLUS5 framework targets:
- Core 20: The most deprived 20% of areas (IMD Quintile 1)
- PLUS: Additional inclusion criteria (learning disabilities, care homes, etc.)
- 5 Clinical Areas: Maternity, SMI, Respiratory, Cancer, Hypertension
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Core20PLUS5Analyzer:
    """
    Analyzer for the NHS Core20PLUS5 framework.
    
    Identifies the Core 20% most deprived areas and tracks performance
    against the 5 target clinical areas.
    """
    
    # The 5 clinical areas and their indicator mappings
    CLINICAL_AREAS = {
        'maternity': {
            'name': 'Maternity',
            'indicators': ['maternity_early_access', 'low_birth_weight'],
            'description': 'Early access to maternity services'
        },
        'severe_mental_illness': {
            'name': 'Severe Mental Illness',
            'indicators': ['severe_mental_illness'],
            'description': 'SMI prevalence and mortality'
        },
        'chronic_respiratory': {
            'name': 'Chronic Respiratory Disease',
            'indicators': ['copd_prevalence', 'asthma_prevalence'],
            'description': 'COPD and asthma management'
        },
        'early_cancer_diagnosis': {
            'name': 'Early Cancer Diagnosis',
            'indicators': ['cancer_emergency_presentations', 'cancer_screening_breast', 'cancer_screening_cervical'],
            'description': 'Emergency presentations and screening coverage'
        },
        'hypertension': {
            'name': 'Hypertension',
            'indicators': ['hypertension_prevalence', 'cvd_prevalence'],
            'description': 'Hypertension prevalence and CVD management'
        }
    }
    
    def __init__(self, imd_df: Optional[pd.DataFrame] = None):
        """
        Initialize the Core20PLUS5 analyzer.
        
        Args:
            imd_df: IMD 2019 DataFrame, or None to fetch automatically
        """
        if imd_df is None:
            from ..data_acquisition.imd_fetcher import IMDFetcher
            fetcher = IMDFetcher()
            self.imd_df = fetcher.get_combined_imd_data()
        else:
            self.imd_df = imd_df
        
        logger.info(f"Core20PLUS5 Analyzer initialized with {len(self.imd_df)} LSOAs")
    
    def get_core20_areas(self) -> pd.DataFrame:
        """
        Get the Core 20% most deprived areas (IMD Quintile 1).
        
        Returns:
            DataFrame with Core 20% LSOAs
        """
        core20 = self.imd_df[self.imd_df['imd_quintile'] == 1].copy()
        logger.info(f"Core 20%: {len(core20)} LSOAs identified")
        return core20
    
    def get_core20_by_la(self) -> pd.DataFrame:
        """
        Get Core 20% summary by Local Authority.
        
        Returns:
            DataFrame with LA-level Core 20% statistics
        """
        # Group by LA and calculate Core 20% metrics
        la_summary = self.imd_df.groupby(['lad19cd', 'lad19nm']).agg({
            'imd_quintile': lambda x: (x == 1).sum(),  # Count of Q1 LSOAs
            'lsoa11cd': 'count'  # Total LSOAs
        }).reset_index()
        
        la_summary.columns = ['lad19cd', 'lad19nm', 'core20_count', 'total_lsoas']
        la_summary['core20_percentage'] = (
            la_summary['core20_count'] / la_summary['total_lsoas'] * 100
        ).round(2)
        
        # Sort by Core 20% percentage
        la_summary = la_summary.sort_values('core20_percentage', ascending=False)
        
        return la_summary
    
    def calculate_core20_indicator_rates(
        self,
        health_df: pd.DataFrame,
        indicator_col: str = 'indicator_id',
        value_col: str = 'value'
    ) -> Dict[str, Dict]:
        """
        Calculate health indicator rates for Core 20% vs overall population.
        
        Args:
            health_df: Health indicators DataFrame
            indicator_col: Column name for indicator ID
            value_col: Column name for indicator value
            
        Returns:
            Dictionary with Core 20% and overall rates by indicator
        """
        # Get Core 20% LSOA codes
        core20_lsoas = set(self.get_core20_areas()['lsoa11cd'])
        
        results = {}
        
        for indicator in health_df[indicator_col].unique():
            indicator_data = health_df[health_df[indicator_col] == indicator]
            
            # Overall rate
            overall_rate = indicator_data[value_col].mean()
            
            # Core 20% rate
            core20_data = indicator_data[
                indicator_data['area_code'].isin(core20_lsoas)
            ]
            core20_rate = core20_data[value_col].mean() if len(core20_data) > 0 else None
            
            # Calculate ratio
            if core20_rate and overall_rate:
                ratio = core20_rate / overall_rate
            else:
                ratio = None
            
            results[indicator] = {
                'overall_rate': overall_rate,
                'core20_rate': core20_rate,
                'core20_ratio': ratio,
                'core20_count': len(core20_data),
                'overall_count': len(indicator_data)
            }
        
        return results
    
    def get_clinical_area_performance(
        self,
        health_df: pd.DataFrame,
        la_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get performance metrics for the 5 clinical areas.
        
        Args:
            health_df: Health indicators DataFrame
            la_code: Optional LA code to filter by
            
        Returns:
            DataFrame with clinical area performance metrics
        """
        results = []
        
        for area_key, area_info in self.CLINICAL_AREAS.items():
            for indicator_key in area_info['indicators']:
                # Filter data for this indicator
                indicator_data = health_df[
                    health_df['indicator_key'] == indicator_key
                ]
                
                if la_code:
                    indicator_data = indicator_data[
                        indicator_data['lad19cd'] == la_code
                    ]
                
                if len(indicator_data) == 0:
                    continue
                
                # Calculate metrics
                avg_value = indicator_data['value'].mean()
                core20_data = indicator_data[
                    indicator_data['imd_quintile'] == 1
                ]
                core20_value = core20_data['value'].mean() if len(core20_data) > 0 else None
                
                results.append({
                    'clinical_area': area_info['name'],
                    'clinical_area_key': area_key,
                    'indicator': indicator_key,
                    'description': area_info['description'],
                    'average_value': avg_value,
                    'core20_value': core20_value,
                    'data_points': len(indicator_data),
                    'core20_data_points': len(core20_data)
                })
        
        return pd.DataFrame(results)
    
    def generate_scorecard(self, la_code: str, health_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate a Core20PLUS5 scorecard for a specific Local Authority.
        
        Args:
            la_code: Local Authority code
            health_df: Health indicators DataFrame
            
        Returns:
            DataFrame with scorecard metrics
        """
        # Get LA info
        la_info = self.imd_df[self.imd_df['lad19cd'] == la_code]
        if len(la_info) == 0:
            raise ValueError(f"Local Authority {la_code} not found")
        
        la_name = la_info['lad19nm'].iloc[0]
        
        # Calculate Core 20% stats for this LA
        la_lsoas = self.imd_df[self.imd_df['lad19cd'] == la_code]
        core20_count = (la_lsoas['imd_quintile'] == 1).sum()
        core20_pct = (core20_count / len(la_lsoas)) * 100
        
        # Get clinical area performance
        clinical_performance = self.get_clinical_area_performance(health_df, la_code)
        
        # Add national comparison
        national_performance = self.get_clinical_area_performance(health_df)
        
        # Merge and calculate percentiles
        scorecard = clinical_performance.merge(
            national_performance[['indicator', 'average_value']],
            on='indicator',
            suffixes=('', '_national')
        )
        
        scorecard['la_name'] = la_name
        scorecard['core20_pct'] = core20_pct
        scorecard['vs_national'] = (
            scorecard['average_value'] / scorecard['average_value_national']
        )
        
        # Add traffic light status
        scorecard['status'] = scorecard['vs_national'].apply(
            lambda x: 'Green' if x < 0.95 else ('Red' if x > 1.05 else 'Amber')
        )
        
        return scorecard
    
    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics for the Core20PLUS5 framework.
        
        Returns:
            Dictionary with summary statistics
        """
        core20 = self.get_core20_areas()
        
        return {
            'total_lsoas': len(self.imd_df),
            'core20_count': len(core20),
            'core20_percentage': (len(core20) / len(self.imd_df)) * 100,
            'lad_count': self.imd_df['lad19cd'].nunique(),
            'core20_by_domain': {
                'income': core20['income_score'].mean(),
                'employment': core20['employment_score'].mean(),
                'education': core20['education_score'].mean(),
                'health': core20['health_score'].mean(),
                'crime': core20['crime_score'].mean(),
                'housing': core20['housing_score'].mean(),
                'environment': core20['environment_score'].mean()
            },
            'most_deprived_la': self.get_core20_by_la().iloc[0]['lad19nm']
        }


if __name__ == "__main__":
    # Test the analyzer
    print("Testing Core20PLUS5 Analyzer...")
    
    analyzer = Core20PLUS5Analyzer()
    
    # Test 1: Get Core 20% areas
    print("\n1. Core 20% Areas:")
    core20 = analyzer.get_core20_areas()
    print(f"   Count: {len(core20)} LSOAs")
    print(f"   Sample: {core20[['lsoa11nm', 'lad19nm', 'imd_rank']].head()}")
    
    # Test 2: Get Core 20% by LA
    print("\n2. Top 5 LAs by Core 20% percentage:")
    la_summary = analyzer.get_core20_by_la()
    print(la_summary.head()[['lad19nm', 'core20_count', 'core20_percentage']])
    
    # Test 3: Summary statistics
    print("\n3. Summary Statistics:")
    stats = analyzer.get_summary_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"      {k}: {v:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print("\n✓ Core20PLUS5 Analyzer test complete!")