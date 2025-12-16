"""
GridGuard - Regional Analysis
Director of Grid Planning Persona

Deep-dive into region-by-region vulnerability assessment.
Provides regional network subgraphs, cross-region dependencies,
and investment recommendations per region.
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import (
    run_queries_parallel,
    get_regional_summary,
    get_regional_failures_by_scenario,
    get_cross_region_flows,
    get_regional_investment_recommendations,
    get_nodes_by_region,
    get_edges_by_region
)
from utils.viz import (
    create_regional_heatmap,
    create_regional_failures_chart,
    create_sankey_diagram,
    create_network_graph,
    create_executive_summary_card,
    COLORS,
    REGION_COLORS
)

st.set_page_config(
    page_title="Regional Analysis | GridGuard",
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #0f1419 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B2A41 0%, #0f1419 100%);
    }
    
    .region-header {
        background: linear-gradient(135deg, rgba(41, 181, 232, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        border: 1px solid rgba(41, 181, 232, 0.3);
    }
    
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: white;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(41, 181, 232, 0.3);
    }
    
    .region-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        margin-bottom: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .region-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(41, 181, 232, 0.2);
    }
    
    .region-name {
        font-size: 18px;
        font-weight: 600;
        color: white;
        margin-bottom: 12px;
    }
    
    .region-stats {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .region-stat {
        text-align: center;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        flex: 1;
        min-width: 80px;
    }
    
    .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: #29B5E8;
    }
    
    .stat-label {
        font-size: 11px;
        color: #94A3B8;
        text-transform: uppercase;
    }
    
    .risk-indicator {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin-left: 12px;
    }
    
    .risk-high {
        background: rgba(239, 68, 68, 0.2);
        color: #EF4444;
    }
    
    .risk-medium {
        background: rgba(234, 179, 8, 0.2);
        color: #EAB308;
    }
    
    .risk-low {
        background: rgba(34, 197, 94, 0.2);
        color: #22C55E;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.markdown("""
<div class="region-header">
    <div style="font-size: 28px; font-weight: 700; color: white; margin-bottom: 8px;">
        Regional Analysis
    </div>
    <div style="font-size: 16px; color: #94A3B8;">
        Deep-dive into region-by-region vulnerability and investment opportunities
    </div>
</div>
""", unsafe_allow_html=True)

# Load data
with st.spinner("Loading regional data..."):
    regional_summary = get_regional_summary(session)
    regional_failures = get_regional_failures_by_scenario(session)
    cross_region_flows = get_cross_region_flows(session)
    investment_recommendations = get_regional_investment_recommendations(session)

# =============================================================================
# SECTION 1: REGIONAL COMPARISON CARDS
# =============================================================================

st.markdown('<div class="section-header">Regional Overview</div>', unsafe_allow_html=True)

if regional_summary is not None and len(regional_summary) > 0:
    cols = st.columns(len(regional_summary))
    
    for i, (_, row) in enumerate(regional_summary.iterrows()):
        with cols[i]:
            region_name = row['REGION'].replace('_', ' ').title()
            region_color = REGION_COLORS.get(row['REGION'], '#888888')
            
            # Determine risk level
            if row['AVG_FAILURE_PROB'] > 0.6:
                risk_level = 'HIGH'
                risk_class = 'risk-high'
            elif row['AVG_FAILURE_PROB'] > 0.4:
                risk_level = 'MEDIUM'
                risk_class = 'risk-medium'
            else:
                risk_level = 'LOW'
                risk_class = 'risk-low'
            
            st.markdown(f"""
            <div class="region-card" style="border-left: 4px solid {region_color};">
                <div class="region-name">
                    {region_name}
                    <span class="risk-indicator {risk_class}">{risk_level} RISK</span>
                </div>
                <div class="region-stats">
                    <div class="region-stat">
                        <div class="stat-value">{int(row['NODE_COUNT'])}</div>
                        <div class="stat-label">Nodes</div>
                    </div>
                    <div class="region-stat">
                        <div class="stat-value">{row['TOTAL_CAPACITY_MW']/1000:.1f}K</div>
                        <div class="stat-label">MW Capacity</div>
                    </div>
                    <div class="region-stat">
                        <div class="stat-value" style="color: {'#EF4444' if row['HIGH_RISK_NODES'] > 2 else '#EAB308' if row['HIGH_RISK_NODES'] > 0 else '#22C55E'};">
                            {int(row['HIGH_RISK_NODES'])}
                        </div>
                        <div class="stat-label">At Risk</div>
                    </div>
                    <div class="region-stat">
                        <div class="stat-value">${row['TOTAL_EXPOSURE']/1000000:.1f}M</div>
                        <div class="stat-label">Exposure</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 2: REGIONAL PERFORMANCE COMPARISON
# =============================================================================

st.markdown('<div class="section-header">Regional Performance by Scenario</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if regional_failures is not None and len(regional_failures) > 0:
        fig = create_regional_failures_chart(regional_failures)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No regional failure data available")

with col2:
    st.markdown("### Insights")
    
    if regional_failures is not None and len(regional_failures) > 0:
        # Find worst-performing region
        winter_storm = regional_failures[regional_failures['SCENARIO_NAME'] == 'WINTER_STORM_2021']
        if len(winter_storm) > 0:
            worst_region = winter_storm.loc[winter_storm['FAILURE_COUNT'].idxmax()]
            best_region = winter_storm.loc[winter_storm['FAILURE_COUNT'].idxmin()]
            
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="color: #EF4444; font-size: 12px; font-weight: 600;">MOST VULNERABLE</div>
                <div style="color: white; font-size: 16px; font-weight: 600; margin-top: 4px;">
                    {worst_region['REGION'].replace('_', ' ').title()}
                </div>
                <div style="color: #94A3B8; font-size: 13px;">
                    {int(worst_region['FAILURE_COUNT'])} failures during Winter Storm
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 16px;">
                <div style="color: #22C55E; font-size: 12px; font-weight: 600;">MOST RESILIENT</div>
                <div style="color: white; font-size: 16px; font-weight: 600; margin-top: 4px;">
                    {best_region['REGION'].replace('_', ' ').title()}
                </div>
                <div style="color: #94A3B8; font-size: 13px;">
                    {int(best_region['FAILURE_COUNT'])} failures during Winter Storm
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 3: CROSS-REGION DEPENDENCIES
# =============================================================================

st.markdown('<div class="section-header">Cross-Region Power Flow</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if cross_region_flows is not None and len(cross_region_flows) > 0:
        fig = create_sankey_diagram(cross_region_flows)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cross-region flow data available (all edges are within regions)")

with col2:
    st.markdown("### Interconnection Summary")
    
    if cross_region_flows is not None and len(cross_region_flows) > 0:
        total_capacity = cross_region_flows['TOTAL_CAPACITY_MW'].sum()
        total_edges = cross_region_flows['EDGE_COUNT'].sum()
        
        st.markdown(f"""
        <div style="background: rgba(27, 42, 65, 0.6); border-radius: 12px; padding: 20px; border: 1px solid rgba(41, 181, 232, 0.2);">
            <div style="margin-bottom: 16px;">
                <div style="color: #94A3B8; font-size: 12px;">Total Cross-Region Capacity</div>
                <div style="color: #29B5E8; font-size: 24px; font-weight: 700;">{total_capacity:,.0f} MW</div>
            </div>
            <div style="margin-bottom: 16px;">
                <div style="color: #94A3B8; font-size: 12px;">Interconnection Lines</div>
                <div style="color: white; font-size: 24px; font-weight: 700;">{int(total_edges)}</div>
            </div>
            <div style="color: #94A3B8; font-size: 13px; line-height: 1.6;">
                Cross-region transmission lines are critical for grid stability. 
                Failures in these interconnections can isolate regions and cascade outages.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(27, 42, 65, 0.6); border-radius: 12px; padding: 20px; border: 1px solid rgba(41, 181, 232, 0.2);">
            <div style="color: #94A3B8; font-size: 14px;">
                This grid topology has limited cross-region connections. 
                All transmission lines operate within regional boundaries.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 4: REGIONAL NETWORK EXPLORER
# =============================================================================

st.markdown('<div class="section-header">Regional Network Explorer</div>', unsafe_allow_html=True)

# Region selector
regions = regional_summary['REGION'].tolist() if regional_summary is not None and len(regional_summary) > 0 else []

if regions:
    selected_region = st.selectbox(
        "Select a region to explore:",
        options=regions,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Load region-specific data
    with st.spinner(f"Loading {selected_region.replace('_', ' ').title()} network..."):
        region_nodes = get_nodes_by_region(session, selected_region)
        region_edges = get_edges_by_region(session, selected_region)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if region_nodes is not None and len(region_nodes) > 0:
            # Create simulation_df from region_nodes for visualization
            sim_df = region_nodes[['NODE_ID', 'FAILURE_PROBABILITY', 'RISK_SCORE', 'CASCADE_ORDER', 'IS_PATIENT_ZERO']].copy()
            
            fig = create_network_graph(
                nodes_df=region_nodes,
                edges_df=region_edges if region_edges is not None else pd.DataFrame(),
                simulation_df=sim_df,
                highlight_patient_zero=True,
                title=f"{selected_region.replace('_', ' ').title()} - Network Topology"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No nodes found in {selected_region}")
    
    with col2:
        st.markdown(f"### {selected_region.replace('_', ' ').title()} Details")
        
        if region_nodes is not None and len(region_nodes) > 0:
            region_color = REGION_COLORS.get(selected_region, '#888888')
            
            # Calculate stats
            total_capacity = region_nodes['CAPACITY_MW'].sum()
            avg_criticality = region_nodes['CRITICALITY_SCORE'].mean()
            high_risk = len(region_nodes[region_nodes['RISK_SCORE'] > 0.7]) if 'RISK_SCORE' in region_nodes.columns else 0
            failed = len(region_nodes[region_nodes['CASCADE_ORDER'].notna()]) if 'CASCADE_ORDER' in region_nodes.columns else 0
            
            st.markdown(f"""
            <div style="background: rgba(27, 42, 65, 0.6); border-radius: 12px; padding: 20px; border-left: 4px solid {region_color};">
                <div style="margin-bottom: 16px;">
                    <div style="color: #94A3B8; font-size: 12px;">Total Nodes</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">{len(region_nodes)}</div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="color: #94A3B8; font-size: 12px;">Total Capacity</div>
                    <div style="color: #29B5E8; font-size: 24px; font-weight: 700;">{total_capacity:,.0f} MW</div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="color: #94A3B8; font-size: 12px;">Avg Criticality Score</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">{avg_criticality:.2f}</div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="color: #94A3B8; font-size: 12px;">High-Risk Nodes</div>
                    <div style="color: {'#EF4444' if high_risk > 2 else '#EAB308' if high_risk > 0 else '#22C55E'}; font-size: 24px; font-weight: 700;">
                        {high_risk}
                    </div>
                </div>
                <div>
                    <div style="color: #94A3B8; font-size: 12px;">Failed in Scenario</div>
                    <div style="color: #EF4444; font-size: 24px; font-weight: 700;">{failed}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Node type breakdown
            st.markdown("### Node Types")
            type_counts = region_nodes['NODE_TYPE'].value_counts()
            for node_type, count in type_counts.items():
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <span style="color: #94A3B8;">{node_type.replace('_', ' ').title()}</span>
                    <span style="color: white; font-weight: 600;">{count}</span>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 5: INVESTMENT RECOMMENDATIONS BY REGION
# =============================================================================

st.markdown('<div class="section-header">Investment Recommendations by Region</div>', unsafe_allow_html=True)

if investment_recommendations is not None and len(investment_recommendations) > 0:
    # Create summary table with renamed columns for display
    display_df = investment_recommendations.copy()
    display_df.columns = ['Region', 'Total Nodes', 'Upgrade Needed', 'Est. Investment ($)', 'Expected Benefit ($)', 'ROI %']
    st.dataframe(
        display_df,
        use_container_width=True
    )
    
    # Investment summary cards
    st.markdown("### Investment Summary")
    
    total_investment = investment_recommendations['EST_INVESTMENT_COST'].sum()
    total_benefit = investment_recommendations['EXPECTED_BENEFIT'].sum()
    overall_roi = (total_benefit / total_investment * 100) if total_investment > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(41, 181, 232, 0.1); border: 1px solid rgba(41, 181, 232, 0.3); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #29B5E8; font-size: 12px; font-weight: 600;">TOTAL INVESTMENT NEEDED</div>
            <div style="color: white; font-size: 28px; font-weight: 700; margin-top: 8px;">
                ${total_investment/1000000:.1f}M
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #22C55E; font-size: 12px; font-weight: 600;">TOTAL EXPECTED BENEFIT</div>
            <div style="color: white; font-size: 28px; font-weight: 700; margin-top: 8px;">
                ${total_benefit/1000000:.1f}M
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        roi_color = "#22C55E" if overall_roi > 100 else "#EAB308" if overall_roi > 0 else "#EF4444"
        st.markdown(f"""
        <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #8B5CF6; font-size: 12px; font-weight: 600;">OVERALL ROI</div>
            <div style="color: {roi_color}; font-size: 28px; font-weight: 700; margin-top: 8px;">
                {overall_roi:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Priority recommendation
    best_roi_region = investment_recommendations.loc[investment_recommendations['ROI_PERCENT'].idxmax()]
    
    st.markdown(f"""
    <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-left: 4px solid #8B5CF6; border-radius: 8px; padding: 16px; margin-top: 24px;">
        <div style="color: #8B5CF6; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
            📊 RECOMMENDATION
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            Prioritize investments in <b style="color: white;">{best_roi_region['REGION'].replace('_', ' ').title()}</b> 
            with the highest ROI of <b style="color: #22C55E;">{best_roi_region['ROI_PERCENT']:.0f}%</b>.
            An investment of <b style="color: white;">${best_roi_region['EST_INVESTMENT_COST']/1000000:.1f}M</b> 
            could yield <b style="color: white;">${best_roi_region['EXPECTED_BENEFIT']/1000000:.1f}M</b> in avoided damages.
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("No investment recommendation data available")

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>7_Scenario_Builder</b> | Next: <b>9_About</b>
</div>
""", unsafe_allow_html=True)

