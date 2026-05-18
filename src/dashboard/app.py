#!/usr/bin/env python3
"""
PHM Health Inequalities Dashboard - Main Application.

Streamlit-based dashboard for visualizing health inequalities in England.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_acquisition.fingertips_api import FingertipsAPI
from data_acquisition.imd_fetcher import IMDFetcher
from analytics.core20plus5 import Core20PLUS5Analyzer
from analytics.inequality_metrics import (
    calculate_slope_index_inequality,
    calculate_gap_analysis,
    calculate_quintile_progression
)

# Page configuration
st.set_page_config(
    page_title="PHM Health Inequalities Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_imd_data():
    """Load IMD 2019 data with caching."""
    fetcher = IMDFetcher()
    return fetcher.get_combined_imd_data()


@st.cache_data
def get_core20_data(imd_df):
    """Get Core 20% areas."""
    analyzer = Core20PLUS5Analyzer(imd_df)
    return analyzer.get_core20_areas()


def render_home():
    """Render the home page."""
    st.markdown('<p class="main-header">🏥 PHM Health Inequalities Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Welcome to the Population Health Management (PHM) Health Inequalities Dashboard.
    
    This tool visualizes health inequalities across England using open data from:
    - **Index of Multiple Deprivation (IMD) 2019** - Official deprivation measure
    - **OHID Fingertips API** - Public health indicators
    - **Core20PLUS5 Framework** - NHS strategy for reducing inequalities
    
    ### 📊 Dashboard Sections
    
    Use the sidebar to navigate between:
    
    1. **📍 Geographic Overview** - Explore IMD scores and deprivation by area
    2. **📊 Inequality Analysis** - Gap analysis and Slope Index of Inequality
    3. **🎯 Core20PLUS5 Tracker** - Performance against NHS targets
    
    ### 🚀 Quick Stats
    """)
    
    # Load data
    imd_df = load_imd_data()
    core20_df = get_core20_data(imd_df)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total LSOAs",
            value=f"{len(imd_df):,}",
            help="Lower Layer Super Output Areas in England"
        )
    
    with col2:
        st.metric(
            label="Core 20% Areas",
            value=f"{len(core20_df):,}",
            help="Most deprived quintile (IMD Q1)"
        )
    
    with col3:
        st.metric(
            label="Local Authorities",
            value=f"{imd_df['lad19cd'].nunique()}",
            help="Number of councils"
        )
    
    with col4:
        avg_deprivation = core20_df['imd_score'].mean()
        st.metric(
            label="Avg IMD Score (Core 20%)",
            value=f"{avg_deprivation:.1f}",
            help="Higher = more deprived"
        )
    
    # Show quintile distribution
    st.markdown("### 📈 Deprivation Quintile Distribution")
    
    quintile_counts = imd_df['imd_quintile'].value_counts().sort_index()
    quintile_pct = (quintile_counts / len(imd_df) * 100).round(1)
    
    fig = go.Figure(data=[
        go.Bar(
            x=['Q1 (Most Deprived)', 'Q2', 'Q3', 'Q4', 'Q5 (Least Deprived)'],
            y=quintile_counts.values,
            text=[f"{v:,}<br>({p}%)" for v, p in zip(quintile_counts.values, quintile_pct.values)],
            textposition='auto',
            marker_color=['#d62728', '#ff7f0e', '#ffbb78', '#2ca02c', '#1f77b4']
        )
    ])
    
    fig.update_layout(
        title="Number of LSOAs by Deprivation Quintile",
        xaxis_title="IMD Quintile",
        yaxis_title="Number of LSOAs",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Most deprived areas table
    st.markdown("### 🔴 Most Deprived Areas (Top 10)")
    
    most_deprived = imd_df.nsmallest(10, 'imd_rank')[
        ['lsoa11nm', 'lad19nm', 'imd_rank', 'imd_score', 'imd_quintile']
    ]
    most_deprived.columns = ['LSOA Name', 'Local Authority', 'IMD Rank', 'IMD Score', 'Quintile']
    
    st.dataframe(most_deprived, use_container_width=True)


def render_geographic_overview():
    """Render the geographic overview page."""
    st.markdown('<p class="sub-header">📍 Geographic Overview</p>', unsafe_allow_html=True)
    
    imd_df = load_imd_data()
    
    # Filters
    st.sidebar.markdown("### 🎛️ Filters")
    
    selected_region = st.sidebar.selectbox(
        "Select Region",
        ["All England"] + sorted(imd_df['lad19nm'].unique().tolist())
    )
    
    view_metric = st.sidebar.selectbox(
        "View Metric",
        ["IMD Score", "IMD Rank", "Income Score", "Employment Score", "Health Score"]
    )
    
    metric_col = {
        "IMD Score": "imd_score",
        "IMD Rank": "imd_rank",
        "Income Score": "income_score",
        "Employment Score": "employment_score",
        "Health Score": "health_score"
    }[view_metric]
    
    # Filter data
    if selected_region != "All England":
        filtered_df = imd_df[imd_df['lad19nm'] == selected_region]
    else:
        filtered_df = imd_df
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Areas", f"{len(filtered_df):,}")
    
    with col2:
        st.metric(f"Mean {view_metric}", f"{filtered_df[metric_col].mean():.2f}")
    
    with col3:
        st.metric(f"Max {view_metric}", f"{filtered_df[metric_col].max():.2f}")
    
    with col4:
        st.metric(f"Min {view_metric}", f"{filtered_df[metric_col].min():.2f}")
    
    # Distribution histogram
    st.markdown(f"### 📊 {view_metric} Distribution")
    
    fig = px.histogram(
        filtered_df,
        x=metric_col,
        nbins=50,
        color='imd_quintile',
        color_discrete_map={
            1: '#d62728',
            2: '#ff7f0e',
            3: '#ffbb78',
            4: '#2ca02c',
            5: '#1f77b4'
        },
        labels={'imd_quintile': 'Quintile'},
        title=f"Distribution of {view_metric} by Deprivation Quintile"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top/Bottom areas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔴 Highest Deprivation (Top 10)")
        top10 = filtered_df.nlargest(10, metric_col if metric_col != 'imd_rank' else 'imd_score')[
            ['lsoa11nm', 'lad19nm', metric_col]
        ]
        st.dataframe(top10, use_container_width=True)
    
    with col2:
        st.markdown("### 🟢 Lowest Deprivation (Bottom 10)")
        bottom10 = filtered_df.nsmallest(10, metric_col if metric_col != 'imd_rank' else 'imd_score')[
            ['lsoa11nm', 'lad19nm', metric_col]
        ]
        st.dataframe(bottom10, use_container_width=True)
    
    # LA summary table
    st.markdown("### 📋 Local Authority Summary")
    
    la_summary = filtered_df.groupby('lad19nm').agg({
        'imd_score': ['mean', 'min', 'max'],
        'lsoa11cd': 'count',
        'imd_quintile': lambda x: (x == 1).sum()
    }).round(2)
    
    la_summary.columns = ['Mean IMD', 'Min IMD', 'Max IMD', 'Total LSOAs', 'Core20 Count']
    la_summary = la_summary.sort_values('Mean IMD', ascending=False)
    
    st.dataframe(la_summary, use_container_width=True)


def render_inequality_analysis():
    """Render the inequality analysis page."""
    st.markdown('<p class="sub-header">📊 Inequality Gap Analysis</p>', unsafe_allow_html=True)
    
    imd_df = load_imd_data()
    
    # Select indicator
    st.sidebar.markdown("### 📈 Analysis Options")
    
    available_metrics = [
        'imd_score', 'income_score', 'employment_score', 
        'education_score', 'health_score', 'crime_score',
        'housing_score', 'environment_score'
    ]
    
    selected_metric = st.sidebar.selectbox(
        "Select Metric for Analysis",
        available_metrics,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Calculate metrics
    sii_results = calculate_slope_index_inequality(imd_df, selected_metric)
    gap_results = calculate_gap_analysis(imd_df, selected_metric)
    quintile_prog = calculate_quintile_progression(imd_df, selected_metric)
    
    # Display SII and Gap metrics
    st.markdown("### 📐 Inequality Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Slope Index of Inequality (SII)",
            f"{sii_results['sii']:.2f}",
            help="Absolute difference between most and least deprived"
        )
    
    with col2:
        st.metric(
            "Relative Index of Inequality (RII)",
            f"{sii_results['rii']:.2%}" if sii_results['rii'] else "N/A",
            help="SII as proportion of population mean"
        )
    
    with col3:
        st.metric(
            "Absolute Gap (Q1 - Q5)",
            f"{gap_results['absolute_gap']:.2f}",
            help="Difference between most and least deprived quintiles"
        )
    
    with col4:
        st.metric(
            "Relative Gap",
            f"{gap_results['relative_gap_percent']:.1f}%" if gap_results['relative_gap_percent'] else "N/A",
            help="Gap as percentage of least deprived quintile"
        )
    
    # Quintile progression chart
    st.markdown("### 📊 Quintile Progression")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=quintile_prog['quintile_label'],
        y=quintile_prog['mean'],
        mode='lines+markers',
        name='Mean Value',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=10)
    ))
    
    # Add confidence intervals
    fig.add_trace(go.Scatter(
        x=quintile_prog['quintile_label'].tolist() + quintile_prog['quintile_label'].tolist()[::-1],
        y=quintile_prog['ci_upper'].tolist() + quintile_prog['ci_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(31, 119, 180, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% Confidence Interval'
    ))
    
    fig.update_layout(
        title=f"{selected_metric.replace('_', ' ').title()} by Deprivation Quintile",
        xaxis_title="Deprivation Quintile",
        yaxis_title="Mean Value",
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Quintile comparison bar chart
    st.markdown("### 📊 Quintile Comparison")
    
    fig2 = px.bar(
        quintile_prog,
        x='quintile_label',
        y='mean',
        error_y='sem',
        color='quintile',
        color_continuous_scale='RdYlBu',
        labels={'mean': 'Mean Value', 'quintile_label': 'Quintile'},
        title=f"Mean {selected_metric.replace('_', ' ').title()} by Quintile"
    )
    
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed statistics table
    st.markdown("### 📋 Detailed Statistics by Quintile")
    
    stats_df = quintile_prog[['quintile_label', 'mean', 'std', 'ci_lower', 'ci_upper', 'n']]
    stats_df.columns = ['Quintile', 'Mean', 'Std Dev', 'CI Lower', 'CI Upper', 'N']
    
    st.dataframe(stats_df.round(2), use_container_width=True)


def render_core20plus5_tracker():
    """Render the Core20PLUS5 tracker page."""
    st.markdown('<p class="sub-header">🎯 Core20PLUS5 Tracker</p>', unsafe_allow_html=True)
    
    imd_df = load_imd_data()
    analyzer = Core20PLUS5Analyzer(imd_df)
    
    # Get LA selection
    st.sidebar.markdown("### 🎯 Tracker Options")
    
    la_list = ["All England"] + sorted(imd_df['lad19nm'].unique().tolist())
    selected_la = st.sidebar.selectbox("Select Local Authority", la_list)
    
    # Display Core 20% stats
    st.markdown("### 📊 Core 20% (Most Deprived Areas) Summary")
    
    if selected_la != "All England":
        la_data = imd_df[imd_df['lad19nm'] == selected_la]
        core20_in_la = la_data[la_data['imd_quintile'] == 1]
        core20_pct = (len(core20_in_la) / len(la_data)) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total LSOAs in LA", f"{len(la_data)}")
        
        with col2:
            st.metric("Core 20% LSOAs", f"{len(core20_in_la)}")
        
        with col3:
            st.metric("Core 20% Percentage", f"{core20_pct:.1f}%")
        
        # Domain scores for Core 20%
        st.markdown("### 📈 Domain Scores (Core 20% Areas)")
        
        domain_cols = ['income_score', 'employment_score', 'education_score', 
                      'health_score', 'crime_score', 'housing_score', 'environment_score']
        
        domain_means = core20_in_la[domain_cols].mean()
        
        fig = px.bar(
            x=domain_means.index.str.replace('_score', '').str.title(),
            y=domain_means.values,
            labels={'x': 'Domain', 'y': 'Mean Score'},
            title="IMD Domain Scores - Core 20% Areas",
            color=domain_means.values,
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison with national average
        st.markdown("### 🔄 Comparison with National Average")
        
        national_core20 = imd_df[imd_df['imd_quintile'] == 1]
        
        comparison_data = []
        for domain in domain_cols:
            comparison_data.append({
                'Domain': domain.replace('_score', '').title(),
                'This LA': core20_in_la[domain].mean(),
                'National Average': national_core20[domain].mean(),
                'Difference': core20_in_la[domain].mean() - national_core20[domain].mean()
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            name=selected_la,
            x=comparison_df['Domain'],
            y=comparison_df['This LA'],
            marker_color='#1f77b4'
        ))
        
        fig2.add_trace(go.Bar(
            name='National Average',
            x=comparison_df['Domain'],
            y=comparison_df['National Average'],
            marker_color='#ff7f0e'
        ))
        
        fig2.update_layout(
            barmode='group',
            title="Core 20% Domain Scores: LA vs National",
            height=500
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Show comparison table
        st.dataframe(comparison_df.round(2), use_container_width=True)
    
    else:
        # National view
        core20_national = analyzer.get_core20_areas()
        la_summary = analyzer.get_core20_by_la()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Core 20% LSOAs", f"{len(core20_national):,}")
        
        with col2:
            st.metric("LAs with Core 20% Areas", f"{len(la_summary)}")
        
        with col3:
            avg_pct = la_summary['core20_percentage'].mean()
            st.metric("Avg Core 20% per LA", f"{avg_pct:.1f}%")
        
        # Top LAs by Core 20%
        st.markdown("### 🏆 Top 10 LAs by Core 20% Percentage")
        
        top10 = la_summary.head(10)[['lad19nm', 'core20_count', 'core20_percentage']]
        top10.columns = ['Local Authority', 'Core 20% Count', 'Core 20% Percentage']
        
        fig = px.bar(
            top10,
            x='Core 20% Percentage',
            y='Local Authority',
            orientation='h',
            color='Core 20% Percentage',
            color_continuous_scale='Reds',
            text='Core 20% Percentage'
        )
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Full LA table
        st.markdown("### 📋 All Local Authorities")
        st.dataframe(la_summary[['lad19nm', 'core20_count', 'total_lsoas', 'core20_percentage']].round(2), 
                    use_container_width=True)


def main():
    """Main function to run the dashboard."""
    # Sidebar navigation
    st.sidebar.title("🏥 Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        ["🏠 Home", "📍 Geographic Overview", "📊 Inequality Analysis", "🎯 Core20PLUS5 Tracker"]
    )
    
    # Render selected page
    if page == "🏠 Home":
        render_home()
    elif page == "📍 Geographic Overview":
        render_geographic_overview()
    elif page == "📊 Inequality Analysis":
        render_inequality_analysis()
    elif page == "🎯 Core20PLUS5 Tracker":
        render_core20plus5_tracker()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📊 About
    Built with open data from:
    - UK Government (IMD 2019)
    - NHS England (OHID Fingertips)
    
    **Version**: 0.1.0
    """)


if __name__ == "__main__":
    main()