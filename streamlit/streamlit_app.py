"""
GridGuard - Energy Grid Resilience Digital Twin
Main Landing Page

This Streamlit app presents a business-focused walkthrough of the GridGuard
energy grid resilience analysis powered by Graph Neural Networks.
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session

# Page configuration
st.set_page_config(
    page_title="GridGuard - Energy Grid Resilience",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Snowflake brand styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #0f1419 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B2A41 0%, #0f1419 100%);
        border-right: 1px solid rgba(41, 181, 232, 0.2);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Hero section */
    .hero-container {
        background: linear-gradient(135deg, rgba(41, 181, 232, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 16px;
        padding: 48px;
        margin-bottom: 32px;
        border: 1px solid rgba(41, 181, 232, 0.3);
    }
    
    .hero-title {
        font-size: 48px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 16px;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 20px;
        color: #94A3B8;
        margin-bottom: 32px;
        line-height: 1.6;
    }
    
    .hero-stat {
        font-size: 36px;
        font-weight: 700;
        color: #29B5E8;
    }
    
    .hero-stat-label {
        font-size: 14px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        height: 100%;
    }
    
    .feature-icon {
        font-size: 32px;
        margin-bottom: 16px;
    }
    
    .feature-title {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        font-size: 14px;
        color: #94A3B8;
    }
    
    /* CTA button */
    .stButton > button {
        background: linear-gradient(135deg, #29B5E8 0%, #1E88E5 100%);
        color: white;
        border: none;
        padding: 12px 32px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1E88E5 0%, #29B5E8 100%);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #29B5E8 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session
session = get_active_session()

# Sidebar
with st.sidebar:
    st.image("https://www.snowflake.com/wp-content/themes/snowflake/assets/img/brand-guidelines/logo-sno-blue-example.svg", width=180)
    st.markdown("---")
    st.markdown("### GridGuard")
    st.markdown("*Energy Grid Resilience Digital Twin*")
    st.markdown("---")
    st.markdown("**Quick Navigation**")
    st.markdown("""
    **Director Path:**
    - Executive Dashboard
    - Regional Analysis
    - Scenario Builder
    
    **Full Demo:**
    1. Data Foundation
    2. Simulation Results
    3. Key Insights
    4. Take Action
    5. Ask GridGuard
    """)

# Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">
        Predict Grid Failures<br/>
        <span style="color: #29B5E8;">Before They Cascade</span>
    </div>
    <div class="hero-subtitle">
        GridGuard uses Graph Neural Networks to analyze power grid topology and identify 
        vulnerable nodes that could trigger cascading failures. Powered by Snowflake's 
        unified data platform and Cortex AI.
    </div>
</div>
""", unsafe_allow_html=True)

# Problem Statement
st.markdown("## The Challenge")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    Power grid operators face a critical challenge: **cascade failures can propagate 
    through interconnected infrastructure in minutes**, leaving millions without power 
    and causing billions in damages.
    
    Traditional monitoring systems detect failures *after* they happen. By then, the 
    cascade has already begun. Grid operators need **predictive intelligence** that 
    can identify vulnerable "Patient Zero" nodes before they trigger system-wide outages.
    
    **The 2021 Texas Winter Storm** demonstrated the devastating consequences:
    - 4.5 million customers lost power
    - $130 billion in economic damages
    - Cascade failures originated from a small number of critical nodes
    
    What if we could have predicted which substations would fail first?
    """)

with col2:
    # Key statistics
    st.markdown("### By The Numbers")
    
    # Try to get actual counts from database
    try:
        counts = session.sql("""
            SELECT 
                (SELECT COUNT(*) FROM GRID_NODES) as nodes,
                (SELECT COUNT(*) FROM GRID_EDGES) as edges,
                (SELECT COUNT(DISTINCT SCENARIO_NAME) FROM SIMULATION_RESULTS) as scenarios
        """).to_pandas().iloc[0]
        
        st.metric("Grid Nodes", f"{counts['NODES']:,}")
        st.metric("Transmission Lines", f"{counts['EDGES']:,}")
        st.metric("Scenarios Analyzed", f"{counts['SCENARIOS']:,}")
    except:
        st.metric("Grid Nodes", "45")
        st.metric("Transmission Lines", "106")
        st.metric("Scenarios Analyzed", "3")

st.markdown("---")

# Solution Overview
st.markdown("## The Solution: AI-Powered Grid Intelligence")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">Graph Neural Networks</div>
        <div class="feature-desc">
            Our GCN model analyzes grid topology to understand how failures 
            propagate through interconnected infrastructure. It identifies 
            "Patient Zero" nodes before cascade events occur.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">Snowflake Cortex AI</div>
        <div class="feature-desc">
            Cortex Analyst answers questions about simulation results using 
            natural language. Cortex Search retrieves relevant compliance 
            regulations for incident response.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Real-Time Insights</div>
        <div class="feature-desc">
            Pre-computed scenario analysis means instant results. Explore 
            different stress scenarios and see potential cascade paths 
            without waiting for simulations.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Architecture Overview
st.markdown("## How It Works")

# SVG Architecture Diagram
st.markdown("""
<div style="display: flex; justify-content: center; padding: 20px 0;">
<svg width="720" height="580" viewBox="0 0 720 580" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Outer container - Snowflake Data Cloud -->
  <rect x="10" y="10" width="700" height="560" rx="16" fill="url(#bgGradient)" stroke="#29B5E8" stroke-width="2"/>
  
  <!-- Header bar -->
  <rect x="10" y="10" width="700" height="44" rx="16" fill="rgba(41, 181, 232, 0.15)"/>
  <rect x="10" y="38" width="700" height="16" fill="rgba(41, 181, 232, 0.15)"/>
  <text x="360" y="38" fill="#29B5E8" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="700" text-anchor="middle">SNOWFLAKE DATA CLOUD</text>
  
  <!-- Data Sources Row -->
  <!-- GRID_NODES -->
  <rect x="80" y="80" width="140" height="60" rx="8" fill="rgba(27, 42, 65, 0.8)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="150" y="105" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" text-anchor="middle">GRID_NODES</text>
  <text x="150" y="125" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">(Topology)</text>
  
  <!-- GRID_EDGES -->
  <rect x="290" y="80" width="140" height="60" rx="8" fill="rgba(27, 42, 65, 0.8)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="360" y="105" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" text-anchor="middle">GRID_EDGES</text>
  <text x="360" y="125" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">(Connections)</text>
  
  <!-- TELEMETRY -->
  <rect x="500" y="80" width="140" height="60" rx="8" fill="rgba(27, 42, 65, 0.8)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="570" y="105" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" text-anchor="middle">TELEMETRY</text>
  <text x="570" y="125" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">(Time Series)</text>
  
  <!-- Connectors from data sources -->
  <path d="M150 140 L150 160 L360 160 L360 180" stroke="#64748B" stroke-width="1.5" fill="none"/>
  <path d="M360 140 L360 180" stroke="#64748B" stroke-width="1.5" fill="none"/>
  <path d="M570 140 L570 160 L360 160" stroke="#64748B" stroke-width="1.5" fill="none"/>
  
  <!-- Arrow down -->
  <polygon points="360,180 354,170 366,170" fill="#64748B"/>
  
  <!-- PyTorch Geometric Box -->
  <rect x="250" y="190" width="220" height="70" rx="10" fill="rgba(34, 197, 94, 0.15)" stroke="#22C55E" stroke-width="2"/>
  <text x="360" y="218" fill="#22C55E" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" text-anchor="middle">PyTorch Geometric</text>
  <text x="360" y="236" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="12" text-anchor="middle">GCN Model (GPU)</text>
  <text x="360" y="252" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">via SPCS Notebook</text>
  
  <!-- Connector -->
  <line x1="360" y1="260" x2="360" y2="290" stroke="#64748B" stroke-width="1.5"/>
  <polygon points="360,290 354,280 366,280" fill="#64748B"/>
  
  <!-- SIMULATION_RESULTS Box -->
  <rect x="230" y="300" width="260" height="90" rx="10" fill="rgba(41, 181, 232, 0.15)" stroke="#29B5E8" stroke-width="2"/>
  <text x="360" y="328" fill="#29B5E8" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" text-anchor="middle">SIMULATION_RESULTS</text>
  <text x="360" y="350" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">• Patient Zero ID</text>
  <text x="360" y="366" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="11" text-anchor="middle">• Cascade Order  •  Risk Scores</text>
  
  <!-- Branching connectors -->
  <line x1="360" y1="390" x2="360" y2="410" stroke="#64748B" stroke-width="1.5"/>
  <line x1="150" y1="410" x2="570" y2="410" stroke="#64748B" stroke-width="1.5"/>
  <line x1="150" y1="410" x2="150" y2="430" stroke="#64748B" stroke-width="1.5"/>
  <line x1="360" y1="410" x2="360" y2="430" stroke="#64748B" stroke-width="1.5"/>
  <line x1="570" y1="410" x2="570" y2="430" stroke="#64748B" stroke-width="1.5"/>
  
  <!-- Arrows -->
  <polygon points="150,430 144,420 156,420" fill="#64748B"/>
  <polygon points="360,430 354,420 366,420" fill="#64748B"/>
  <polygon points="570,430 564,420 576,420" fill="#64748B"/>
  
  <!-- Cortex Services Row -->
  <!-- Cortex Analyst -->
  <rect x="80" y="440" width="140" height="55" rx="8" fill="rgba(139, 92, 246, 0.15)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="150" y="462" fill="#8B5CF6" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" text-anchor="middle">Cortex Analyst</text>
  <text x="150" y="482" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="10" text-anchor="middle">(SQL Q&A)</text>
  
  <!-- Cortex Search -->
  <rect x="290" y="440" width="140" height="55" rx="8" fill="rgba(139, 92, 246, 0.15)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="360" y="462" fill="#8B5CF6" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" text-anchor="middle">Cortex Search</text>
  <text x="360" y="482" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="10" text-anchor="middle">(Compliance)</text>
  
  <!-- Cortex Agent -->
  <rect x="500" y="440" width="140" height="55" rx="8" fill="rgba(139, 92, 246, 0.15)" stroke="#8B5CF6" stroke-width="1.5"/>
  <text x="570" y="462" fill="#8B5CF6" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" text-anchor="middle">Cortex Agent</text>
  <text x="570" y="482" fill="#94A3B8" font-family="system-ui, -apple-system, sans-serif" font-size="10" text-anchor="middle">(Orchestrator)</text>
  
  <!-- Final connectors -->
  <line x1="150" y1="495" x2="150" y2="510" stroke="#64748B" stroke-width="1.5"/>
  <line x1="570" y1="495" x2="570" y2="510" stroke="#64748B" stroke-width="1.5"/>
  <line x1="360" y1="495" x2="360" y2="510" stroke="#64748B" stroke-width="1.5"/>
  <line x1="150" y1="510" x2="570" y2="510" stroke="#64748B" stroke-width="1.5"/>
  <line x1="360" y1="510" x2="360" y2="525" stroke="#64748B" stroke-width="1.5"/>
  <polygon points="360,525 354,515 366,515" fill="#64748B"/>
  
  <!-- Streamlit Dashboard Box -->
  <rect x="230" y="535" width="260" height="28" rx="6" fill="rgba(239, 68, 68, 0.15)" stroke="#EF4444" stroke-width="1.5"/>
  <text x="360" y="554" fill="#EF4444" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" text-anchor="middle">STREAMLIT DASHBOARD</text>
  
  <!-- Gradient definitions -->
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:rgba(15, 20, 25, 0.95)"/>
      <stop offset="50%" style="stop-color:rgba(26, 35, 50, 0.95)"/>
      <stop offset="100%" style="stop-color:rgba(15, 20, 25, 0.95)"/>
    </linearGradient>
  </defs>
</svg>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Persona-Based Navigation
st.markdown("## Choose Your Path")

st.markdown("""
<div style="color: #94A3B8; font-size: 16px; margin-bottom: 24px;">
    GridGuard serves different stakeholders. Select your role for a tailored experience:
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(41, 181, 232, 0.15) 0%, rgba(41, 181, 232, 0.05) 100%);
        border-radius: 16px;
        padding: 28px;
        border: 2px solid rgba(41, 181, 232, 0.4);
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    ">
        <div style="font-size: 40px; margin-bottom: 16px;">📊</div>
        <div style="font-size: 20px; font-weight: 700; color: #29B5E8; margin-bottom: 8px;">
            Director of Grid Planning
        </div>
        <div style="font-size: 14px; color: #94A3B8; line-height: 1.6; margin-bottom: 16px;">
            Strategic investment prioritization, scenario comparison, and ROI analysis for infrastructure upgrades.
        </div>
        <div style="font-size: 12px; color: #64748B; font-style: italic;">
            "Simulate how our infrastructure would handle a repeat of the 2021 Winter Storm to prioritize upgrades."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Executive Dashboard →", key="btn_director", use_container_width=True):
        st.info("👈 Please select **0_Executive_Dashboard** from the sidebar to continue.")

with col2:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%);
        border-radius: 16px;
        padding: 28px;
        border: 2px solid rgba(139, 92, 246, 0.4);
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    ">
        <div style="font-size: 40px; margin-bottom: 16px;">📋</div>
        <div style="font-size: 20px; font-weight: 700; color: #8B5CF6; margin-bottom: 8px;">
            Compliance Officer
        </div>
        <div style="font-size: 14px; color: #94A3B8; line-height: 1.6; margin-bottom: 16px;">
            Audit trails, regulatory compliance, and detailed telemetry investigation for incident response.
        </div>
        <div style="font-size: 12px; color: #64748B; font-style: italic;">
            "Review the specific maintenance logs and voltage readings from a failed substation to audit our response."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Take Action →", key="btn_compliance", use_container_width=True):
        st.info("👈 Please select **4_Take_Action** from the sidebar to continue.")

with col3:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(34, 197, 94, 0.05) 100%);
        border-radius: 16px;
        padding: 28px;
        border: 2px solid rgba(34, 197, 94, 0.4);
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    ">
        <div style="font-size: 40px; margin-bottom: 16px;">🔬</div>
        <div style="font-size: 20px; font-weight: 700; color: #22C55E; margin-bottom: 8px;">
            Data Scientist
        </div>
        <div style="font-size: 14px; color: #94A3B8; line-height: 1.6; margin-bottom: 16px;">
            Model exploration, data analysis, and algorithm validation without managing complex pipelines.
        </div>
        <div style="font-size: 12px; color: #64748B; font-style: italic;">
            "Run complex graph algorithms on static snapshots of data without managing complex data pipelines."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Data Foundation →", key="btn_data_scientist", use_container_width=True):
        st.info("👈 Please select **1_Data_Foundation** from the sidebar to continue.")

st.markdown("---")

# Standard Tour Option
st.markdown("## Or Take the Full Tour")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style="text-align: center; color: #94A3B8; margin-bottom: 16px;">
        Walk through all capabilities in a guided sequence
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    1. **Data Foundation** - Explore the grid topology and data sources
    2. **Simulation Results** - View GNN-powered cascade analysis
    3. **Key Insights** - Discover the "Patient Zero" identification
    4. **Take Action** - Get compliance guidance via Cortex AI
    """)
    
    if st.button("Start the Full Tour →", use_container_width=True, key="btn_tour"):
        st.info("👈 Please select **1_Data_Foundation** from the sidebar to start the tour.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 12px;">
    Built with Snowflake | PyTorch Geometric | Cortex AI<br/>
    GridGuard Demo - Energy Grid Resilience Digital Twin
</div>
""", unsafe_allow_html=True)

