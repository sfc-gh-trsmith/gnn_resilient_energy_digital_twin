"""
GridGuard - Simulation Results Page

Displays pre-computed GNN cascade analysis results with interactive network visualization.
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import run_queries_parallel, get_cascade_analysis
from utils.viz import create_network_graph, create_kpi_card, create_cascade_flow_diagram

st.set_page_config(
    page_title="Simulation Results | GridGuard",
    page_icon="🔬",
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
    [data-testid="stMetricValue"] {
        color: #29B5E8 !important;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("Simulation Results")
st.markdown("""
Explore the GNN-powered cascade analysis results. The model has analyzed multiple 
stress scenarios to identify failure patterns and vulnerable infrastructure.
""")

# View Mode Toggle (using checkbox for SiS compatibility)
col_header1, col_header2 = st.columns([3, 1])
with col_header2:
    view_mode = st.checkbox("Executive View", value=False, help="Simplified view for executives")

st.markdown("---")

# Scenario Selection
st.markdown("## Select Scenario")

# Get available scenarios
scenarios_df = session.sql("""
    SELECT DISTINCT SCENARIO_NAME 
    FROM SIMULATION_RESULTS 
    ORDER BY SCENARIO_NAME
""").to_pandas()

if len(scenarios_df) == 0:
    st.warning("No simulation results available. Please run the notebook first using: `./run.sh main`")
    st.stop()

scenario_options = scenarios_df['SCENARIO_NAME'].tolist()
selected_scenario = st.selectbox(
    "Choose a scenario to analyze:",
    options=scenario_options,
    index=scenario_options.index('WINTER_STORM_2021') if 'WINTER_STORM_2021' in scenario_options else 0
)

# Load data for selected scenario
with st.spinner("Loading simulation results..."):
    queries = {
        'nodes': "SELECT * FROM GRID_NODES",
        'edges': "SELECT * FROM GRID_EDGES",
        'simulation': f"""
            SELECT * FROM SIMULATION_RESULTS 
            WHERE SCENARIO_NAME = '{selected_scenario}'
        """,
        'impact': f"""
            SELECT * FROM VW_SCENARIO_IMPACT
            WHERE SCENARIO_NAME = '{selected_scenario}'
        """
    }
    data = run_queries_parallel(session, queries)

nodes_df = data.get('nodes', pd.DataFrame())
edges_df = data.get('edges', pd.DataFrame())
simulation_df = data.get('simulation', pd.DataFrame())
impact_df = data.get('impact', pd.DataFrame())

st.markdown("---")

# =============================================================================
# EXECUTIVE VIEW - Simplified for Directors
# =============================================================================
if view_mode:
    st.markdown("""
    <div style="background: rgba(41, 181, 232, 0.1); border: 1px solid rgba(41, 181, 232, 0.3); border-radius: 12px; padding: 16px; margin-bottom: 24px;">
        <div style="color: #29B5E8; font-size: 14px; font-weight: 600;">EXECUTIVE VIEW</div>
        <div style="color: #94A3B8; font-size: 13px;">Simplified metrics for strategic decision-making</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive KPIs
    if impact_df is not None and len(impact_df) > 0:
        impact = impact_df.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Impact",
                f"${(impact['TOTAL_REPAIR_COST'] or 0)/1000000:.1f}M",
                delta="Repair Costs"
            )
        
        with col2:
            st.metric(
                "Cascade Size",
                f"{int(impact['TOTAL_NODES_AFFECTED'] or 0)} nodes"
            )
        
        with col3:
            st.metric(
                "Customers Affected",
                f"{int(impact['TOTAL_CUSTOMERS_IMPACTED'] or 0):,}"
            )
        
        with col4:
            st.metric(
                "Load Shed",
                f"{(impact['TOTAL_LOAD_SHED_MW'] or 0)/1000:.1f} GW"
            )
    
    st.markdown("---")
    
    # Executive Summary
    st.markdown("## Executive Summary")
    
    if simulation_df is not None and len(simulation_df) > 0:
        patient_zero = simulation_df[simulation_df['IS_PATIENT_ZERO'] == True]
        if len(patient_zero) > 0:
            pz = patient_zero.iloc[0]
            node_info = nodes_df[nodes_df['NODE_ID'] == pz['NODE_ID']]
            node_name = node_info.iloc[0]['NODE_NAME'] if len(node_info) > 0 else pz['NODE_ID']
            node_region = node_info.iloc[0]['REGION'].replace('_', ' ').title() if len(node_info) > 0 else 'Unknown'
            
            total_cost = impact_df.iloc[0]['TOTAL_REPAIR_COST'] if impact_df is not None and len(impact_df) > 0 else 0
            
            st.markdown(f"""
            <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 24px;">
                <div style="color: white; font-size: 16px; line-height: 1.8;">
                    The <b>{selected_scenario.replace('_', ' ').title()}</b> scenario identified 
                    <b style="color: #8B5CF6;">{node_name}</b> in {node_region} as the cascade origin point.
                    <br/><br/>
                    <b>Key Finding:</b> Reinforcing this single node could prevent up to 
                    <b style="color: #22C55E;">${total_cost/1000000:.1f}M</b> in damages.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Top 5 Critical Nodes
    st.markdown("## Top 5 Critical Nodes")
    
    if simulation_df is not None and len(simulation_df) > 0:
        top_nodes = simulation_df.nlargest(5, 'RISK_SCORE').merge(
            nodes_df[['NODE_ID', 'NODE_NAME', 'REGION']],
            on='NODE_ID',
            how='left'
        )
        
        # Rename columns for display
        display_df = top_nodes[['NODE_NAME', 'REGION', 'RISK_SCORE', 'REPAIR_COST']].copy()
        display_df.columns = ['Node', 'Region', 'Risk Score', 'Repair Cost ($)']
        st.dataframe(
            display_df,
            use_container_width=True
        )
    
    # Link to Executive Dashboard
    st.markdown("---")
    if st.button("📊 Go to Executive Dashboard", use_container_width=True):
        st.info("👈 Please select **0_Executive_Dashboard** from the sidebar.")

# =============================================================================
# FULL TECHNICAL VIEW
# =============================================================================
else:
    # KPI Cards
    st.markdown("## Scenario Impact Summary")
    
    if impact_df is not None and len(impact_df) > 0:
        impact = impact_df.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Nodes Affected",
                f"{int(impact['TOTAL_NODES_AFFECTED'] or 0):,}",
                delta=f"of {len(nodes_df)} total"
            )
        
        with col2:
            st.metric(
                "Total Load Shed",
                f"{impact['TOTAL_LOAD_SHED_MW'] or 0:,.0f} MW"
            )
        
        with col3:
            st.metric(
                "Customers Impacted",
                f"{int(impact['TOTAL_CUSTOMERS_IMPACTED'] or 0):,}"
            )
        
        with col4:
            st.metric(
                "Repair Cost",
                f"${impact['TOTAL_REPAIR_COST'] or 0:,.0f}"
            )
    else:
        st.info("No impact data available for this scenario")
    
    st.markdown("---")
    
    # Network Visualization
    st.markdown("## Network Topology & Cascade Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if nodes_df is not None and edges_df is not None and simulation_df is not None:
            fig = create_network_graph(
                nodes_df=nodes_df,
                edges_df=edges_df,
                simulation_df=simulation_df,
                highlight_patient_zero=True,
                title=f"{selected_scenario} - Cascade Analysis"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data for network visualization")
    
    with col2:
        st.markdown("### Analysis Legend")
        st.markdown("""
        <div style="background: rgba(27, 42, 65, 0.6); padding: 16px; border-radius: 8px; border: 1px solid rgba(41, 181, 232, 0.2);">
            <div style="margin-bottom: 12px;">
                <span style="color: #8B5CF6; font-size: 20px;">●</span>
                <span style="color: white; margin-left: 8px;"><b>Patient Zero</b></span>
                <div style="color: #94A3B8; font-size: 12px; margin-left: 28px;">Cascade origin node</div>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: #EF4444; font-size: 20px;">●</span>
                <span style="color: white; margin-left: 8px;"><b>Failed</b></span>
                <div style="color: #94A3B8; font-size: 12px; margin-left: 28px;">Nodes in cascade path</div>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: #EAB308; font-size: 20px;">●</span>
                <span style="color: white; margin-left: 8px;"><b>Warning</b></span>
                <div style="color: #94A3B8; font-size: 12px; margin-left: 28px;">High failure probability</div>
            </div>
            <div>
                <span style="color: #22C55E; font-size: 20px;">●</span>
                <span style="color: white; margin-left: 8px;"><b>Active</b></span>
                <div style="color: #94A3B8; font-size: 12px; margin-left: 28px;">Operating normally</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Patient Zero info
        if simulation_df is not None and len(simulation_df) > 0:
            patient_zero = simulation_df[simulation_df['IS_PATIENT_ZERO'] == True]
            if len(patient_zero) > 0:
                pz = patient_zero.iloc[0]
                node_info = nodes_df[nodes_df['NODE_ID'] == pz['NODE_ID']]
                node_name = node_info.iloc[0]['NODE_NAME'] if len(node_info) > 0 else pz['NODE_ID']
                
                st.markdown("### Patient Zero")
                st.markdown(f"""
                <div style="background: rgba(139, 92, 246, 0.2); padding: 16px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.4);">
                    <div style="color: #8B5CF6; font-weight: 600;">{node_name}</div>
                    <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">
                        Failure Probability: {pz['FAILURE_PROBABILITY']:.1%}<br/>
                        Risk Score: {pz['RISK_SCORE']:.4f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Cascade Flow Analysis
    st.markdown("## Cascade Flow Analysis")
    
    if simulation_df is not None and len(simulation_df) > 0:
        # Check if we have cascade data
        has_cascade_data = (
            'CASCADE_ORDER' in simulation_df.columns and 
            simulation_df['CASCADE_ORDER'].notna().any()
        )
        
        if has_cascade_data:
            # Merge with node info for the flow diagram
            cascade_df = simulation_df.merge(
                nodes_df[['NODE_ID', 'NODE_NAME', 'NODE_TYPE', 'REGION']],
                on='NODE_ID',
                how='left'
            )
            
            fig = create_cascade_flow_diagram(cascade_df)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div style="background: rgba(27, 42, 65, 0.4); padding: 12px; border-radius: 8px; margin-top: 8px;">
                <div style="color: #94A3B8; font-size: 12px;">
                    <b>Reading the diagram:</b> Shows how failures propagate from Patient Zero to different infrastructure types. 
                    Flow width represents total load shed (MW) per asset type. Hover over nodes to see affected components.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No cascade propagation data available for this scenario")
    else:
        st.info("No simulation data available")
    
    st.markdown("---")
    
    # Detailed Results Table
    st.markdown("## Detailed Results")
    
    if simulation_df is not None and len(simulation_df) > 0:
        # Merge with node info
        results_display = simulation_df.merge(
            nodes_df[['NODE_ID', 'NODE_NAME', 'NODE_TYPE', 'REGION']],
            on='NODE_ID',
            how='left'
        )
        
        # Sort by cascade order, then by failure probability
        results_display = results_display.sort_values(
            by=['CASCADE_ORDER', 'FAILURE_PROBABILITY'],
            ascending=[True, False],
            na_position='last'
        )
        
        # Display columns
        display_cols = [
            'NODE_NAME', 'REGION', 'NODE_TYPE', 
            'FAILURE_PROBABILITY', 'IS_PATIENT_ZERO', 
            'CASCADE_ORDER', 'LOAD_SHED_MW', 'CUSTOMERS_IMPACTED'
        ]
        
        # Rename columns for display
        display_df = results_display[display_cols].head(20).copy()
        display_df.columns = ['Node', 'Region', 'Type', 'Failure Prob', 'Patient Zero', 'Cascade #', 'Load Shed (MW)', 'Customers']
        st.dataframe(
            display_df,
            use_container_width=True
        )

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>1_Data_Foundation</b> | Next: <b>3_Key_Insights</b>
</div>
""", unsafe_allow_html=True)

