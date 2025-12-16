"""
GridGuard - Key Insights Page

Highlights the "Patient Zero" discovery and AI-powered analysis insights.
Includes animated cascade visualization, counter-factual analysis, and ROI calculator.
"""

import streamlit as st
import pandas as pd
import time
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import run_queries_parallel
from utils.viz import create_animated_cascade_graph, create_counterfactual_chart

st.set_page_config(
    page_title="Key Insights | GridGuard",
    page_icon="💡",
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
    .insight-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(41, 181, 232, 0.1) 100%);
        border-radius: 16px;
        padding: 32px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        margin-bottom: 24px;
    }
    .insight-number {
        font-size: 64px;
        font-weight: 700;
        color: #8B5CF6;
        line-height: 1;
    }
    .insight-label {
        font-size: 18px;
        color: #94A3B8;
        margin-top: 8px;
    }
    .highlight-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("Key Insights")
st.markdown("""
The GNN analysis revealed critical insights about grid vulnerability patterns.
Here's what the AI discovered.
""")

st.markdown("---")

# Load Winter Storm data
with st.spinner("Loading insights..."):
    queries = {
        'patient_zero': """
            SELECT sr.*, gn.NODE_NAME, gn.REGION, gn.NODE_TYPE, gn.CAPACITY_MW, gn.CRITICALITY_SCORE
            FROM SIMULATION_RESULTS sr
            JOIN GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
            WHERE sr.SCENARIO_NAME = 'WINTER_STORM_2021'
            AND sr.IS_PATIENT_ZERO = TRUE
        """,
        'cascade_stats': """
            SELECT 
                COUNT(*) as TOTAL_NODES,
                SUM(CASE WHEN CASCADE_ORDER IS NOT NULL THEN 1 ELSE 0 END) as CASCADE_NODES,
                MAX(CASCADE_DEPTH) as MAX_DEPTH,
                SUM(LOAD_SHED_MW) as TOTAL_LOAD_SHED,
                SUM(CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS,
                SUM(REPAIR_COST) as TOTAL_COST
            FROM SIMULATION_RESULTS
            WHERE SCENARIO_NAME = 'WINTER_STORM_2021'
        """,
        'cascade_path': """
            SELECT sr.CASCADE_ORDER, sr.NODE_ID, gn.NODE_NAME, gn.REGION, 
                   sr.FAILURE_PROBABILITY, sr.LOAD_SHED_MW, sr.AI_EXPLANATION
            FROM SIMULATION_RESULTS sr
            JOIN GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
            WHERE sr.SCENARIO_NAME = 'WINTER_STORM_2021'
            AND sr.CASCADE_ORDER IS NOT NULL
            ORDER BY sr.CASCADE_ORDER
        """,
        'comparison': """
            SELECT SCENARIO_NAME,
                   SUM(CASE WHEN CASCADE_ORDER IS NOT NULL THEN 1 ELSE 0 END) as FAILURES,
                   SUM(LOAD_SHED_MW) as LOAD_SHED,
                   SUM(REPAIR_COST) as COST
            FROM SIMULATION_RESULTS
            GROUP BY SCENARIO_NAME
            ORDER BY COST DESC
        """
    }
    data = run_queries_parallel(session, queries)

patient_zero_df = data.get('patient_zero', pd.DataFrame())
cascade_stats = data.get('cascade_stats', pd.DataFrame())
cascade_path = data.get('cascade_path', pd.DataFrame())
comparison = data.get('comparison', pd.DataFrame())

# Patient Zero Discovery
st.markdown("## The Discovery: Patient Zero")

if patient_zero_df is not None and len(patient_zero_df) > 0:
    pz = patient_zero_df.iloc[0]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-size: 14px; color: #8B5CF6; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
                Cascade Origin Identified
            </div>
            <div style="font-size: 32px; font-weight: 700; color: white; margin-bottom: 16px;">
                {pz['NODE_NAME']}
            </div>
            <div style="color: #94A3B8; font-size: 16px; line-height: 1.8;">
                The GNN identified this substation as the cascade origin point - 
                the first node to fail that triggered the chain reaction across the grid.
                <br/><br/>
                <b>Why this node?</b> The analysis shows it has:
                <ul>
                    <li>High criticality score ({pz['CRITICALITY_SCORE']:.2f})</li>
                    <li>Strategic position in network topology</li>
                    <li>Single-point failure exposure</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="insight-number">{pz['FAILURE_PROBABILITY']:.0%}</div>
            <div class="insight-label">Failure Probability</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: rgba(27, 42, 65, 0.6); padding: 16px; border-radius: 8px; border: 1px solid rgba(41, 181, 232, 0.2);">
            <div style="color: #94A3B8; font-size: 12px;">Region</div>
            <div style="color: white; font-size: 18px; font-weight: 600;">{pz['REGION']}</div>
            <br/>
            <div style="color: #94A3B8; font-size: 12px;">Node Type</div>
            <div style="color: white; font-size: 18px; font-weight: 600;">{pz['NODE_TYPE']}</div>
            <br/>
            <div style="color: #94A3B8; font-size: 12px;">Capacity</div>
            <div style="color: white; font-size: 18px; font-weight: 600;">{pz['CAPACITY_MW']:,.0f} MW</div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("Patient Zero data not available. Run the notebook first.")

st.markdown("---")

# Cascade Impact
st.markdown("## Cascade Impact Analysis")

if cascade_stats is not None and len(cascade_stats) > 0:
    stats = cascade_stats.iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cascade_nodes = int(stats['CASCADE_NODES'] or 0)
        total_nodes = int(stats['TOTAL_NODES'] or 1)
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="insight-number">{cascade_nodes}</div>
            <div class="insight-label">Nodes Failed</div>
            <div style="color: #64748B; font-size: 12px;">{cascade_nodes/total_nodes*100:.0f}% of grid</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="insight-number">{int(stats['MAX_DEPTH'] or 0)}</div>
            <div class="insight-label">Cascade Depth</div>
            <div style="color: #64748B; font-size: 12px;">Hops from origin</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        load_shed = stats['TOTAL_LOAD_SHED'] or 0
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="insight-number">{load_shed/1000:.1f}K</div>
            <div class="insight-label">MW Load Shed</div>
            <div style="color: #64748B; font-size: 12px;">Total capacity lost</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        cost = stats['TOTAL_COST'] or 0
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="insight-number">${cost/1000000:.1f}M</div>
            <div class="insight-label">Repair Cost</div>
            <div style="color: #64748B; font-size: 12px;">Estimated damages</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Animated Cascade Visualization
st.markdown("## 🎬 Cascade Propagation Animation")

# Load nodes and edges for animation
with st.spinner("Loading grid topology..."):
    topo_queries = {
        'nodes': "SELECT * FROM GRID_NODES",
        'edges': "SELECT * FROM GRID_EDGES"
    }
    topo_data = run_queries_parallel(session, topo_queries)

nodes_df = topo_data.get('nodes', pd.DataFrame())
edges_df = topo_data.get('edges', pd.DataFrame())

if cascade_path is not None and len(cascade_path) > 0:
    max_cascade_order = int(cascade_path['CASCADE_ORDER'].max())
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### Animation Controls")
        
        # Initialize session state
        if 'animation_step' not in st.session_state:
            st.session_state.animation_step = 0
        if 'auto_play' not in st.session_state:
            st.session_state.auto_play = False
        
        # Animation step slider - update session state when changed
        animation_step = st.slider(
            "Cascade Step",
            min_value=0,
            max_value=max_cascade_order,
            value=st.session_state.animation_step,
            key="cascade_slider"
        )
        
        # Sync slider value back to session state
        if animation_step != st.session_state.animation_step:
            st.session_state.animation_step = animation_step
            st.session_state.auto_play = False  # Stop auto-play if user manually changes slider
        
        # Control buttons in a row
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            # Step forward button
            if st.button("⏭️ Step", use_container_width=True):
                if st.session_state.animation_step < max_cascade_order:
                    st.session_state.animation_step += 1
                    st.experimental_rerun()
        
        with btn_col2:
            # Reset button
            if st.button("⏮️ Reset", use_container_width=True):
                st.session_state.animation_step = 0
                st.session_state.auto_play = False
                st.experimental_rerun()
        
        # Auto-play toggle
        if st.button(
            "⏹️ Stop" if st.session_state.auto_play else "▶️ Auto-Play",
            use_container_width=True,
            type="primary" if st.session_state.auto_play else "secondary"
        ):
            st.session_state.auto_play = not st.session_state.auto_play
            if st.session_state.auto_play and st.session_state.animation_step >= max_cascade_order:
                st.session_state.animation_step = 0  # Reset if at end
            st.experimental_rerun()
        
        # Auto-play logic - increment step if auto_play is on
        if st.session_state.auto_play:
            if st.session_state.animation_step < max_cascade_order:
                time.sleep(1.0)
                st.session_state.animation_step += 1
                st.experimental_rerun()
            else:
                st.session_state.auto_play = False  # Stop at the end
                st.experimental_rerun()
        
        # Current step info
        current_step = st.session_state.animation_step
        if current_step > 0:
            current_failures = cascade_path[cascade_path['CASCADE_ORDER'] <= current_step]
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; margin-top: 16px;">
                <div style="color: #EF4444; font-size: 24px; font-weight: 700;">{len(current_failures)}</div>
                <div style="color: #94A3B8; font-size: 12px;">Nodes Failed</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Progress indicator
        progress = current_step / max_cascade_order if max_cascade_order > 0 else 0
        st.progress(progress)
        st.caption(f"Step {current_step} of {max_cascade_order}")
    
    with col1:
        # Get cascade simulation data
        cascade_sim = cascade_path.copy()
        
        # Create animated graph
        fig = create_animated_cascade_graph(
            nodes_df=nodes_df,
            edges_df=edges_df,
            simulation_df=cascade_sim,
            current_step=st.session_state.animation_step if st.session_state.animation_step > 0 else None,
            title=f"Winter Storm 2021 - Cascade Propagation (Step {st.session_state.animation_step})"
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No cascade data available for animation")

st.markdown("---")

# Counter-Factual Analysis
st.markdown("## 🔄 What If We Had Reinforced Patient Zero?")

if cascade_stats is not None and len(cascade_stats) > 0 and patient_zero_df is not None and len(patient_zero_df) > 0:
    stats = cascade_stats.iloc[0]
    
    # Calculate actual impact
    actual_impact = {
        'load_shed': float(stats['TOTAL_LOAD_SHED'] or 0),
        'customers': int(stats['TOTAL_CUSTOMERS'] or 0),
        'cost': float(stats['TOTAL_COST'] or 0)
    }
    
    # Calculate prevented impact (assuming Patient Zero reinforcement prevents downstream cascade)
    # Query for impact without Patient Zero
    downstream_impact = session.sql("""
        SELECT 
            SUM(LOAD_SHED_MW) as LOAD_SHED,
            SUM(CUSTOMERS_IMPACTED) as CUSTOMERS,
            SUM(REPAIR_COST) as COST
        FROM SIMULATION_RESULTS
        WHERE SCENARIO_NAME = 'WINTER_STORM_2021'
        AND CASCADE_ORDER > 1
    """).to_pandas()
    
    if len(downstream_impact) > 0:
        di = downstream_impact.iloc[0]
        prevented_impact = {
            'load_shed': float(di['LOAD_SHED'] or 0),
            'customers': int(di['CUSTOMERS'] or 0),
            'cost': float(di['COST'] or 0)
        }
    else:
        prevented_impact = {'load_shed': 0, 'customers': 0, 'cost': 0}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create comparison chart
        fig = create_counterfactual_chart(actual_impact, prevented_impact)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Prevention Potential")
        
        pct_load = (prevented_impact['load_shed'] / max(actual_impact['load_shed'], 1)) * 100
        pct_customers = (prevented_impact['customers'] / max(actual_impact['customers'], 1)) * 100
        pct_cost = (prevented_impact['cost'] / max(actual_impact['cost'], 1)) * 100
        
        st.markdown(f"""
        <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); 
                    border-radius: 12px; padding: 20px;">
            <div style="color: #22C55E; font-size: 14px; font-weight: 600; margin-bottom: 16px;">
                BY REINFORCING PATIENT ZERO
            </div>
            <div style="margin-bottom: 16px;">
                <div style="color: white; font-size: 28px; font-weight: 700;">{pct_load:.0f}%</div>
                <div style="color: #94A3B8; font-size: 12px;">Load Shed Prevented</div>
            </div>
            <div style="margin-bottom: 16px;">
                <div style="color: white; font-size: 28px; font-weight: 700;">{prevented_impact['customers']:,}</div>
                <div style="color: #94A3B8; font-size: 12px;">Customers Protected</div>
            </div>
            <div>
                <div style="color: white; font-size: 28px; font-weight: 700;">${prevented_impact['cost']/1000000:.1f}M</div>
                <div style="color: #94A3B8; font-size: 12px;">Damages Avoided</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ROI Calculator
st.markdown("## 💰 Infrastructure Investment ROI Calculator")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Investment Parameters")
    
    reinforcement_cost = st.slider(
        "Patient Zero Reinforcement Cost ($M)",
        min_value=1.0,
        max_value=50.0,
        value=10.0,
        step=1.0
    )
    
    annual_probability = st.slider(
        "Annual Probability of Similar Event (%)",
        min_value=1,
        max_value=50,
        value=10,
        step=1
    )
    
    planning_horizon = st.slider(
        "Planning Horizon (Years)",
        min_value=5,
        max_value=30,
        value=10,
        step=1
    )

with col2:
    st.markdown("### ROI Analysis")
    
    if cascade_stats is not None and len(cascade_stats) > 0:
        stats = cascade_stats.iloc[0]
        avoided_cost_per_event = float(stats['TOTAL_COST'] or 0)
        
        # Calculate expected value
        expected_events = planning_horizon * (annual_probability / 100)
        expected_savings = expected_events * avoided_cost_per_event
        investment = reinforcement_cost * 1000000
        net_benefit = expected_savings - investment
        roi = ((expected_savings - investment) / investment) * 100 if investment > 0 else 0
        
        roi_color = "#22C55E" if roi > 0 else "#EF4444"
        
        st.markdown(f"""
        <div style="background: rgba(41, 181, 232, 0.1); border: 1px solid rgba(41, 181, 232, 0.3); 
                    border-radius: 12px; padding: 24px;">
            <div style="margin-bottom: 20px;">
                <div style="color: #94A3B8; font-size: 12px;">Expected Events ({planning_horizon} years)</div>
                <div style="color: white; font-size: 24px; font-weight: 700;">{expected_events:.1f}</div>
            </div>
            <div style="margin-bottom: 20px;">
                <div style="color: #94A3B8; font-size: 12px;">Expected Cost Avoided</div>
                <div style="color: white; font-size: 24px; font-weight: 700;">${expected_savings/1000000:.1f}M</div>
            </div>
            <div style="margin-bottom: 20px;">
                <div style="color: #94A3B8; font-size: 12px;">Net Benefit</div>
                <div style="color: {roi_color}; font-size: 24px; font-weight: 700;">${net_benefit/1000000:+.1f}M</div>
            </div>
            <div style="padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #94A3B8; font-size: 12px;">Return on Investment</div>
                <div style="color: {roi_color}; font-size: 36px; font-weight: 700;">{roi:+.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if roi > 100:
            st.success("✅ Strong investment case - ROI exceeds 100%")
        elif roi > 0:
            st.info("📊 Positive ROI - consider additional risk factors")
        else:
            st.warning("⚠️ Negative ROI at current assumptions")

st.markdown("---")

# Cascade Propagation Path (Text Version)
st.markdown("## 📋 Cascade Propagation Details")

if cascade_path is not None and len(cascade_path) > 0:
    st.markdown("""
    The GNN traced the cascade failure as it propagated through the network:
    """)
    
    for _, row in cascade_path.iterrows():
        order = int(row['CASCADE_ORDER'])
        is_first = order == 1
        
        if is_first:
            bg_color = "rgba(139, 92, 246, 0.2)"
            border_color = "rgba(139, 92, 246, 0.4)"
            label = "PATIENT ZERO"
        else:
            bg_color = "rgba(239, 68, 68, 0.1)"
            border_color = "rgba(239, 68, 68, 0.3)"
            label = f"CASCADE #{order}"
        
        st.markdown(f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: {'#8B5CF6' if is_first else '#EF4444'}; font-size: 12px; font-weight: 600;">{label}</span>
                    <div style="color: white; font-size: 18px; font-weight: 600;">{row['NODE_NAME']}</div>
                    <div style="color: #94A3B8; font-size: 14px;">{row['REGION']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #29B5E8; font-size: 24px; font-weight: 700;">{row['FAILURE_PROBABILITY']:.0%}</div>
                    <div style="color: #94A3B8; font-size: 12px;">{row['LOAD_SHED_MW']:.0f} MW shed</div>
                </div>
            </div>
            {f'<div style="color: #94A3B8; font-size: 13px; margin-top: 12px; font-style: italic;">{row["AI_EXPLANATION"]}</div>' if pd.notna(row.get('AI_EXPLANATION')) else ''}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Cascade path data not available")

st.markdown("---")

# Regional Breakdown (Director-focused)
st.markdown("## Regional Impact Breakdown")

# Get regional breakdown for cascade
regional_cascade = session.sql("""
    SELECT 
        n.REGION,
        COUNT(*) as TOTAL_NODES,
        COUNT(CASE WHEN sr.CASCADE_ORDER IS NOT NULL THEN 1 END) as FAILED_NODES,
        ROUND(SUM(sr.LOAD_SHED_MW), 0) as LOAD_SHED_MW,
        ROUND(SUM(sr.REPAIR_COST), 0) as REPAIR_COST
    FROM GRID_NODES n
    JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
    WHERE sr.SCENARIO_NAME = 'WINTER_STORM_2021'
    GROUP BY n.REGION
    ORDER BY REPAIR_COST DESC
""").to_pandas()

if regional_cascade is not None and len(regional_cascade) > 0:
    st.markdown("""
    <div style="color: #94A3B8; margin-bottom: 16px;">
        Which regions contributed most to the cascade failure?
    </div>
    """, unsafe_allow_html=True)
    
    # Color mapping for regions (matching actual data format with spaces)
    region_colors = {
        'Permian Basin': '#e74c3c',
        'Gulf Coast': '#1abc9c',
        'Panhandle': '#e67e22',
        'East Texas': '#27ae60',
        'West Texas': '#3498db',
        'North Central': '#9b59b6',
        'South Central': '#f39c12',
        # Fallback for uppercase versions
        'WEST_TEXAS': '#3498db',
        'NORTH_CENTRAL': '#9b59b6',
        'COASTAL': '#1abc9c',
        'SOUTH_TEXAS': '#f39c12',
    }
    
    cols = st.columns(len(regional_cascade))
    
    total_cost = regional_cascade['REPAIR_COST'].sum() if pd.notna(regional_cascade['REPAIR_COST'].sum()) else 0
    
    for i, (_, row) in enumerate(regional_cascade.iterrows()):
        with cols[i]:
            region_name = str(row['REGION']).replace('_', ' ').title()
            color = region_colors.get(row['REGION'], '#888888')
            
            # Handle None/NaN values safely
            failed_nodes = int(row['FAILED_NODES']) if pd.notna(row['FAILED_NODES']) else 0
            total_nodes = int(row['TOTAL_NODES']) if pd.notna(row['TOTAL_NODES']) else 0
            repair_cost = float(row['REPAIR_COST']) if pd.notna(row['REPAIR_COST']) else 0.0
            pct_of_total = (repair_cost / total_cost * 100) if total_cost > 0 else 0
            
            # Determine if this is the worst region
            max_cost = regional_cascade['REPAIR_COST'].max()
            is_worst = repair_cost > 0 and repair_cost == max_cost
            
            # Build badge separately to avoid f-string issues
            badge = '<span style="color: #EF4444; font-size: 10px; margin-left: 8px;">HIGHEST IMPACT</span>' if is_worst else ''
            bg_color = 'rgba(239, 68, 68, 0.1)' if is_worst else 'rgba(27, 42, 65, 0.6)'
            border_color = 'rgba(239, 68, 68, 0.4)' if is_worst else 'rgba(41, 181, 232, 0.2)'
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-left: 4px solid {color}; border-radius: 12px; padding: 20px;">
                <div style="color: white; font-size: 16px; font-weight: 600; margin-bottom: 12px;">
                    {region_name} {badge}
                </div>
                <div style="color: {color}; font-size: 28px; font-weight: 700;">
                    {failed_nodes}
                </div>
                <div style="color: #94A3B8; font-size: 12px; margin-bottom: 12px;">
                    nodes failed of {total_nodes}
                </div>
                <div style="color: white; font-size: 18px; font-weight: 600;">
                    ${repair_cost/1000000:.1f}M
                </div>
                <div style="color: #94A3B8; font-size: 12px;">
                    {pct_of_total:.0f}% of total damage
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Regional insight callout
    worst_region = regional_cascade.iloc[0]
    worst_region_name = str(worst_region['REGION']).replace('_', ' ').title()
    worst_cost = float(worst_region['REPAIR_COST']) if pd.notna(worst_region['REPAIR_COST']) else 0.0
    worst_pct = (worst_cost / total_cost * 100) if total_cost > 0 else 0
    
    st.markdown(f"""
    <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-left: 4px solid #8B5CF6; border-radius: 8px; padding: 16px; margin-top: 24px;">
        <div style="color: #8B5CF6; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
            REGIONAL INSIGHT
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b style="color: white;">{worst_region_name}</b> accounts for 
            <b style="color: white;">{worst_pct:.0f}%</b> of total cascade damage.
            Prioritizing infrastructure upgrades in this region would have the highest impact on grid resilience.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Scenario Comparison
st.markdown("## Scenario Comparison")

if comparison is not None and len(comparison) > 0:
    st.markdown("""
    The GNN analyzed multiple scenarios. Here's how they compare:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    for i, (_, row) in enumerate(comparison.iterrows()):
        with [col1, col2, col3][i % 3]:
            scenario = row['SCENARIO_NAME']
            is_worst = row['COST'] == comparison['COST'].max()
            
            if is_worst:
                bg = "rgba(239, 68, 68, 0.1)"
                border = "rgba(239, 68, 68, 0.4)"
            else:
                bg = "rgba(27, 42, 65, 0.6)"
                border = "rgba(41, 181, 232, 0.2)"
            
            st.markdown(f"""
            <div style="background: {bg}; border: 1px solid {border}; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="color: white; font-size: 16px; font-weight: 600; margin-bottom: 12px;">
                    {scenario.replace('_', ' ')}
                </div>
                <div style="color: #29B5E8; font-size: 28px; font-weight: 700;">
                    {int(row['FAILURES'])} failures
                </div>
                <div style="color: #94A3B8; font-size: 14px; margin-top: 8px;">
                    {row['LOAD_SHED']:,.0f} MW shed<br/>
                    ${row['COST']:,.0f} cost
                </div>
                {'<div style="color: #EF4444; font-size: 12px; margin-top: 8px; font-weight: 600;">HIGHEST IMPACT</div>' if is_worst else ''}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Key Takeaways
st.markdown("## Key Takeaways")

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(41, 181, 232, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%); border-radius: 16px; padding: 32px; border: 1px solid rgba(41, 181, 232, 0.3);">
<div style="font-size: 20px; color: white; font-weight: 600; margin-bottom: 20px;">What the GNN Analysis Revealed</div>
<div style="color: #94A3B8; font-size: 16px; line-height: 1.8;">
<div style="margin-bottom: 16px;"><span style="color: #29B5E8; font-weight: 600;">1. Early Warning is Possible</span><br/>The GNN identified Patient Zero with high confidence before the cascade began. This demonstrates that predictive intervention is feasible.</div>
<div style="margin-bottom: 16px;"><span style="color: #29B5E8; font-weight: 600;">2. Topology Matters</span><br/>The cascade origin was not the largest or most loaded node - it was a strategically positioned bottleneck. Network analysis reveals vulnerabilities that capacity monitoring misses.</div>
<div><span style="color: #29B5E8; font-weight: 600;">3. Small Changes, Big Impact</span><br/>Reinforcing just a few critical nodes could prevent cascading failures across the entire grid. The model identifies exactly which nodes to prioritize.</div>
</div>
</div>
""", unsafe_allow_html=True)

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>2_Simulation_Results</b> | Next: <b>4_Take_Action</b>
</div>
""", unsafe_allow_html=True)

