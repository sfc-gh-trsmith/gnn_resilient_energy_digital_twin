"""
GridGuard - Scenario Builder

Interactive what-if scenario exploration for grid stress testing.
Allows users to adjust parameters and see predicted cascade effects.
"""

import streamlit as st
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import run_queries_parallel
from utils.viz import create_animated_cascade_graph, COLORS

st.set_page_config(
    page_title="Scenario Builder | GridGuard",
    page_icon="🔧",
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
    
    .param-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        margin-bottom: 16px;
    }
    
    .result-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(41, 181, 232, 0.1) 100%);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    .prediction-header {
        font-size: 14px;
        color: #8B5CF6;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    
    .prediction-value {
        font-size: 48px;
        font-weight: 700;
        color: white;
    }
    
    .warning-banner {
        background: rgba(234, 179, 8, 0.1);
        border: 1px solid rgba(234, 179, 8, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .danger-banner {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("🔧 Scenario Builder")
st.markdown("""
Create custom stress scenarios to explore "what-if" conditions. 
Adjust environmental parameters and manually disable nodes to see predicted cascade effects.
""")

st.markdown("---")

# Load base data
with st.spinner("Loading grid data..."):
    queries = {
        'nodes': "SELECT * FROM GRID_NODES ORDER BY NODE_NAME",
        'edges': "SELECT * FROM GRID_EDGES",
        'scenarios': """
            SELECT SCENARIO_NAME, 
                   AVG(TEMPERATURE_F) as AVG_TEMP,
                   AVG(LOAD_MW) as AVG_LOAD,
                   COUNT(DISTINCT CASE WHEN STATUS = 'FAILED' THEN NODE_ID END) as FAILURE_COUNT
            FROM HISTORICAL_TELEMETRY
            GROUP BY SCENARIO_NAME
        """,
        'base_results': """
            SELECT * FROM SIMULATION_RESULTS 
            WHERE SCENARIO_NAME = 'WINTER_STORM_2021'
        """
    }
    data = run_queries_parallel(session, queries)

nodes_df = data.get('nodes', pd.DataFrame())
edges_df = data.get('edges', pd.DataFrame())
scenarios_df = data.get('scenarios', pd.DataFrame())
base_results = data.get('base_results', pd.DataFrame())

# Scenario Parameters
st.markdown("## 📊 Scenario Parameters")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Environmental Conditions")
    
    # Temperature control
    temperature = st.slider(
        "🌡️ Ambient Temperature (°F)",
        min_value=-20,
        max_value=120,
        value=32,
        step=5,
        help="Lower temperatures increase stress on grid infrastructure"
    )
    
    # Show temperature context
    if temperature < 20:
        st.markdown("""
        <div class="danger-banner">
            <span style="color: #EF4444; font-weight: 600;">⚠️ Extreme Cold Warning</span>
            <p style="color: #94A3B8; margin-top: 4px; font-size: 13px;">
                Temperatures below 20°F significantly increase failure risk due to equipment stress and natural gas supply issues.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif temperature > 100:
        st.markdown("""
        <div class="danger-banner">
            <span style="color: #EF4444; font-weight: 600;">⚠️ Extreme Heat Warning</span>
            <p style="color: #94A3B8; margin-top: 4px; font-size: 13px;">
                High temperatures reduce transmission efficiency and increase cooling load demands.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Load multiplier
    load_multiplier = st.slider(
        "⚡ Load Multiplier",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="1.0 = normal load, 2.0 = double normal load"
    )
    
    if load_multiplier > 1.5:
        st.markdown("""
        <div class="warning-banner">
            <span style="color: #EAB308; font-weight: 600;">⚡ High Load Conditions</span>
            <p style="color: #94A3B8; margin-top: 4px; font-size: 13px;">
                Load above 150% increases risk of overloading transmission lines.
            </p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### Manual Node Overrides")
    
    # Get node options
    node_options = nodes_df['NODE_NAME'].tolist() if len(nodes_df) > 0 else []
    
    # Multi-select for disabled nodes
    disabled_nodes = st.multiselect(
        "🔴 Disable Nodes (Simulate Failures)",
        options=node_options,
        help="Select nodes to manually mark as failed in the simulation"
    )
    
    if disabled_nodes:
        st.markdown(f"""
        <div class="danger-banner">
            <span style="color: #EF4444; font-weight: 600;">
                {len(disabled_nodes)} Node(s) Manually Disabled
            </span>
            <p style="color: #94A3B8; margin-top: 4px; font-size: 13px;">
                These nodes will be treated as failed in the cascade prediction.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Region focus
    regions = nodes_df['REGION'].unique().tolist() if len(nodes_df) > 0 else []
    selected_regions = st.multiselect(
        "🗺️ Focus Regions (Optional)",
        options=regions,
        default=regions,
        help="Filter analysis to specific regions"
    )

st.markdown("---")

# Run Analysis Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_analysis = st.button(
        "🚀 Run Scenario Analysis",
        use_container_width=True,
        type="primary"
    )

# Analysis Results
if run_analysis:
    st.markdown("---")
    st.markdown("## 🎯 Scenario Prediction Results")
    
    with st.spinner("Calculating cascade predictions..."):
        # Calculate stress factors based on parameters
        # Temperature stress: exponential increase below 20°F or above 100°F
        temp_stress = 0
        if temperature < 20:
            temp_stress = (20 - temperature) / 40  # Max 1.0 at -20°F
        elif temperature > 100:
            temp_stress = (temperature - 100) / 20  # Max 1.0 at 120°F
        temp_stress = min(temp_stress, 1.0)
        
        # Load stress
        load_stress = max(0, (load_multiplier - 1.0) / 1.0)  # 0 at 1.0, 1.0 at 2.0
        
        # Combined stress factor
        combined_stress = min(1.0, temp_stress * 0.5 + load_stress * 0.5)
        
        # Get base failure probabilities and adjust
        if base_results is not None and len(base_results) > 0:
            # Create adjusted predictions
            predictions = base_results.copy()
            
            # Adjust failure probabilities based on stress
            base_probs = predictions['FAILURE_PROBABILITY'].values
            adjusted_probs = base_probs + (1 - base_probs) * combined_stress * 0.3
            
            # Mark manually disabled nodes
            disabled_node_ids = []
            if disabled_nodes:
                disabled_node_ids = nodes_df[nodes_df['NODE_NAME'].isin(disabled_nodes)]['NODE_ID'].tolist()
                for node_id in disabled_node_ids:
                    mask = predictions['NODE_ID'] == node_id
                    adjusted_probs[mask] = 1.0
            
            predictions['ADJUSTED_PROBABILITY'] = adjusted_probs
            predictions['IS_DISABLED'] = predictions['NODE_ID'].isin(disabled_node_ids)
            
            # Calculate predicted cascade metrics
            high_risk_count = (adjusted_probs > 0.7).sum()
            predicted_failures = (adjusted_probs > 0.8).sum() + len(disabled_nodes)
            
            # Estimate impact based on failure count
            avg_load_per_node = nodes_df['CAPACITY_MW'].mean() if len(nodes_df) > 0 else 500
            predicted_load_shed = predicted_failures * avg_load_per_node * 0.6
            predicted_customers = int(predicted_failures * 50000)
            predicted_cost = predicted_failures * 5000000
            
            # Display Results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                risk_color = "#EF4444" if combined_stress > 0.5 else "#EAB308" if combined_stress > 0.2 else "#22C55E"
                st.markdown(f"""
                <div class="result-card">
                    <div class="prediction-header">Stress Level</div>
                    <div class="prediction-value" style="color: {risk_color};">{combined_stress*100:.0f}%</div>
                    <div style="color: #94A3B8; font-size: 12px;">Combined Risk Factor</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="result-card">
                    <div class="prediction-header">High Risk Nodes</div>
                    <div class="prediction-value">{high_risk_count}</div>
                    <div style="color: #94A3B8; font-size: 12px;">Above 70% failure probability</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="result-card">
                    <div class="prediction-header">Predicted Failures</div>
                    <div class="prediction-value" style="color: #EF4444;">{predicted_failures}</div>
                    <div style="color: #94A3B8; font-size: 12px;">Expected cascade size</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="result-card">
                    <div class="prediction-header">Est. Impact</div>
                    <div class="prediction-value">${predicted_cost/1000000:.1f}M</div>
                    <div style="color: #94A3B8; font-size: 12px;">{predicted_customers:,} customers</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Visualization
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Predicted Grid State")
                
                # Create visualization with adjusted probabilities
                viz_df = predictions.copy()
                viz_df['FAILURE_PROBABILITY'] = viz_df['ADJUSTED_PROBABILITY']
                viz_df['CASCADE_ORDER'] = None
                viz_df.loc[viz_df['ADJUSTED_PROBABILITY'] > 0.8, 'CASCADE_ORDER'] = 1
                viz_df.loc[viz_df['IS_DISABLED'], 'IS_PATIENT_ZERO'] = True
                
                fig = create_animated_cascade_graph(
                    nodes_df=nodes_df,
                    edges_df=edges_df,
                    simulation_df=viz_df,
                    current_step=None,
                    title=f"Custom Scenario ({temperature}°F, {load_multiplier}x load)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Risk Distribution")
                
                # Risk breakdown
                very_high = (adjusted_probs > 0.8).sum()
                high = ((adjusted_probs > 0.6) & (adjusted_probs <= 0.8)).sum()
                medium = ((adjusted_probs > 0.4) & (adjusted_probs <= 0.6)).sum()
                low = (adjusted_probs <= 0.4).sum()
                
                st.markdown(f"""
                <div class="param-card">
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #EF4444;">● Very High (&gt;80%)</span>
                            <span style="color: white; font-weight: 700;">{very_high}</span>
                        </div>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #F97316;">● High (60-80%)</span>
                            <span style="color: white; font-weight: 700;">{high}</span>
                        </div>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #EAB308;">● Medium (40-60%)</span>
                            <span style="color: white; font-weight: 700;">{medium}</span>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #22C55E;">● Low (&lt;40%)</span>
                            <span style="color: white; font-weight: 700;">{low}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Most at-risk nodes
                st.markdown("### Most At-Risk Nodes")
                top_risk = predictions.nlargest(5, 'ADJUSTED_PROBABILITY')[['NODE_ID', 'ADJUSTED_PROBABILITY']]
                top_risk = top_risk.merge(nodes_df[['NODE_ID', 'NODE_NAME', 'REGION']], on='NODE_ID', how='left')
                
                for _, row in top_risk.iterrows():
                    prob = row['ADJUSTED_PROBABILITY']
                    prob_color = "#EF4444" if prob > 0.8 else "#EAB308"
                    st.markdown(f"""
                    <div style="background: rgba(27, 42, 65, 0.4); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;">
                        <div style="color: white; font-weight: 600;">{row['NODE_NAME']}</div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8; font-size: 11px;">{row['REGION']}</span>
                            <span style="color: {prob_color}; font-weight: 600;">{prob:.0%}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Comparison with base scenarios
            st.markdown("### Scenario Comparison")
            
            if scenarios_df is not None and len(scenarios_df) > 0:
                comparison_data = []
                for _, row in scenarios_df.iterrows():
                    comparison_data.append({
                        'Scenario': row['SCENARIO_NAME'].replace('_', ' '),
                        'Avg Temp (°F)': f"{row['AVG_TEMP']:.0f}" if row['AVG_TEMP'] else "N/A",
                        'Failures': int(row['FAILURE_COUNT']) if row['FAILURE_COUNT'] else 0
                    })
                
                # Add custom scenario
                comparison_data.append({
                    'Scenario': '→ CUSTOM (Current)',
                    'Avg Temp (°F)': f"{temperature}",
                    'Failures': predicted_failures
                })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(
                    comparison_df,
                    use_container_width=True
                )
        else:
            st.warning("No base simulation results available to build predictions from.")

# Show preset scenarios for quick selection
st.markdown("---")
st.markdown("## 🎛️ Preset Scenarios")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="param-card">
        <div style="color: #29B5E8; font-weight: 600; margin-bottom: 8px;">❄️ Winter Storm</div>
        <div style="color: #94A3B8; font-size: 13px;">
            Temperature: -10°F<br/>
            Load: 1.8x normal<br/>
            <em>Simulates 2021 Uri conditions</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Apply Winter Storm", key="preset_winter", use_container_width=True):
        st.session_state['scenario_temp'] = -10
        st.session_state['scenario_load'] = 1.8
        st.experimental_rerun()

with col2:
    st.markdown("""
    <div class="param-card">
        <div style="color: #EAB308; font-weight: 600; margin-bottom: 8px;">🔥 Summer Peak</div>
        <div style="color: #94A3B8; font-size: 13px;">
            Temperature: 105°F<br/>
            Load: 1.5x normal<br/>
            <em>High AC demand period</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Apply Summer Peak", key="preset_summer", use_container_width=True):
        st.session_state['scenario_temp'] = 105
        st.session_state['scenario_load'] = 1.5
        st.experimental_rerun()

with col3:
    st.markdown("""
    <div class="param-card">
        <div style="color: #22C55E; font-weight: 600; margin-bottom: 8px;">✅ Normal Operations</div>
        <div style="color: #94A3B8; font-size: 13px;">
            Temperature: 70°F<br/>
            Load: 1.0x normal<br/>
            <em>Baseline conditions</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Apply Normal", key="preset_normal", use_container_width=True):
        st.session_state['scenario_temp'] = 70
        st.session_state['scenario_load'] = 1.0
        st.experimental_rerun()

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>6_Ask_GridGuard</b> | Next: <b>8_Regional_Analysis</b>
</div>
""", unsafe_allow_html=True)

