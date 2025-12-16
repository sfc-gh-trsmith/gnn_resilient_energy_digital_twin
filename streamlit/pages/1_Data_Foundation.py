"""
GridGuard - Data Foundation Page

Shows grid topology, data sources, and the foundation of the analysis.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.data_loader import run_queries_parallel, get_table_row_counts

st.set_page_config(
    page_title="Data Foundation | GridGuard",
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
    .data-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        margin-bottom: 16px;
    }
    .data-title {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
    }
    .data-value {
        font-size: 32px;
        font-weight: 700;
        color: #29B5E8;
    }
    .data-desc {
        font-size: 14px;
        color: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("Data Foundation")
st.markdown("""
The GridGuard analysis is built on a comprehensive data foundation that captures
grid topology, operational telemetry, and compliance requirements.
""")

st.markdown("---")

# Load data in parallel
queries = {
    'nodes': "SELECT * FROM GRID_NODES",
    'edges': "SELECT * FROM GRID_EDGES",
    'row_counts': """
        SELECT 'GRID_NODES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM GRID_NODES
        UNION ALL SELECT 'GRID_EDGES', COUNT(*) FROM GRID_EDGES
        UNION ALL SELECT 'HISTORICAL_TELEMETRY', COUNT(*) FROM HISTORICAL_TELEMETRY
        UNION ALL SELECT 'COMPLIANCE_DOCS', COUNT(*) FROM COMPLIANCE_DOCS
        UNION ALL SELECT 'SIMULATION_RESULTS', COUNT(*) FROM SIMULATION_RESULTS
    """,
    'region_summary': """
        SELECT REGION, COUNT(*) as NODE_COUNT, 
               SUM(CAPACITY_MW) as TOTAL_CAPACITY_MW,
               AVG(CRITICALITY_SCORE) as AVG_CRITICALITY
        FROM GRID_NODES
        GROUP BY REGION
        ORDER BY TOTAL_CAPACITY_MW DESC
    """
}

with st.spinner("Loading data..."):
    data = run_queries_parallel(session, queries)

nodes_df = data.get('nodes', pd.DataFrame())
edges_df = data.get('edges', pd.DataFrame())
row_counts = data.get('row_counts', pd.DataFrame())
region_summary = data.get('region_summary', pd.DataFrame())

# Data Source Cards
st.markdown("## Data Sources")

col1, col2, col3, col4 = st.columns(4)

def get_row_count(table_name):
    if row_counts is not None and len(row_counts) > 0:
        match = row_counts[row_counts['TABLE_NAME'] == table_name]
        if len(match) > 0:
            return match.iloc[0]['ROW_COUNT']
    return 0

with col1:
    count = get_row_count('GRID_NODES')
    st.markdown(f"""
    <div class="data-card">
        <div class="data-title">Grid Nodes</div>
        <div class="data-value">{count:,}</div>
        <div class="data-desc">Substations, generators, load centers</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    count = get_row_count('GRID_EDGES')
    st.markdown(f"""
    <div class="data-card">
        <div class="data-title">Transmission Lines</div>
        <div class="data-value">{count:,}</div>
        <div class="data-desc">High-voltage interconnections</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    count = get_row_count('HISTORICAL_TELEMETRY')
    st.markdown(f"""
    <div class="data-card">
        <div class="data-title">Telemetry Records</div>
        <div class="data-value">{count:,}</div>
        <div class="data-desc">Time-series operational data</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    count = get_row_count('COMPLIANCE_DOCS')
    st.markdown(f"""
    <div class="data-card">
        <div class="data-title">Compliance Docs</div>
        <div class="data-value">{count:,}</div>
        <div class="data-desc">NERC regulations indexed</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Grid Topology Map
st.markdown("## Grid Topology")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Geographic Distribution")
    
    if nodes_df is not None and len(nodes_df) > 0:
        # Create PyDeck map layer
        # Color nodes by type
        type_colors = {
            'SUBSTATION': [41, 181, 232, 200],      # Blue
            'GENERATOR': [34, 197, 94, 200],         # Green
            'LOAD_CENTER': [234, 179, 8, 200],       # Yellow
            'TRANSMISSION_HUB': [139, 92, 246, 200]  # Purple
        }
        
        nodes_df['color'] = nodes_df['NODE_TYPE'].map(
            lambda x: type_colors.get(x, [148, 163, 184, 200])
        )
        
        # Create layer
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=nodes_df,
            get_position='[LON, LAT]',
            get_color='color',
            get_radius='CAPACITY_MW * 5',
            radius_min_pixels=5,
            radius_max_pixels=30,
            pickable=True
        )
        
        # Create view
        view = pdk.ViewState(
            latitude=31.5,
            longitude=-99.0,
            zoom=5,
            pitch=0
        )
        
        # Create deck
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip={
                'text': '{NODE_NAME}\nType: {NODE_TYPE}\nCapacity: {CAPACITY_MW} MW\nRegion: {REGION}'
            },
            map_style=None  # Required for SiS CSP compliance
        )
        
        st.pydeck_chart(deck)
        
        # Legend
        st.markdown("""
        **Legend:** 
        <span style="color: #29B5E8;">●</span> Substation 
        <span style="color: #22C55E;">●</span> Generator 
        <span style="color: #EAB308;">●</span> Load Center 
        <span style="color: #8B5CF6;">●</span> Transmission Hub
        """, unsafe_allow_html=True)
    else:
        st.warning("No grid node data available")

with col2:
    st.markdown("### Region Summary")
    
    if region_summary is not None and len(region_summary) > 0:
        for _, row in region_summary.iterrows():
            st.markdown(f"""
            <div class="data-card">
                <div class="data-title">{row['REGION']}</div>
                <div style="color: #94A3B8; font-size: 14px;">
                    {row['NODE_COUNT']} nodes | {row['TOTAL_CAPACITY_MW']:,.0f} MW
                </div>
                <div style="color: #29B5E8; font-size: 12px;">
                    Avg Criticality: {row['AVG_CRITICALITY']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Region data loading...")

st.markdown("---")

# Node Type Distribution
st.markdown("## Infrastructure Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Node Types")
    if nodes_df is not None and len(nodes_df) > 0:
        type_counts = nodes_df['NODE_TYPE'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        st.dataframe(
            type_counts,
            use_container_width=True
        )

with col2:
    st.markdown("### Edge Types")
    if edges_df is not None and len(edges_df) > 0:
        edge_counts = edges_df['EDGE_TYPE'].value_counts().reset_index()
        edge_counts.columns = ['Type', 'Count']
        st.dataframe(
            edge_counts,
            use_container_width=True
        )

st.markdown("---")

# Sample Data
st.markdown("## Sample Data")

tab1, tab2, tab3 = st.tabs(["Grid Nodes", "Grid Edges", "Telemetry Schema"])

with tab1:
    if nodes_df is not None and len(nodes_df) > 0:
        display_cols = ['NODE_ID', 'NODE_NAME', 'NODE_TYPE', 'REGION', 'CAPACITY_MW', 'CRITICALITY_SCORE']
        st.dataframe(
            nodes_df[display_cols].head(10),
            use_container_width=True
        )

with tab2:
    if edges_df is not None and len(edges_df) > 0:
        display_cols = ['EDGE_ID', 'SRC_NODE', 'DST_NODE', 'EDGE_TYPE', 'CAPACITY_MW', 'LENGTH_MILES']
        st.dataframe(
            edges_df[display_cols].head(10),
            use_container_width=True
        )

with tab3:
    st.markdown("""
    The `HISTORICAL_TELEMETRY` table contains time-series sensor data:
    
    | Column | Description |
    |--------|-------------|
    | TIMESTAMP | Measurement timestamp (15-min intervals) |
    | NODE_ID | Reference to grid node |
    | SCENARIO_NAME | Simulation scenario |
    | VOLTAGE_KV | Measured voltage |
    | LOAD_MW | Current load |
    | TEMPERATURE_F | Ambient temperature |
    | STATUS | ACTIVE, WARNING, FAILED |
    | ALERT_CODE | Alert type if triggered |
    """)

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate between pages. Next: <b>2_Simulation_Results</b>
</div>
""", unsafe_allow_html=True)

