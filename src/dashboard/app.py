#!/usr/bin/env python3
"""
PHM Health Inequalities Dashboard - Premium Version.
Minimalist, Google/AI-inspired interface with freemium model.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
import base64
from datetime import datetime, timedelta
import json
import urllib.parse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_acquisition.imd_fetcher import IMDFetcher
from analytics.core20plus5 import Core20PLUS5Analyzer
from analytics.inequality_metrics import (
    calculate_slope_index_inequality,
    calculate_gap_analysis,
    calculate_quintile_progression
)

# =============================================================================
# PAGE CONFIGURATION & THEME
# =============================================================================

st.set_page_config(
    page_title="HealthMap AI | Population Health Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/mohammedimran2901/phm-health-inequalities',
        'Report a bug': 'https://github.com/mohammedimran2901/phm-health-inequalities/issues',
        'About': 'AI-powered health inequalities analysis for NHS Integrated Care Systems'
    }
)

# =============================================================================
# GOOGLE/AI-INSPIRED CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(180deg, #FAFBFC 0%, #F0F4F8 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #1A1A2E;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    /* Google-style Search Bar */
    .search-container {
        background: white;
        border-radius: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
        padding: 16px 24px;
        margin: 20px 0;
        border: 1px solid #E8EAED;
        transition: all 0.2s ease;
    }
    
    .search-container:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.08);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #E8EAED;
        transition: all 0.2s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 12px 24px rgba(0,0,0,0.08);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1A73E8;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #5F6368;
        font-weight: 500;
        margin-top: 4px;
    }
    
    /* AI Chat Interface */
    .chat-bubble {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #1A73E8;
    }
    
    .chat-bubble.user {
        background: #E8F0FE;
        border-left-color: #34A853;
    }
    
    /* Premium Badge */
    .premium-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Buttons */
    .stButton>button {
        background: #1A73E8;
        color: white;
        border-radius: 24px;
        padding: 12px 32px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 8px rgba(26,115,232,0.3);
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: #1557B0;
        box-shadow: 0 4px 16px rgba(26,115,232,0.4);
        transform: translateY(-1px);
    }
    
    /* Premium Button */
    .premium-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 24px;
        padding: 14px 36px;
        font-weight: 600;
        border: none;
        font-size: 1rem;
    }
    
    /* Navigation */
    .nav-pill {
        background: white;
        border-radius: 30px;
        padding: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        display: inline-flex;
        gap: 8px;
    }
    
    .nav-pill button {
        background: transparent;
        border: none;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: 500;
        color: #5F6368;
        transition: all 0.2s;
    }
    
    .nav-pill button.active {
        background: #E8F0FE;
        color: #1A73E8;
    }
    
    /* Insights Panel */
    .insight-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #667eea30;
        margin: 8px 0;
    }
    
    /* Progress Bars */
    .progress-container {
        background: #E8EAED;
        border-radius: 8px;
        height: 8px;
        overflow: hidden;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #34A853, #1A73E8);
        height: 100%;
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    
    /* Data Table */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Freemium Banner */
    .freemium-banner {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border: 1px solid #FFD54F;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Share Buttons */
    .share-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        margin: 4px;
    }
    
    .share-twitter { background: #1DA1F2; color: white; }
    .share-linkedin { background: #0A66C2; color: white; }
    .share-facebook { background: #4267B2; color: white; }
    
    .share-btn:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Hide Streamlit default */
    .css-1d391kg {display: none;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FREEMIUM & USAGE TRACKING
# =============================================================================

def init_session_state():
    """Initialize session state for freemium model."""
    if 'usage' not in st.session_state:
        st.session_state.usage = {
            'searches': 0,
            'exports': 0,
            'analyses': 0,
            'last_reset': datetime.now().isoformat()
        }
    if 'is_premium' not in st.session_state:
        st.session_state.is_premium = False
    if 'shared' not in st.session_state:
        st.session_state.shared = False
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'search'

def check_usage_limit(action_type):
    """Check if user has exceeded free tier limits."""
    if st.session_state.is_premium or st.session_state.shared:
        return True
    
    limits = {
        'searches': 5,
        'exports': 2,
        'analyses': 3
    }
    
    return st.session_state.usage[action_type] < limits[action_type]

def increment_usage(action_type):
    """Increment usage counter."""
    st.session_state.usage[action_type] += 1

def get_remaining(action_type):
    """Get remaining free tier usage."""
    if st.session_state.is_premium or st.session_state.shared:
        return float('inf')
    limits = {'searches': 5, 'exports': 2, 'analyses': 3}
    return limits[action_type] - st.session_state.usage[action_type]

# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(ttl=3600)
def load_imd_data():
    """Load IMD 2019 data with caching."""
    fetcher = IMDFetcher()
    return fetcher.get_combined_imd_data()

# =============================================================================
# SOCIAL SHARING
# =============================================================================

def get_share_urls():
    """Generate social media share URLs."""
    app_url = "https://phm-health-inequalities.streamlit.app"
    text = "🔬 Just discovered HealthMap AI - powerful health inequalities analysis for NHS ICS & trusts. Check it out!"
    
    return {
        'twitter': f"https://twitter.com/intent/tweet?text={urllib.parse.quote(text)}&url={urllib.parse.quote(app_url)}",
        'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(app_url)}",
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(app_url)}"
    }

def render_share_buttons():
    """Render social share buttons."""
    st.markdown("### 📢 Share to Unlock Premium")
    st.markdown("Share HealthMap AI to get unlimited access:")
    
    urls = get_share_urls()
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
        <a href="{urls['twitter']}" target="_blank" class="share-btn share-twitter">
            🐦 Twitter
        </a>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <a href="{urls['linkedin']}" target="_blank" class="share-btn share-linkedin">
            💼 LinkedIn
        </a>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"""
        <a href="{urls['facebook']}" target="_blank" class="share-btn share-facebook">
            📘 Facebook
        </a>
        """, unsafe_allow_html=True)
    
    # Manual unlock option
    st.markdown("---")
    if st.button("✅ I've Shared - Unlock Premium", use_container_width=True):
        st.session_state.shared = True
        st.rerun()

# =============================================================================
# PREMIUM MODAL
# =============================================================================

def render_premium_modal():
    """Render premium upgrade modal."""
    st.markdown("## ⭐ Upgrade to HealthMap AI Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Free Tier
        ✅ 5 area searches/month  
        ✅ 3 inequality analyses  
        ✅ 2 data exports  
        ✅ Basic visualizations  
        ---
        **Current Usage:**
        """)
        st.progress(min(st.session_state.usage['searches'] / 5, 1.0), 
                   text=f"Searches: {st.session_state.usage['searches']}/5")
        st.progress(min(st.session_state.usage['analyses'] / 3, 1.0), 
                   text=f"Analyses: {st.session_state.usage['analyses']}/3")
        st.progress(min(st.session_state.usage['exports'] / 2, 1.0), 
                   text=f"Exports: {st.session_state.usage['exports']}/2")
    
    with col2:
        st.markdown("""
        ### Pro Tier - £49/month
        🚀 Unlimited searches  
        📊 Advanced AI insights  
        📥 Unlimited exports (CSV, Excel, PDF)  
        🎯 Custom ICB/Trust reports  
        🔗 API access  
        📞 Priority support  
        """)
        
        st.markdown("### 💳 Choose Payment")
        
        payment_col1, payment_col2 = st.columns(2)
        with payment_col1:
            if st.button("💳 Pay with Card", use_container_width=True):
                st.success("Redirecting to Stripe... (Demo)")
                st.session_state.is_premium = True
                st.rerun()
        with payment_col2:
            if st.button("🏦 NHS Invoice", use_container_width=True):
                st.info("Invoice sent to your NHS email")
                st.session_state.is_premium = True
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎁 Or Share for Free Access")
    render_share_buttons()

# =============================================================================
# AI INSIGHTS
# =============================================================================

def generate_ai_insights(data, metric_name):
    """Generate AI-style insights from data."""
    insights = []
    
    # Core 20% insight
    core20_pct = (data['imd_quintile'] == 1).mean() * 100
    insights.append(f"🎯 **Core 20% Focus:** {core20_pct:.1f}% of areas are in the most deprived quintile")
    
    # Inequality gap
    q1_mean = data[data['imd_quintile'] == 1][metric_name].mean()
    q5_mean = data[data['imd_quintile'] == 5][metric_name].mean()
    gap = abs(q1_mean - q5_mean)
    
    if gap > 0:
        insights.append(f"📊 **Inequality Gap:** {gap:.2f} point difference between most/least deprived")
    
    # Trend
    if 'lad19nm' in data.columns:
        worst_la = data.groupby('lad19nm')[metric_name].mean().idxmax()
        insights.append(f"⚠️ **Priority Area:** {worst_la} shows highest deprivation scores")
    
    return insights

# =============================================================================
# MAIN VIEWS
# =============================================================================

def render_search_view(imd_df):
    """Render Google-style search interface."""
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 3rem; font-weight: 700; color: #1A1A2E; margin-bottom: 8px;">
            HealthMap <span style="color: #1A73E8;">AI</span>
        </h1>
        <p style="font-size: 1.125rem; color: #5F6368; margin-bottom: 32px;">
            Population Health Intelligence for NHS Integrated Care Systems
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search Bar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_query = st.text_input(
            "",
            placeholder="🔍 Search by area, ICB, or Local Authority...",
            key="main_search",
            label_visibility="collapsed"
        )
        
        if search_query and not check_usage_limit('searches'):
            st.error("⚠️ Search limit reached. Upgrade to Pro or share to continue.")
            render_premium_modal()
            return
    
    # Quick Stats Row
    if not search_query:
        cols = st.columns(4)
        metrics = [
            ("32,844", "LSOAs Analyzed", "📍"),
            ("6,569", "Core 20% Areas", "🎯"),
            ("317", "Local Authorities", "🏛️"),
            ("42", "ICS/Trusts", "🏥")
        ]
        
        for col, (value, label, icon) in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
                    <div class="metric-value" style="font-size: 2rem;">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Search Results
    if search_query:
        increment_usage('searches')
        
        # Filter data
        mask = (
            imd_df['lsoa11nm'].str.contains(search_query, case=False, na=False) |
            imd_df['lad19nm'].str.contains(search_query, case=False, na=False)
        )
        results = imd_df[mask]
        
        if len(results) > 0:
            st.success(f"Found {len(results):,} areas matching '{search_query}'")
            
            # AI Insight
            st.markdown("""
            <div class="chat-bubble">
                <strong>🤖 AI Insight:</strong><br>
                This area shows significant health inequality patterns. The Core 20% concentration is 
                higher than the national average, suggesting targeted intervention opportunities.
            </div>
            """, unsafe_allow_html=True)
            
            # Results Table
            display_cols = ['lsoa11nm', 'lad19nm', 'imd_rank', 'imd_score', 'imd_quintile']
            st.dataframe(
                results[display_cols].head(20),
                use_container_width=True,
                hide_index=True
            )
            
            # Visualization
            fig = px.scatter(
                results.head(100),
                x='imd_rank',
                y='imd_score',
                color='imd_quintile',
                hover_data=['lsoa11nm', 'lad19nm'],
                title="Deprivation Distribution",
                color_continuous_scale='RdYlBu_r'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No results found. Try searching for a different area.")

def render_analytics_view(imd_df):
    """Render advanced analytics view."""
    st.markdown("## 📊 Inequality Analytics")
    
    if not check_usage_limit('analyses'):
        st.error("⚠️ Analysis limit reached.")
        render_premium_modal()
        return
    
    increment_usage('analyses')
    
    # Metric Selector
    metric = st.selectbox(
        "Select Metric",
        ['imd_score', 'income_score', 'employment_score', 'health_score'],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Calculate metrics
    sii = calculate_slope_index_inequality(imd_df, metric)
    gap = calculate_gap_analysis(imd_df, metric)
    
    # Display Metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("SII", f"{sii['sii']:.2f}", "Slope Index")
    with cols[1]:
        st.metric("RII", f"{sii['rii']:.2%}", "Relative Index")
    with cols[2]:
        st.metric("Gap", f"{gap['absolute_gap']:.2f}", "Absolute")
    with cols[3]:
        st.metric("Ratio", f"{gap['relative_gap_percent']:.1f}%", "Relative")
    
    # AI Insights
    st.markdown("### 🤖 AI-Generated Insights")
    insights = generate_ai_insights(imd_df, metric)
    for insight in insights:
        st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)
    
    # Visualization
    quintile_data = calculate_quintile_progression(imd_df, metric)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=quintile_data['quintile_label'],
        y=quintile_data['mean'],
        mode='lines+markers',
        fill='tonexty',
        line=dict(color='#1A73E8', width=3),
        marker=dict(size=12, color='#1A73E8')
    ))
    fig.update_layout(
        title=f"{metric.replace('_', ' ').title()} by Deprivation Quintile",
        xaxis_title="Quintile",
        yaxis_title="Score",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

def render_core20_view(imd_df):
    """Render Core20PLUS5 tracker."""
    st.markdown("## 🎯 Core20PLUS5 Tracker")
    
    analyzer = Core20PLUS5Analyzer(imd_df)
    
    # National Overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        core20_count = len(analyzer.get_core20_areas())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{core20_count:,}</div>
            <div class="metric-label">Core 20% LSOAs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_las = imd_df['lad19cd'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_las}</div>
            <div class="metric-label">Local Authorities</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_deprivation = analyzer.get_core20_areas()['imd_score'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_deprivation:.1f}</div>
            <div class="metric-label">Avg IMD Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # LA Selector
    la_list = ["All England"] + sorted(imd_df['lad19nm'].unique().tolist())
    selected_la = st.selectbox("Select Local Authority", la_list)
    
    if selected_la != "All England":
        la_data = imd_df[imd_df['lad19nm'] == selected_la]
        core20_in_la = la_data[la_data['imd_quintile'] == 1]
        
        st.markdown(f"""
        <div class="insight-card">
            <strong>📍 {selected_la}:</strong> {len(core20_in_la)} of {len(la_data)} LSOAs ({len(core20_in_la)/len(la_data)*100:.1f}%) 
            are in the Core 20% most deprived areas.
        </div>
        """, unsafe_allow_html=True)

def render_export_view(imd_df):
    """Render data export view."""
    st.markdown("## 📥 Export Data")
    
    if not check_usage_limit('exports'):
        st.error("⚠️ Export limit reached.")
        render_premium_modal()
        return
    
    increment_usage('exports')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Export Options")
        export_format = st.radio("Format", ["CSV", "Excel", "JSON"])
        
        if st.button("📥 Generate Export", use_container_width=True):
            if export_format == "CSV":
                csv = imd_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="health_inequalities.csv">⬇️ Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            elif export_format == "Excel" and st.session_state.is_premium:
                st.info("Excel export available in Pro tier")
            else:
                st.warning("Upgrade to Pro for Excel/PDF exports")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application."""
    init_session_state()
    
    # Load data
    imd_df = load_imd_data()
    
    # Header
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #E8EAED; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #1A1A2E;">
                HealthMap <span style="color: #1A73E8;">AI</span>
            </div>
            <span class="premium-badge">Beta</span>
        </div>
        <div style="display: flex; gap: 16px; align-items: center;">
    """, unsafe_allow_html=True)
    
    # Usage indicator
    remaining = get_remaining('searches')
    if remaining != float('inf'):
        st.markdown(f"""
            <div style="font-size: 0.875rem; color: #5F6368;">
                {int(remaining)} searches remaining
            </div>
        """, unsafe_allow_html=True)
    
    # Premium badge or upgrade button
    if st.session_state.is_premium:
        st.markdown('<span class="premium-badge">⭐ Pro</span>', unsafe_allow_html=True)
    else:
        if st.button("⭐ Upgrade", key="header_upgrade"):
            st.session_state.show_premium = True
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Navigation
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button("🔍 Search", use_container_width=True, 
                    type="primary" if st.session_state.current_view == 'search' else "secondary"):
            st.session_state.current_view = 'search'
            st.rerun()
    
    with nav_col2:
        if st.button("📊 Analytics", use_container_width=True,
                    type="primary" if st.session_state.current_view == 'analytics' else "secondary"):
            st.session_state.current_view = 'analytics'
            st.rerun()
    
    with nav_col3:
        if st.button("🎯 Core20+", use_container_width=True,
                    type="primary" if st.session_state.current_view == 'core20' else "secondary"):
            st.session_state.current_view = 'core20'
            st.rerun()
    
    with nav_col4:
        if st.button("📥 Export", use_container_width=True,
                    type="primary" if st.session_state.current_view == 'export' else "secondary"):
            st.session_state.current_view = 'export'
            st.rerun()
    
    # Main Content
    if st.session_state.current_view == 'search':
        render_search_view(imd_df)
    elif st.session_state.current_view == 'analytics':
        render_analytics_view(imd_df)
    elif st.session_state.current_view == 'core20':
        render_core20_view(imd_df)
    elif st.session_state.current_view == 'export':
        render_export_view(imd_df)
    
    # Premium Modal    if st.session_state.get('show_premium', False):        st.markdown("---")        render_premium_modal()        if st.button("✕ Close", key="close_premium"):            st.session_state.show_premium = False            st.rerun()        st.markdown("---")
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 40px 0; color: #5F6368; font-size: 0.875rem; border-top: 1px solid #E8EAED; margin-top: 40px;">
        <p>HealthMap AI • Population Health Intelligence for NHS</p>
        <p style="margin-top: 8px;">
            <a href="https://github.com/mohammedimran2901/phm-health-inequalities" style="color: #1A73E8;">GitHub</a> • 
            <a href="#" style="color: #1A73E8;">Documentation</a> • 
            <a href="#" style="color: #1A73E8;">Privacy</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()