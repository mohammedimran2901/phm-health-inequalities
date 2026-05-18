"""
Inequality Metrics Calculations.

Provides methods for calculating:
- Slope Index of Inequality (SII)
- Relative Index of Inequality (RII)
- Gap analysis between quintiles
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from scipy import stats


def calculate_slope_index_inequality(
    df: pd.DataFrame,
    value_col: str,
    rank_col: str = 'imd_rank',
    population_col: Optional[str] = None
) -> Dict:
    """
    Calculate the Slope Index of Inequality (SII).
    
    SII represents the absolute difference in health outcomes between
    the most and least deprived areas, accounting for the full spectrum
    of deprivation.
    
    Args:
        df: DataFrame with health data
        value_col: Column name for the health indicator value
        rank_col: Column name for deprivation rank
        population_col: Optional column for population weights
        
    Returns:
        Dictionary with SII statistics
    """
    # Remove missing values
    data = df[[rank_col, value_col]].dropna()
    
    if population_col and population_col in df.columns:
        # Weighted linear regression
        weights = df[population_col].dropna()
        X = data[rank_col].values.reshape(-1, 1)
        y = data[value_col].values
        w = weights.values
        
        # Weighted least squares
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            data[rank_col], data[value_col]
        )
    else:
        # Simple linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            data[rank_col], data[value_col]
        )
        w = None
    
    # Calculate SII (difference between rank 1 and rank N)
    min_rank = data[rank_col].min()
    max_rank = data[rank_col].max()
    sii = slope * (max_rank - min_rank)
    
    # Calculate RII (Relative Index of Inequality)
    mean_value = data[value_col].mean()
    rii = (sii / mean_value) if mean_value != 0 else None
    
    return {
        'sii': sii,
        'rii': rii,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_error': std_err,
        'mean_value': mean_value,
        'n_observations': len(data)
    }


def calculate_gap_analysis(
    df: pd.DataFrame,
    value_col: str,
    quintile_col: str = 'imd_quintile',
    confidence_interval: float = 0.95
) -> Dict:
    """
    Calculate gap analysis between most and least deprived quintiles.
    
    Args:
        df: DataFrame with health data
        value_col: Column name for the health indicator value
        quintile_col: Column name for deprivation quintile
        confidence_interval: Confidence level for CI calculation
        
    Returns:
        Dictionary with gap analysis statistics
    """
    # Get Q1 (most deprived) and Q5 (least deprived)
    q1_data = df[df[quintile_col] == 1][value_col].dropna()
    q5_data = df[df[quintile_col] == 5][value_col].dropna()
    
    # Calculate means
    q1_mean = q1_data.mean()
    q5_mean = q5_data.mean()
    
    # Calculate absolute gap
    absolute_gap = q1_mean - q5_mean
    
    # Calculate relative gap
    relative_gap = (absolute_gap / q5_mean * 100) if q5_mean != 0 else None
    
    # Calculate confidence intervals
    def calc_ci(data, confidence=0.95):
        n = len(data)
        if n < 2:
            return None, None
        mean = data.mean()
        sem = stats.sem(data)
        ci = stats.t.interval(confidence, n-1, loc=mean, scale=sem)
        return ci
    
    q1_ci = calc_ci(q1_data, confidence_interval)
    q5_ci = calc_ci(q5_data, confidence_interval)
    
    # Calculate all quintile means
    quintile_means = df.groupby(quintile_col)[value_col].mean().to_dict()
    
    return {
        'q1_mean': q1_mean,
        'q5_mean': q5_mean,
        'absolute_gap': absolute_gap,
        'relative_gap_percent': relative_gap,
        'q1_ci_lower': q1_ci[0] if q1_ci else None,
        'q1_ci_upper': q1_ci[1] if q1_ci else None,
        'q5_ci_lower': q5_ci[0] if q5_ci else None,
        'q5_ci_upper': q5_ci[1] if q5_ci else None,
        'q1_n': len(q1_data),
        'q5_n': len(q5_data),
        'quintile_means': quintile_means
    }


def calculate_quintile_progression(
    df: pd.DataFrame,
    value_col: str,
    quintile_col: str = 'imd_quintile'
) -> pd.DataFrame:
    """
    Calculate mean values for each quintile with confidence intervals.
    
    Args:
        df: DataFrame with health data
        value_col: Column name for the health indicator value
        quintile_col: Column name for deprivation quintile
        
    Returns:
        DataFrame with quintile progression statistics
    """
    results = []
    
    for quintile in sorted(df[quintile_col].unique()):
        q_data = df[df[quintile_col] == quintile][value_col].dropna()
        
        if len(q_data) > 0:
            mean_val = q_data.mean()
            std_val = q_data.std()
            sem_val = stats.sem(q_data)
            
            # 95% confidence interval
            ci = stats.t.interval(0.95, len(q_data)-1, loc=mean_val, scale=sem_val)
            
            results.append({
                'quintile': quintile,
                'quintile_label': f'Q{int(quintile)}',
                'mean': mean_val,
                'std': std_val,
                'sem': sem_val,
                'ci_lower': ci[0],
                'ci_upper': ci[1],
                'n': len(q_data)
            })
    
    return pd.DataFrame(results)


def calculate_inequality_trend(
    df: pd.DataFrame,
    value_col: str,
    time_col: str,
    quintile_col: str = 'imd_quintile'
) -> pd.DataFrame:
    """
    Calculate inequality trends over time.
    
    Args:
        df: DataFrame with time-series health data
        value_col: Column name for the health indicator value
        time_col: Column name for time period
        quintile_col: Column name for deprivation quintile
        
    Returns:
        DataFrame with inequality trends by time period
    """
    results = []
    
    for time_period in sorted(df[time_col].unique()):
        time_data = df[df[time_col] == time_period]
        
        # Calculate gap for this time period
        gap = calculate_gap_analysis(time_data, value_col, quintile_col)
        
        # Calculate SII for this time period
        sii = calculate_slope_index_inequality(time_data, value_col)
        
        results.append({
            'time_period': time_period,
            'q1_mean': gap['q1_mean'],
            'q5_mean': gap['q5_mean'],
            'absolute_gap': gap['absolute_gap'],
            'relative_gap': gap['relative_gap_percent'],
            'sii': sii['sii'],
            'rii': sii['rii']
        })
    
    return pd.DataFrame(results)


def calculate_concentration_index(
    df: pd.DataFrame,
    value_col: str,
    rank_col: str = 'imd_rank',
    population_col: Optional[str] = None
) -> float:
    """
    Calculate the Concentration Index.
    
    Measures the extent to which health outcomes are concentrated
    among deprived populations.
    
    Args:
        df: DataFrame with health data
        value_col: Column name for the health indicator value
        rank_col: Column name for deprivation rank
        population_col: Optional column for population weights
        
    Returns:
        Concentration index value (-1 to 1)
    """
    data = df[[rank_col, value_col]].dropna()
    
    if population_col and population_col in df.columns:
        weights = df[population_col].dropna()
    else:
        weights = pd.Series(1, index=data.index)
    
    # Normalize ranks to 0-1 scale
    ranks = (data[rank_col] - data[rank_col].min()) / (data[rank_col].max() - data[rank_col].min())
    values = data[value_col]
    
    # Calculate concentration index
    mean_value = np.average(values, weights=weights)
    
    # Covariance between rank and health outcome
    covariance = np.cov(ranks, values, aweights=weights)[0, 1]
    
    concentration_index = 2 * covariance / mean_value
    
    return concentration_index


if __name__ == "__main__":
    # Test the inequality metrics
    print("Testing Inequality Metrics...")
    
    # Create sample data
    np.random.seed(42)
    n = 1000
    
    sample_df = pd.DataFrame({
        'imd_rank': range(1, n + 1),
        'imd_quintile': pd.qcut(range(1, n + 1), 5, labels=[1, 2, 3, 4, 5]),
        'health_value': 100 - np.linspace(0, 30, n) + np.random.normal(0, 5, n)
    })
    
    # Test SII
    print("\n1. Slope Index of Inequality:")
    sii_results = calculate_slope_index_inequality(sample_df, 'health_value')
    for key, value in sii_results.items():
        print(f"   {key}: {value:.4f}" if isinstance(value, float) else f"   {key}: {value}")
    
    # Test Gap Analysis
    print("\n2. Gap Analysis (Q1 vs Q5):")
    gap_results = calculate_gap_analysis(sample_df, 'health_value')
    for key, value in gap_results.items():
        if isinstance(value, dict):
            print(f"   {key}: {value}")
        elif isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")
    
    # Test Quintile Progression
    print("\n3. Quintile Progression:")
    progression = calculate_quintile_progression(sample_df, 'health_value')
    print(progression[['quintile', 'mean', 'ci_lower', 'ci_upper']])
    
    # Test Concentration Index
    print("\n4. Concentration Index:")
    ci = calculate_concentration_index(sample_df, 'health_value')
    print(f"   {ci:.4f}")
    
    print("\n✓ Inequality metrics test complete!")