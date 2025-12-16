"""
GridGuard - Ask GridGuard (Cortex AI Chat Interface)

Provides natural language interface to query simulation data and compliance documents.
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

import sys
sys.path.insert(0, '.')
from utils.cortex import query_cortex_analyst, query_cortex_agent, query_cortex_search

st.set_page_config(
    page_title="Ask GridGuard | GridGuard",
    page_icon="💬",
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
    
    /* Chat message styling */
    .user-message {
        background: rgba(41, 181, 232, 0.1);
        border: 1px solid rgba(41, 181, 232, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .assistant-message {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .sql-block {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 12px;
        overflow-x: auto;
        margin: 12px 0;
    }
    
    .source-tag {
        display: inline-block;
        background: rgba(41, 181, 232, 0.2);
        color: #29B5E8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        margin-right: 8px;
    }
    
    .mode-selector {
        background: rgba(27, 42, 65, 0.6);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

session = get_active_session()

# Initialize session state for conversation history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'chat_mode' not in st.session_state:
    st.session_state.chat_mode = 'agent'  # 'agent', 'analyst', or 'search'

# Header
st.title("💬 Ask GridGuard")
st.markdown("""
Chat with your grid simulation data using natural language. 
GridGuard AI can answer questions about cascade failures, compliance requirements, and more.
""")

st.markdown("---")

# Mode selector
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "🤖 Agent Mode",
        use_container_width=True,
        type="primary" if st.session_state.chat_mode == 'agent' else "secondary"
    ):
        st.session_state.chat_mode = 'agent'
        st.experimental_rerun()

with col2:
    if st.button(
        "📊 Analyst Mode",
        use_container_width=True,
        type="primary" if st.session_state.chat_mode == 'analyst' else "secondary"
    ):
        st.session_state.chat_mode = 'analyst'
        st.experimental_rerun()

with col3:
    if st.button(
        "📚 Search Mode",
        use_container_width=True,
        type="primary" if st.session_state.chat_mode == 'search' else "secondary"
    ):
        st.session_state.chat_mode = 'search'
        st.experimental_rerun()

# Mode description
mode_descriptions = {
    'agent': "**Agent Mode**: Combines simulation data and compliance documents for comprehensive answers.",
    'analyst': "**Analyst Mode**: Generates and executes SQL queries against simulation results.",
    'search': "**Search Mode**: Searches NERC regulations and compliance documents."
}
st.info(mode_descriptions[st.session_state.chat_mode])

st.markdown("---")

# Suggested questions
st.markdown("### 💡 Try asking...")

suggested_questions = {
    'agent': [
        "What caused the cascade in the winter storm scenario?",
        "What compliance forms do I need after a cascade failure?",
        "Which region was most impacted and what should I do about it?"
    ],
    'analyst': [
        "What was the total repair cost for the winter storm scenario?",
        "Which node had the highest failure probability?",
        "How many customers were impacted in each region?"
    ],
    'search': [
        "What are the NERC reporting requirements for cascade failures?",
        "When do I need to file DOE Form OE-417?",
        "What are the voltage collapse notification timelines?"
    ]
}

cols = st.columns(3)
for i, question in enumerate(suggested_questions[st.session_state.chat_mode]):
    with cols[i]:
        if st.button(question, key=f"suggested_{i}", use_container_width=True):
            st.session_state.pending_question = question
            st.experimental_rerun()

st.markdown("---")

# Chat container
st.markdown("### 💬 Conversation")

# Display chat history
for i, message in enumerate(st.session_state.chat_history):
    role = message.get('role', 'user')
    content = message.get('content', '')
    
    if role == 'user':
        st.markdown(f"""
        <div class="user-message">
            <div style="color: #29B5E8; font-size: 12px; margin-bottom: 8px;">YOU</div>
            <div style="color: white;">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Assistant message with optional SQL and sources
        sql = message.get('sql', '')
        sources = message.get('sources', [])
        
        source_tags = ""
        if 'data' in str(sources):
            source_tags += '<span class="source-tag">📊 Simulation Data</span>'
        if 'compliance' in str(sources):
            source_tags += '<span class="source-tag">📚 Compliance Docs</span>'
        
        sql_block = ""
        if sql:
            sql_block = f'<div class="sql-block"><pre>{sql}</pre></div>'
        
        st.markdown(f"""
        <div class="assistant-message">
            <div style="color: #8B5CF6; font-size: 12px; margin-bottom: 8px;">
                GRIDGUARD AI {source_tags}
            </div>
            <div style="color: white; line-height: 1.6;">{content}</div>
            {sql_block}
        </div>
        """, unsafe_allow_html=True)
        
        # Show dataframe if present
        if 'results' in message and message['results'] is not None:
            st.markdown("**📊 Data Results:**")
            st.dataframe(message['results'], use_container_width=True)

# Chat input (using text_input for SiS compatibility)
col_input, col_btn = st.columns([4, 1])
with col_input:
    user_input_text = st.text_input(
        "Ask a question about grid simulations or compliance...",
        key="chat_input_field",
        label_visibility="collapsed"
    )
with col_btn:
    send_clicked = st.button("Send", key="chat_send_btn", use_container_width=True)

user_input = user_input_text if send_clicked and user_input_text else None

# Handle pending question from suggested buttons
if hasattr(st.session_state, 'pending_question') and st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    with st.spinner("Thinking..."):
        try:
            if st.session_state.chat_mode == 'agent':
                # Use Cortex Agent for combined response
                result = query_cortex_agent(
                    session, 
                    user_input,
                    conversation_history=st.session_state.chat_history[-10:]
                )
                
                if result.get('success'):
                    # Extract SQL if analyst was used
                    sql = None
                    results_df = None
                    for source_type, source_data, _ in result.get('sources', []):
                        if source_type == 'data' and isinstance(source_data, dict):
                            sql = source_data.get('sql')
                            results_df = source_data.get('results')
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': result['response'],
                        'sql': sql,
                        'sources': [s[0] for s in result.get('sources', [])],
                        'results': results_df
                    })
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"I encountered an error: {result.get('error', 'Unknown error')}. Please try rephrasing your question."
                    })
                    
            elif st.session_state.chat_mode == 'analyst':
                # Use Cortex Analyst for SQL generation
                result = query_cortex_analyst(
                    session,
                    user_input,
                    conversation_history=st.session_state.chat_history[-10:]
                )
                
                if result.get('success'):
                    content = result.get('explanation', 'Here are the results:')
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': content,
                        'sql': result.get('sql'),
                        'sources': ['data'],
                        'results': result.get('results')
                    })
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"I couldn't generate a valid query. Error: {result.get('error', 'Unknown')}",
                        'sql': result.get('sql')
                    })
                    
            elif st.session_state.chat_mode == 'search':
                # Use Cortex Search for compliance docs
                results = query_cortex_search(session, user_input, top_k=5)
                
                if results:
                    # Format search results as response
                    response_parts = ["Here's what I found in the compliance documents:\n\n"]
                    for r in results[:3]:
                        reg_code = r.get('REGULATION_CODE', 'N/A')
                        title = r.get('TITLE', 'Untitled')
                        content = r.get('CONTENT', '')[:400]
                        response_parts.append(f"**{reg_code}** - {title}\n{content}...\n\n")
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': ''.join(response_parts),
                        'sources': ['compliance']
                    })
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': "I couldn't find any matching compliance documents. Try different keywords."
                    })
                    
        except Exception as e:
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': f"Sorry, I encountered an error: {str(e)}"
            })
    
    st.experimental_rerun()

# Clear conversation button
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.experimental_rerun()

# Navigation hint
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 14px;">
    👈 Use the <b>sidebar</b> to navigate. Previous: <b>4_Take_Action</b> | Next: <b>7_Scenario_Builder</b>
</div>
""", unsafe_allow_html=True)

