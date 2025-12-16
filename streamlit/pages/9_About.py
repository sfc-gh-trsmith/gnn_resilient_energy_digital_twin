"""
GridGuard - About Page

Tells the story of the demo: the problem, solution, and before/after transformation.
This page should always be LAST in the sidebar navigation.
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="About | GridGuard",
    page_icon="ℹ️",
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
    .story-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        margin-bottom: 16px;
    }
    .problem-card {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left: 4px solid #EF4444;
        border-radius: 12px;
        padding: 24px;
    }
    .solution-card {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-left: 4px solid #22C55E;
        border-radius: 12px;
        padding: 24px;
    }
    .before-after-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .tech-badge {
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid #3b82f6;
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 4px;
    }
    .persona-card {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
    }
    .wow-moment {
        background: linear-gradient(135deg, rgba(41, 181, 232, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 2px solid rgba(41, 181, 232, 0.4);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("About GridGuard")
st.markdown("""
**Project GridGuard** is a demonstration of how Snowflake's unified platform enables 
advanced AI/ML applications for critical infrastructure resilience analysis.
""")

st.markdown("---")

# =============================================================================
# THE PROBLEM
# =============================================================================
st.markdown("## The Problem")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="problem-card">
        <div class="before-after-label" style="color: #EF4444;">THE CHALLENGE</div>
        <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 16px;">
            Grid Operators Are Flying Blind
        </div>
        <div style="color: #94A3B8; font-size: 15px; line-height: 1.8;">
            Energy grid operators struggle to analyze post-incident data or simulate "what-if" scenarios 
            because their <b>topological data is locked in complex formats</b>. They lack the ability to 
            easily run advanced graph algorithms to understand how past failures propagated, 
            <b>preventing them from updating safety protocols effectively</b>.
            <br/><br/>
            <b>Key Pain Points:</b>
            <ul style="margin-top: 12px;">
                <li>Weeks to model a single disaster scenario</li>
                <li>No visibility into cascade failure patterns</li>
                <li>Manual, error-prone compliance verification</li>
                <li>Siloed data across multiple systems</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: rgba(27, 42, 65, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3); text-align: center;">
        <div style="color: #EF4444; font-size: 48px; font-weight: 700;">Weeks</div>
        <div style="color: #94A3B8; font-size: 14px;">to model a scenario</div>
    </div>
    <br/>
    <div style="background: rgba(27, 42, 65, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3); text-align: center;">
        <div style="color: #EF4444; font-size: 48px; font-weight: 700;">0%</div>
        <div style="color: #94A3B8; font-size: 14px;">topology-aware analysis</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# THE SOLUTION
# =============================================================================
st.markdown("## The Solution")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    <div style="background: rgba(27, 42, 65, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3); text-align: center;">
        <div style="color: #22C55E; font-size: 48px; font-weight: 700;">Minutes</div>
        <div style="color: #94A3B8; font-size: 14px;">to model a scenario</div>
    </div>
    <br/>
    <div style="background: rgba(27, 42, 65, 0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3); text-align: center;">
        <div style="color: #22C55E; font-size: 48px; font-weight: 700;">100%</div>
        <div style="color: #94A3B8; font-size: 14px;">GNN-powered analysis</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="solution-card">
        <div class="before-after-label" style="color: #22C55E;">THE SOLUTION</div>
        <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 16px;">
            GridGuard: AI-Powered Grid Resilience
        </div>
        <div style="color: #94A3B8; font-size: 15px; line-height: 1.8;">
            GridGuard unifies grid topology, operational telemetry, and compliance documentation 
            in Snowflake, enabling advanced <b>Graph Neural Network (GNN) analysis</b> that reveals 
            hidden vulnerabilities and cascade patterns.
            <br/><br/>
            <b>Key Capabilities:</b>
            <ul style="margin-top: 12px;">
                <li><b>Instant Scenario Simulation</b> - Minutes, not weeks</li>
                <li><b>Patient Zero Identification</b> - Find cascade origins automatically</li>
                <li><b>AI-Powered Compliance</b> - Natural language regulatory guidance</li>
                <li><b>Unified Data Platform</b> - All data in one secure location</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# THE "WOW" MOMENT
# =============================================================================
st.markdown("## The Wow Moment")

st.markdown("""
<div class="wow-moment">
    <div style="color: #29B5E8; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 16px;">
        ✨ THE MAGIC MOMENT ✨
    </div>
    <div style="color: white; font-size: 20px; line-height: 1.8; max-width: 800px; margin: 0 auto;">
        The user selects a historical <b style="color: #8B5CF6;">"Winter Storm 2021"</b> event from a dropdown. 
        The system <b>instantly reconstructs the grid topology</b> for that timeframe, 
        runs the <b style="color: #22C55E;">PyTorch Geometric GNN model</b> to identify the 
        <b style="color: #EF4444;">"Patient Zero"</b> node that caused the cascade, 
        and <b style="color: #29B5E8;">Cortex AI</b> generates a complete financial impact report 
        with compliance guidance.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# BEFORE & AFTER COMPARISON
# =============================================================================
st.markdown("## Before & After")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="problem-card">
        <div class="before-after-label" style="color: #EF4444;">❌ BEFORE GRIDGUARD</div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.8;">
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Scenario Analysis</b><br/>
                Manual data extraction, spreadsheet modeling, weeks of work
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Failure Investigation</b><br/>
                Linear search through logs, miss topology-based patterns
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Compliance Verification</b><br/>
                Manual document search, prone to missing requirements
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Root Cause Analysis</b><br/>
                Intuition-based, limited to obvious failures
            </div>
            <div>
                <b style="color: white;">Protocol Updates</b><br/>
                Reactive, only after major incidents
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="solution-card">
        <div class="before-after-label" style="color: #22C55E;">✅ AFTER GRIDGUARD</div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.8;">
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Scenario Analysis</b><br/>
                Instant simulation, select dropdown → results in seconds
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Failure Investigation</b><br/>
                GNN identifies "Patient Zero" and cascade propagation path
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Compliance Verification</b><br/>
                AI-powered Cortex Search returns exact regulations instantly
            </div>
            <div style="margin-bottom: 16px;">
                <b style="color: white;">Root Cause Analysis</b><br/>
                Topology-aware ML reveals hidden network vulnerabilities
            </div>
            <div>
                <b style="color: white;">Protocol Updates</b><br/>
                Proactive, simulate scenarios before they happen
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# USER PERSONAS
# =============================================================================
st.markdown("## Who Benefits")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="persona-card">
        <div style="color: #8B5CF6; font-size: 24px; margin-bottom: 8px;">👔</div>
        <div style="color: white; font-size: 16px; font-weight: 600;">Director of Grid Planning</div>
        <div style="color: #94A3B8; font-size: 13px; margin-top: 12px; line-height: 1.6;">
            "I want to simulate how our current infrastructure would handle a repeat of the 
            '2021 Winter Storm' to prioritize upgrades."
        </div>
        <div style="color: #8B5CF6; font-size: 12px; margin-top: 12px;">
            Strategic Decision Making
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="persona-card">
        <div style="color: #29B5E8; font-size: 24px; margin-bottom: 8px;">📋</div>
        <div style="color: white; font-size: 16px; font-weight: 600;">Compliance Officer</div>
        <div style="color: #94A3B8; font-size: 13px; margin-top: 12px; line-height: 1.6;">
            "I want to review specific maintenance logs and voltage readings from a failed 
            substation to audit our response."
        </div>
        <div style="color: #29B5E8; font-size: 12px; margin-top: 12px;">
            Regulatory Compliance
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="persona-card">
        <div style="color: #22C55E; font-size: 24px; margin-bottom: 8px;">🔬</div>
        <div style="color: white; font-size: 16px; font-weight: 600;">Data Scientist</div>
        <div style="color: #94A3B8; font-size: 13px; margin-top: 12px; line-height: 1.6;">
            "I want to run complex graph algorithms on static snapshots of data without 
            managing complex data pipelines."
        </div>
        <div style="color: #22C55E; font-size: 12px; margin-top: 12px;">
            Technical Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# TECHNOLOGY STACK
# =============================================================================
st.markdown("## Technology Stack")

st.markdown("""
<div style="text-align: center; margin-bottom: 24px;">
    <span class="tech-badge">Snowflake</span>
    <span class="tech-badge">Snowpark Container Services</span>
    <span class="tech-badge">PyTorch Geometric</span>
    <span class="tech-badge">Cortex AI</span>
    <span class="tech-badge">Cortex Search</span>
    <span class="tech-badge">Cortex Agent</span>
    <span class="tech-badge">Streamlit in Snowflake</span>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="story-card">
        <div style="color: #29B5E8; font-size: 16px; font-weight: 600; margin-bottom: 12px;">
            🧠 Graph Neural Networks
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b>Framework:</b> PyTorch Geometric (GCN)<br/>
            <b>Execution:</b> GPU-accelerated via SPCS<br/>
            <b>Output:</b> Per-node failure probabilities, cascade paths, Patient Zero identification
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="story-card">
        <div style="color: #8B5CF6; font-size: 16px; font-weight: 600; margin-bottom: 12px;">
            🤖 Cortex AI Services
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b>Agent:</b> Orchestrates data + compliance queries<br/>
            <b>Analyst:</b> Natural language to SQL for metrics<br/>
            <b>Search:</b> RAG over NERC compliance documents
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="story-card">
        <div style="color: #22C55E; font-size: 16px; font-weight: 600; margin-bottom: 12px;">
            📊 Data Architecture
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b>Topology:</b> GRID_NODES, GRID_EDGES<br/>
            <b>Telemetry:</b> HISTORICAL_TELEMETRY<br/>
            <b>Results:</b> SIMULATION_RESULTS<br/>
            <b>Compliance:</b> COMPLIANCE_DOCS
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SUCCESS CRITERIA
# =============================================================================
st.markdown("## Success Criteria")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="story-card">
        <div style="color: #29B5E8; font-size: 14px; font-weight: 600; margin-bottom: 12px;">
            ⚡ TECHNICAL VALIDATOR
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            The SPCS container executes PyTorch Geometric inference on the selected 
            scenario snapshot and returns results to the Streamlit dashboard 
            <b style="color: white;">in under 15 seconds</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="story-card">
        <div style="color: #22C55E; font-size: 14px; font-weight: 600; margin-bottom: 12px;">
            📈 BUSINESS VALIDATOR
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            The demo clearly shows the link between <b style="color: white;">Data</b> (Telemetry), 
            <b style="color: white;">Insight</b> (Graph Model identifying the weak point), 
            and <b style="color: white;">Action</b> (Cortex retrieving the correct protocol).
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# APPLICATION PAGES
# =============================================================================
st.markdown("## Application Pages")

pages_info = [
    ("📊", "Executive Dashboard", "High-level KPIs and executive summary of grid resilience metrics"),
    ("🗄️", "Data Foundation", "Grid topology visualization, data sources, and infrastructure breakdown"),
    ("🔬", "Simulation Results", "Detailed GNN cascade analysis with network visualization"),
    ("💡", "Key Insights", "Patient Zero discovery, cascade animation, and ROI calculator"),
    ("🎯", "Take Action", "AI-powered recommendations and compliance guidance"),
    ("💬", "Ask GridGuard", "Natural language interface to query data and compliance docs"),
    ("🔧", "Scenario Builder", "Create custom stress scenarios for simulation"),
    ("🗺️", "Regional Analysis", "Geographic breakdown of grid vulnerabilities"),
]

cols = st.columns(2)
for i, (icon, name, desc) in enumerate(pages_info):
    with cols[i % 2]:
        st.markdown(f"""
        <div style="background: rgba(27, 42, 65, 0.6); padding: 16px; border-radius: 8px; 
                    border: 1px solid rgba(41, 181, 232, 0.2); margin-bottom: 12px;">
            <div style="color: white; font-size: 16px; font-weight: 600;">
                {icon} {name}
            </div>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 8px;">
                {desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 12px; padding: 20px;">
    <b>GridGuard</b> | Energy Grid Resilience Digital Twin<br/>
    Built with Snowflake • Snowpark Container Services • Cortex AI • Streamlit
</div>
""", unsafe_allow_html=True)

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate to other pages. Previous: <b>8_Regional_Analysis</b>
</div>
""", unsafe_allow_html=True)

