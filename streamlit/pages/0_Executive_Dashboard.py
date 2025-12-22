"""
GridGuard - Executive Dashboard
Director of Grid Planning Persona

Strategic overview with investment prioritization, scenario comparison,
and regional risk assessment. Designed for executive decision-making.

STAR Flow:
- SITUATION: Grid exposure assessment and current risk state
- TASK: Identify highest-priority infrastructure upgrades
- ACTION: Compare scenarios and evaluate investment options
- RESULT: ROI-justified recommendations for budget allocation
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import (
    run_queries_parallel,
    get_executive_summary,
    get_scenario_comparison,
    get_investment_priorities,
    get_regional_summary,
    get_top_priority_nodes
)
from utils.viz import (
    create_investment_matrix,
    create_scenario_comparison_chart,
    create_regional_heatmap,
    create_priority_gauge,
    create_executive_summary_card,
    COLORS,
    REGION_COLORS
)

st.set_page_config(
    page_title="Executive Dashboard | GridGuard",
    page_icon="📊",
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
    
    /* Executive header */
    .exec-header {
        background: linear-gradient(135deg, rgba(41, 181, 232, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        border: 1px solid rgba(41, 181, 232, 0.3);
    }
    
    .exec-title {
        font-size: 28px;
        font-weight: 700;
        color: white;
        margin-bottom: 8px;
    }
    
    .exec-subtitle {
        font-size: 16px;
        color: #94A3B8;
    }
    
    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: white;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(41, 181, 232, 0.3);
    }
    
    /* Insight callout */
    .insight-callout {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-left: 4px solid #8B5CF6;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .insight-title {
        font-size: 14px;
        font-weight: 600;
        color: #8B5CF6;
        margin-bottom: 8px;
    }
    
    .insight-text {
        font-size: 14px;
        color: #94A3B8;
        line-height: 1.6;
    }
    
    /* Priority badge */
    .priority-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .priority-high {
        background: rgba(239, 68, 68, 0.2);
        color: #EF4444;
    }
    
    .priority-medium {
        background: rgba(234, 179, 8, 0.2);
        color: #EAB308;
    }
    
    .priority-low {
        background: rgba(34, 197, 94, 0.2);
        color: #22C55E;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Executive Header
st.markdown("""
<div class="exec-header">
    <div class="exec-title">Executive Dashboard</div>
    <div class="exec-subtitle">
        Strategic Grid Resilience Overview | Director of Grid Planning View
    </div>
</div>
""", unsafe_allow_html=True)

# Scenario selector
col1, col2 = st.columns([3, 1])
with col2:
    scenarios_df = session.sql("SELECT DISTINCT SCENARIO_NAME FROM SIMULATION_RESULTS ORDER BY SCENARIO_NAME").to_pandas()
    scenario_options = scenarios_df['SCENARIO_NAME'].tolist() if len(scenarios_df) > 0 else ['WINTER_STORM_2021']
    selected_scenario = st.selectbox(
        "Analysis Scenario",
        options=scenario_options,
        index=scenario_options.index('WINTER_STORM_2021') if 'WINTER_STORM_2021' in scenario_options else 0
    )

# Load all data
with st.spinner("Loading executive summary..."):
    exec_summary = get_executive_summary(session, selected_scenario)
    scenario_comparison = get_scenario_comparison(session)
    investment_priorities = get_investment_priorities(session, selected_scenario)
    regional_summary = get_regional_summary(session, selected_scenario)
    top_priorities = get_top_priority_nodes(session, selected_scenario, limit=10)

# =============================================================================
# SECTION 1: KEY PERFORMANCE INDICATORS
# =============================================================================

st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)

if exec_summary is not None and len(exec_summary) > 0:
    summary = exec_summary.iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_exposure = summary['TOTAL_EXPOSURE'] or 0
        st.markdown(
            create_executive_summary_card(
                title="Total Grid Exposure",
                value=f"${total_exposure/1000000:.1f}M",
                subtitle="Potential repair costs under worst-case scenario",
                icon="⚠️",
                color=COLORS['failed']
            ),
            unsafe_allow_html=True
        )
    
    with col2:
        critical_nodes = int(summary['CRITICAL_NODES'] or 0)
        total_nodes = int(summary['TOTAL_NODES'] or 1)
        st.markdown(
            create_executive_summary_card(
                title="Critical Nodes",
                value=f"{critical_nodes}",
                subtitle=f"{critical_nodes/total_nodes*100:.0f}% of grid infrastructure",
                icon="🔴",
                color=COLORS['warning']
            ),
            unsafe_allow_html=True
        )
    
    with col3:
        customers = int(summary['TOTAL_CUSTOMERS_AT_RISK'] or 0)
        st.markdown(
            create_executive_summary_card(
                title="Customers at Risk",
                value=f"{customers:,}",
                subtitle="Potential service disruption impact",
                icon="👥",
                color=COLORS['snowflake_blue']
            ),
            unsafe_allow_html=True
        )
    
    with col4:
        cascade_nodes = int(summary['NODES_IN_CASCADE'] or 0)
        st.markdown(
            create_executive_summary_card(
                title="Cascade Size",
                value=f"{cascade_nodes} nodes",
                subtitle=f"{summary['TOTAL_LOAD_SHED'] or 0:,.0f} MW load shed",
                icon="⚡",
                color=COLORS['patient_zero']
            ),
            unsafe_allow_html=True
        )

st.markdown("---")

# =============================================================================
# SECTION 2: INVESTMENT PRIORITY MATRIX
# =============================================================================

st.markdown('<div class="section-header">Investment Priority Matrix</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    if investment_priorities is not None and len(investment_priorities) > 0:
        # --- DEBUG START ---
        with st.expander("🕵️‍♀️ Investment Matrix Debug", expanded=True):
            st.write(f"Total Rows: {len(investment_priorities)}")
            st.write("Column Types:")
            st.write(investment_priorities.dtypes.astype(str))
            
            # Check for critical columns
            req_cols = ['EST_REINFORCEMENT_COST', 'IMPACT_IF_FAILS', 'REGION', 'NODE_DEGREE']
            missing = [c for c in req_cols if c not in investment_priorities.columns]
            if missing:
                st.error(f"Missing columns: {missing}")
            
            # Show sample data
            st.write("First 5 rows (Raw):")
            st.dataframe(investment_priorities[req_cols + ['NODE_NAME']].head())
            
            # Check values
            st.write("Stats:")
            st.write(investment_priorities[['EST_REINFORCEMENT_COST', 'IMPACT_IF_FAILS', 'NODE_DEGREE']].describe())
            
            st.write("Region Counts:")
            st.write(investment_priorities['REGION'].value_counts())
        # --- DEBUG END ---

        fig = create_investment_matrix(investment_priorities)
        
        # --- FIGURE DEBUG ---
        with st.expander("📊 Figure JSON Debug", expanded=False):
            st.json(fig.to_dict())
        # --------------------
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No investment priority data available")

with col2:
    st.markdown("### Priority Legend")
    st.markdown("""
    <div style="background: rgba(27, 42, 65, 0.6); padding: 16px; border-radius: 12px; border: 1px solid rgba(41, 181, 232, 0.2);">
        <div style="margin-bottom: 16px;">
            <span style="color: #EF4444; font-weight: 600;">● MUST FIX</span>
            <div style="color: #94A3B8; font-size: 12px;">High impact, low cost</div>
        </div>
        <div style="margin-bottom: 16px;">
            <span style="color: #EAB308; font-weight: 600;">● CONSIDER</span>
            <div style="color: #94A3B8; font-size: 12px;">High impact, high cost</div>
        </div>
        <div style="margin-bottom: 16px;">
            <span style="color: #22C55E; font-weight: 600;">● MONITOR</span>
            <div style="color: #94A3B8; font-size: 12px;">Low impact, low cost</div>
        </div>
        <div>
            <span style="color: #64748B; font-weight: 600;">● LOW PRIORITY</span>
            <div style="color: #94A3B8; font-size: 12px;">Low impact, high cost</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Node priority distribution
    if investment_priorities is not None and len(investment_priorities) > 0:
        high = len(investment_priorities[investment_priorities['RISK_SCORE'] > 0.7])
        medium = len(investment_priorities[(investment_priorities['RISK_SCORE'] > 0.4) & 
                                           (investment_priorities['RISK_SCORE'] <= 0.7)])
        low = len(investment_priorities[investment_priorities['RISK_SCORE'] <= 0.4])
        
        fig_gauge = create_priority_gauge(high, medium, low)
        st.plotly_chart(fig_gauge, use_container_width=True)

# Key insight callout
if investment_priorities is not None and len(investment_priorities) > 0:
    patient_zero = investment_priorities[investment_priorities['IS_PATIENT_ZERO'] == True]
    if len(patient_zero) > 0:
        pz = patient_zero.iloc[0]
        st.markdown(f"""
        <div class="insight-callout">
            <div class="insight-title">🎯 KEY INSIGHT: Patient Zero Identified</div>
            <div class="insight-text">
                <b>{pz['NODE_NAME']}</b> in {pz['REGION'].replace('_', ' ').title()} is the cascade origin point.
                Reinforcing this node (est. ${pz['EST_REINFORCEMENT_COST']/1000000:.1f}M) could prevent 
                ${pz['IMPACT_IF_FAILS']/1000000:.1f}M in downstream damages.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 3: SCENARIO COMPARISON
# =============================================================================

st.markdown('<div class="section-header">Scenario Comparison</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if scenario_comparison is not None and len(scenario_comparison) > 0:
        fig = create_scenario_comparison_chart(scenario_comparison)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No scenario comparison data available")

with col2:
    st.markdown("### Scenario Summary")
    if scenario_comparison is not None and len(scenario_comparison) > 0:
        for _, row in scenario_comparison.iterrows():
            scenario_name = row['SCENARIO_NAME'].replace('_', ' ').title()
            
            # Handle None/NaN values safely
            failures = int(row['FAILURES']) if pd.notna(row['FAILURES']) else 0
            repair_cost = float(row['TOTAL_REPAIR_COST']) if pd.notna(row['TOTAL_REPAIR_COST']) else 0.0
            max_cost = scenario_comparison['TOTAL_REPAIR_COST'].max()
            is_worst = repair_cost > 0 and repair_cost == max_cost
            
            bg_color = "rgba(239, 68, 68, 0.1)" if is_worst else "rgba(27, 42, 65, 0.6)"
            border_color = "rgba(239, 68, 68, 0.4)" if is_worst else "rgba(41, 181, 232, 0.2)"
            worst_badge = '<span style="color: #EF4444; font-size: 10px; margin-left: 8px;">HIGHEST IMPACT</span>' if is_worst else ''
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="color: white; font-weight: 600; margin-bottom: 4px;">
                    {scenario_name} {worst_badge}
                </div>
                <div style="color: #94A3B8; font-size: 13px;">
                    {failures} failures | ${repair_cost/1000000:.1f}M cost
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 4: REGIONAL RISK OVERVIEW
# =============================================================================

st.markdown('<div class="section-header">Regional Risk Overview</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if regional_summary is not None and len(regional_summary) > 0:
        fig = create_regional_heatmap(regional_summary)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No regional data available")

with col2:
    st.markdown("### Region Details")
    if regional_summary is not None and len(regional_summary) > 0:
        for _, row in regional_summary.iterrows():
            region_name = row['REGION'].replace('_', ' ').title()
            region_color = REGION_COLORS.get(row['REGION'], '#888888')
            
            risk_level = 'HIGH' if row['AVG_FAILURE_PROB'] > 0.6 else 'MEDIUM' if row['AVG_FAILURE_PROB'] > 0.4 else 'LOW'
            risk_class = f"priority-{risk_level.lower()}"
            
            st.markdown(f"""
            <div style="background: rgba(27, 42, 65, 0.6); border-radius: 8px; padding: 12px; margin-bottom: 12px; border-left: 4px solid {region_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: white; font-weight: 600;">{region_name}</span>
                    <span class="priority-badge {risk_class}">{risk_level}</span>
                </div>
                <div style="color: #94A3B8; font-size: 12px; margin-top: 8px;">
                    {int(row['NODE_COUNT'])} nodes | {int(row['HIGH_RISK_NODES'])} at risk | ${row['TOTAL_EXPOSURE']/1000000:.1f}M exposure
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 5: TOP PRIORITY NODES
# =============================================================================

st.markdown('<div class="section-header">Top 10 Priority Nodes</div>', unsafe_allow_html=True)

if top_priorities is not None and len(top_priorities) > 0:
    # Rename columns for cleaner display
    display_cols = ['NODE_NAME', 'REGION', 'NODE_TYPE', 'RISK_SCORE', 'FAILURE_PROB', 'POTENTIAL_COST', 'IS_PATIENT_ZERO', 'CASCADE_ORDER', 'RECOMMENDED_ACTION']
    available_cols = [c for c in display_cols if c in top_priorities.columns]
    display_df = top_priorities[available_cols].copy()
    
    # Rename columns for display
    col_rename = {
        'NODE_NAME': 'Node',
        'REGION': 'Region',
        'NODE_TYPE': 'Type',
        'RISK_SCORE': 'Risk Score',
        'FAILURE_PROB': 'Failure Prob',
        'POTENTIAL_COST': 'Potential Cost ($)',
        'IS_PATIENT_ZERO': 'P0',
        'CASCADE_ORDER': 'Cascade #',
        'RECOMMENDED_ACTION': 'Recommended Action'
    }
    display_df.columns = [col_rename.get(c, c) for c in display_df.columns]
    
    st.dataframe(
        display_df,
        use_container_width=True
    )
else:
    st.info("No priority data available")

st.markdown("---")

# =============================================================================
# EXECUTIVE RECOMMENDATIONS
# =============================================================================

st.markdown('<div class="section-header">Executive Recommendations</div>', unsafe_allow_html=True)

if investment_priorities is not None and len(investment_priorities) > 0:
    # Calculate recommendation summary
    must_fix = investment_priorities[investment_priorities['RISK_SCORE'] > 0.7]
    total_investment = must_fix['EST_REINFORCEMENT_COST'].sum() if len(must_fix) > 0 else 0
    total_avoided_cost = must_fix['IMPACT_IF_FAILS'].sum() if len(must_fix) > 0 else 0
    roi = ((total_avoided_cost - total_investment) / total_investment * 100) if total_investment > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <div style="color: #22C55E; font-size: 14px; font-weight: 600; margin-bottom: 8px;">RECOMMENDED INVESTMENT</div>
            <div style="color: white; font-size: 32px; font-weight: 700;">${total_investment/1000000:.1f}M</div>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 8px;">{len(must_fix)} high-priority nodes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: rgba(41, 181, 232, 0.1); border: 1px solid rgba(41, 181, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <div style="color: #29B5E8; font-size: 14px; font-weight: 600; margin-bottom: 8px;">AVOIDED DAMAGES</div>
            <div style="color: white; font-size: 32px; font-weight: 700;">${total_avoided_cost/1000000:.1f}M</div>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 8px;">Expected cost savings</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        roi_color = "#22C55E" if roi > 100 else "#EAB308" if roi > 0 else "#EF4444"
        st.markdown(f"""
        <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <div style="color: #8B5CF6; font-size: 14px; font-weight: 600; margin-bottom: 8px;">PROJECTED ROI</div>
            <div style="color: {roi_color}; font-size: 32px; font-weight: 700;">{roi:.0f}%</div>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 8px;">Return on investment</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Action summary
    st.markdown(f"""
    <div class="insight-callout" style="margin-top: 24px;">
        <div class="insight-title">📋 RECOMMENDED ACTIONS</div>
        <div class="insight-text">
            <ol style="margin: 0; padding-left: 20px;">
                <li><b>Immediate:</b> Reinforce Patient Zero node to prevent cascade initiation</li>
                <li><b>Q1 Priority:</b> Address {len(must_fix)} high-risk nodes in {', '.join(must_fix['REGION'].unique()[:2]).replace('_', ' ').title()}</li>
                <li><b>Budget Request:</b> ${total_investment/1000000:.1f}M capital investment for {roi:.0f}% ROI</li>
                <li><b>Monitoring:</b> Implement real-time monitoring for all critical nodes</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Navigation
st.markdown("---")
# Navigation hint
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Home: <b>streamlit_app</b> | Next: <b>8_Regional_Analysis</b>
</div>
""", unsafe_allow_html=True)

