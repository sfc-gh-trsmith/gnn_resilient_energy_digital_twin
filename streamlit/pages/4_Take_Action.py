"""
GridGuard - Take Action Page

Provides Cortex Agent-powered compliance guidance, action recommendations,
and intelligent chat for combined data + compliance queries.
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.cortex import (
    query_cortex_search, 
    format_search_results,
    get_compliance_context,
    generate_action_recommendations,
    query_cortex_agent
)

st.set_page_config(
    page_title="Take Action | GridGuard",
    page_icon="🎯",
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
    .action-card {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(41, 181, 232, 0.2);
        margin-bottom: 16px;
    }
    .action-priority-1 {
        border-left: 4px solid #EF4444;
    }
    .action-priority-2 {
        border-left: 4px solid #EAB308;
    }
    .action-priority-3 {
        border-left: 4px solid #22C55E;
    }
    .compliance-result {
        background: rgba(41, 181, 232, 0.1);
        border: 1px solid rgba(41, 181, 232, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Header
st.title("Take Action")
st.markdown("""
Based on the GNN analysis, here are recommended actions and compliance requirements.
Use Cortex Search to find relevant regulations and procedures.
""")

st.markdown("---")

# Scenario context
selected_scenario = "WINTER_STORM_2021"

# Action Recommendations
st.markdown("## Recommended Actions")

try:
    recommendations = generate_action_recommendations(session, selected_scenario)
    
    for i, rec in enumerate(recommendations):
        priority_class = f"action-priority-{min(i+1, 3)}"
        priority_label = ["HIGH", "MEDIUM", "NORMAL"][min(i, 2)]
        priority_color = ["#EF4444", "#EAB308", "#22C55E"][min(i, 2)]
        
        st.markdown(f"""
        <div class="action-card {priority_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <span style="color: {priority_color}; font-size: 11px; font-weight: 600; 
                                  background: rgba({",".join(str(int(priority_color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))}, 0.2);
                                  padding: 2px 8px; border-radius: 4px;">
                        {priority_label} PRIORITY
                    </span>
                    <div style="color: white; font-size: 16px; margin-top: 8px; line-height: 1.6;">
                        {rec}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading recommendations: {e}")

st.markdown("---")

# Compliance Context
st.markdown("## Regulatory Impact Assessment")

try:
    context = get_compliance_context(session, selected_scenario)
    st.markdown(f"""
    <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); 
                border-radius: 12px; padding: 24px;">
        <div style="color: white; font-size: 16px; line-height: 1.8; white-space: pre-line;">
{context}
        </div>
    </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Could not load compliance context: {e}")

st.markdown("---")

# Cortex Agent Chat Interface
st.markdown("## 🤖 Ask GridGuard Agent")
st.markdown("""
Ask questions about both **simulation data** and **compliance requirements**. 
The GridGuard Agent combines AI-powered data analysis with regulatory knowledge.
""")

# Initialize agent chat history in session state
if 'agent_chat_history' not in st.session_state:
    st.session_state.agent_chat_history = []

# Suggested queries for agent
st.markdown("**Quick questions:**")
suggested = [
    "Based on this simulation, what forms do I need to file?",
    "What's the total repair cost and which regulations apply?",
    "Which node failed first and what are the reporting requirements?",
    "Summarize the cascade impact and next steps"
]

cols = st.columns(4)
for i, query in enumerate(suggested):
    with cols[i]:
        if st.button(query, key=f"agent_suggested_{i}", use_container_width=True):
            st.session_state.pending_agent_query = query
            st.experimental_rerun()

# Display agent chat history
if st.session_state.agent_chat_history:
    st.markdown("### Conversation")
    for msg in st.session_state.agent_chat_history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        if role == 'user':
            st.markdown(f"""
            <div style="background: rgba(41, 181, 232, 0.1); border: 1px solid rgba(41, 181, 232, 0.3); 
                        border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="color: #29B5E8; font-size: 11px; margin-bottom: 4px;">YOU</div>
                <div style="color: white;">{content}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sources = msg.get('sources', [])
            source_tags = ""
            if 'data' in sources:
                source_tags += '<span style="background: rgba(34, 197, 94, 0.2); color: #22C55E; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-right: 4px;">📊 Data</span>'
            if 'compliance' in sources:
                source_tags += '<span style="background: rgba(139, 92, 246, 0.2); color: #8B5CF6; padding: 2px 6px; border-radius: 4px; font-size: 10px;">📚 Compliance</span>'
            
            st.markdown(f"""
            <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); 
                        border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="color: #8B5CF6; font-size: 11px; margin-bottom: 4px;">GRIDGUARD AGENT {source_tags}</div>
                <div style="color: white; line-height: 1.6;">{content}</div>
            </div>
            """, unsafe_allow_html=True)

# Agent chat input (using text_input for SiS compatibility)
col_input, col_btn = st.columns([4, 1])
with col_input:
    agent_query_input = st.text_input(
        "Ask about simulation results, compliance requirements, or both...",
        key="agent_query_input",
        label_visibility="collapsed"
    )
with col_btn:
    send_clicked = st.button("Send", key="agent_send_btn", use_container_width=True)

agent_query = agent_query_input if send_clicked and agent_query_input else None

# Handle pending query from suggested buttons
if hasattr(st.session_state, 'pending_agent_query') and st.session_state.pending_agent_query:
    agent_query = st.session_state.pending_agent_query
    st.session_state.pending_agent_query = None

if agent_query:
    # Add user message
    st.session_state.agent_chat_history.append({
        'role': 'user',
        'content': agent_query
    })
    
    with st.spinner("GridGuard Agent is thinking..."):
        try:
            result = query_cortex_agent(
                session,
                agent_query,
                conversation_history=st.session_state.agent_chat_history[-10:],
                scenario_context=selected_scenario
            )
            
            if result.get('success'):
                sources = [s[0] for s in result.get('sources', [])]
                st.session_state.agent_chat_history.append({
                    'role': 'assistant',
                    'content': result['response'],
                    'sources': sources
                })
            else:
                st.session_state.agent_chat_history.append({
                    'role': 'assistant',
                    'content': f"I encountered an issue: {result.get('error', 'Unknown error')}. Please try rephrasing your question.",
                    'sources': []
                })
        except Exception as e:
            st.session_state.agent_chat_history.append({
                'role': 'assistant',
                'content': f"Error: {str(e)}",
                'sources': []
            })
    
    st.experimental_rerun()

# Clear chat button
if st.session_state.agent_chat_history:
    if st.button("🗑️ Clear Conversation"):
        st.session_state.agent_chat_history = []
        st.experimental_rerun()

st.markdown("---")

# Fallback: Direct Compliance Search
with st.expander("📚 Direct Compliance Document Search"):
    search_query = st.text_input(
        "Search compliance documents:",
        placeholder="e.g., cascade failure reporting requirements, OE-417 form, voltage collapse...",
        key="direct_search"
    )
    
    if search_query:
        with st.spinner("Searching..."):
            try:
                results = query_cortex_search(session, search_query, top_k=5)
                
                if results:
                    for i, result in enumerate(results, 1):
                        reg_code = result.get('REGULATION_CODE', 'N/A')
                        title = result.get('TITLE', 'Untitled')
                        content = result.get('CONTENT', '')[:400]
                        
                        st.markdown(f"""
                        <div class="compliance-result">
                            <span style="color: #29B5E8; font-size: 12px; font-weight: 600;">{reg_code}</span>
                            <div style="color: white; font-size: 14px; font-weight: 600; margin-top: 4px;">{title}</div>
                            <div style="color: #94A3B8; font-size: 13px; margin-top: 8px;">{content}...</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No matching documents found.")
            except Exception as e:
                st.error(f"Search error: {str(e)}")

st.markdown("---")

# Quick Reference
st.markdown("## Quick Reference: Key Reporting Requirements")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="action-card">
        <div style="color: #29B5E8; font-size: 14px; font-weight: 600; margin-bottom: 12px;">
            DOE Form OE-417
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b>When Required:</b> Load shedding > 100 MW<br/>
            <b>Timeline:</b> Initial report within 6 hours, final within 30 days<br/>
            <b>Submit to:</b> DOE Office of Electricity
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="action-card">
        <div style="color: #29B5E8; font-size: 14px; font-weight: 600; margin-bottom: 12px;">
            Regional Entity Notification
        </div>
        <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
            <b>When Required:</b> Voltage collapse > 300 MW<br/>
            <b>Timeline:</b> Within 1 hour of event<br/>
            <b>Contact:</b> ERCOT Reliability Coordinator
        </div>
    </div>
    """, unsafe_allow_html=True)

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>3_Key_Insights</b> | Next: <b>6_Ask_GridGuard</b>
</div>
""", unsafe_allow_html=True)

