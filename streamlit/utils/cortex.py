"""
cortex.py - Cortex Integration Utilities for GridGuard

Provides helpers for interacting with Cortex Analyst, Search, and Agent services.
"""

import json
from typing import Optional, Dict, Any, List
import streamlit as st

# Configuration
SEMANTIC_MODEL_PATH = "@GRIDGUARD.GRIDGUARD.MODELS_STAGE/semantic_model.yaml"
SEARCH_SERVICE_NAME = "GRIDGUARD.GRIDGUARD.COMPLIANCE_SEARCH_SERVICE"


def query_cortex_analyst(
    session,
    question: str,
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    Query Cortex Analyst with natural language to generate and execute SQL.
    
    Args:
        session: Snowflake session
        question: Natural language question about simulation data
        conversation_history: Optional list of previous messages for multi-turn
    
    Returns:
        Dictionary with 'sql', 'results', 'explanation' keys
    """
    try:
        # Build messages array
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": [{"type": "text", "text": msg.get("content", "")}]
                })
        
        # Add current question
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": question}]
        })
        
        # Build request body
        request_body = {
            "messages": messages,
            "semantic_model_file": SEMANTIC_MODEL_PATH
        }
        
        # Escape for SQL
        request_json = json.dumps(request_body).replace("'", "''")
        
        # Call Cortex Analyst
        response = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                CONCAT(
                    'You are a helpful data analyst. Answer questions about energy grid simulation data. ',
                    'The user asked: {question.replace("'", "''")}. ',
                    'Generate a SQL query to answer this question using these tables: ',
                    'SIMULATION_RESULTS (SCENARIO_NAME, NODE_ID, FAILURE_PROBABILITY, IS_PATIENT_ZERO, CASCADE_ORDER, LOAD_SHED_MW, CUSTOMERS_IMPACTED, REPAIR_COST), ',
                    'GRID_NODES (NODE_ID, NODE_NAME, NODE_TYPE, REGION, CAPACITY_MW). ',
                    'Return ONLY the SQL query, nothing else.'
                )
            ) as SQL_QUERY
        """).collect()
        
        if response and len(response) > 0:
            generated_sql = response[0]['SQL_QUERY'].strip()
            
            # Clean up the SQL (remove markdown code blocks if present)
            if generated_sql.startswith('```'):
                lines = generated_sql.split('\n')
                generated_sql = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            # Execute the generated SQL
            try:
                results = session.sql(generated_sql).to_pandas()
                
                # Generate explanation
                explanation = session.sql(f"""
                    SELECT SNOWFLAKE.CORTEX.COMPLETE(
                        'claude-3-5-sonnet',
                        'Briefly explain these query results in 1-2 sentences for a grid operator: {results.head(5).to_string().replace("'", "''")}'
                    )
                """).collect()[0][0]
                
                return {
                    'success': True,
                    'sql': generated_sql,
                    'results': results,
                    'explanation': explanation,
                    'error': None
                }
            except Exception as sql_error:
                return {
                    'success': False,
                    'sql': generated_sql,
                    'results': None,
                    'explanation': None,
                    'error': f"SQL execution error: {str(sql_error)}"
                }
        
        return {
            'success': False,
            'sql': None,
            'results': None,
            'explanation': None,
            'error': "No response from Cortex"
        }
        
    except Exception as e:
        return {
            'success': False,
            'sql': None,
            'results': None,
            'explanation': None,
            'error': str(e)
        }


def query_cortex_agent(
    session,
    question: str,
    conversation_history: List[Dict] = None,
    scenario_context: str = None
) -> Dict[str, Any]:
    """
    Query Cortex Agent that combines Analyst (SQL) and Search (RAG) capabilities.
    
    The agent can:
    - Answer questions about simulation data using SQL
    - Search compliance documents for regulations
    - Combine both for contextual responses
    
    Args:
        session: Snowflake session
        question: User's natural language question
        conversation_history: Previous messages for multi-turn conversation
        scenario_context: Optional scenario name for context
    
    Returns:
        Dictionary with response, sources, and any generated SQL
    """
    try:
        # Build context from conversation history
        context = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"
        
        # Build system prompt with scenario context
        system_prompt = """You are GridGuard AI, an intelligent assistant for energy grid operators.
You have access to two data sources:
1. SIMULATION_RESULTS - GNN model predictions about cascade failures
2. COMPLIANCE_DOCS - NERC regulations and reporting requirements

When the user asks about:
- Simulation data, failures, Patient Zero, cascade analysis → Query the simulation tables
- Regulations, compliance, reporting forms, NERC requirements → Search compliance documents
- Questions that need both → Combine both sources

Always provide actionable insights for grid operators."""

        if scenario_context:
            system_prompt += f"\n\nCurrent scenario context: {scenario_context}"
        
        # Determine if question is about data or compliance
        question_lower = question.lower()
        is_compliance = any(word in question_lower for word in 
            ['regulation', 'compliance', 'nerc', 'form', 'report', 'filing', 'requirement'])
        is_data = any(word in question_lower for word in 
            ['failure', 'cascade', 'patient zero', 'node', 'load', 'cost', 'customer', 'scenario'])
        
        responses = []
        
        # Query compliance documents if relevant
        if is_compliance or not is_data:
            search_results = query_cortex_search(session, question, top_k=3)
            if search_results:
                compliance_context = "\n".join([
                    f"- {r.get('REGULATION_CODE', 'N/A')}: {r.get('CONTENT', '')[:300]}"
                    for r in search_results[:3]
                ])
                responses.append(("compliance", compliance_context, search_results))
        
        # Query simulation data if relevant
        if is_data or not is_compliance:
            analyst_result = query_cortex_analyst(session, question)
            if analyst_result.get('success'):
                responses.append(("data", analyst_result, None))
        
        # Generate unified response
        combined_context = f"Previous conversation:\n{context}\n\n" if context else ""
        
        for source_type, result, _ in responses:
            if source_type == "compliance":
                combined_context += f"Relevant compliance documents:\n{result}\n\n"
            elif source_type == "data" and isinstance(result, dict):
                combined_context += f"Query results:\n{result.get('results', '').head(10).to_string() if result.get('results') is not None else 'No results'}\n\n"
        
        # Generate final response
        final_response = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                '{system_prompt.replace("'", "''")}
                
                User question: {question.replace("'", "''")}
                
                {combined_context.replace("'", "''")}
                
                Provide a helpful, concise response that directly answers the user\\'s question.
                If relevant, mention specific regulations, node names, or metrics.
                Keep the response under 200 words.'
            )
        """).collect()[0][0]
        
        return {
            'success': True,
            'response': final_response,
            'sources': responses,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'response': None,
            'sources': [],
            'error': str(e)
        }


def query_cortex_search(
    session,
    query: str,
    service_name: str = "COMPLIANCE_SEARCH_SERVICE",
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Query the Cortex Search service for compliance documents.
    
    Args:
        session: Snowflake session
        query: Natural language search query
        service_name: Name of the Cortex Search service
        top_k: Number of results to return
    
    Returns:
        List of matching documents
    """
    try:
        # Execute search query
        results = session.sql(f"""
            SELECT * FROM TABLE(
                {service_name}!SEARCH(
                    QUERY => '{query.replace("'", "''")}',
                    COLUMNS => ['REGULATION_CODE', 'TITLE', 'CONTENT'],
                    TOP_K => {top_k}
                )
            )
        """).to_pandas()
        
        return results.to_dict('records')
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results as markdown for display.
    
    Args:
        results: List of search result dictionaries
    
    Returns:
        Formatted markdown string
    """
    if not results:
        return "No relevant compliance documents found."
    
    output = []
    for i, result in enumerate(results, 1):
        output.append(f"""
**{i}. {result.get('TITLE', 'Untitled')}**

*Regulation: {result.get('REGULATION_CODE', 'N/A')}*

{result.get('CONTENT', '')[:500]}...

---
""")
    
    return "\n".join(output)


def get_compliance_context(session, scenario_name: str) -> str:
    """
    Get relevant compliance context for a given scenario.
    
    Args:
        session: Snowflake session
        scenario_name: Name of the simulation scenario
    
    Returns:
        Formatted compliance context string
    """
    # Get scenario impact summary
    impact = session.sql(f"""
        SELECT 
            SUM(LOAD_SHED_MW) as TOTAL_LOAD_SHED,
            SUM(CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS,
            SUM(REPAIR_COST) as TOTAL_COST,
            COUNT(*) as NODES_AFFECTED
        FROM SIMULATION_RESULTS
        WHERE SCENARIO_NAME = '{scenario_name}'
        AND CASCADE_ORDER IS NOT NULL
    """).to_pandas()
    
    if len(impact) == 0:
        return "No simulation results available for this scenario."
    
    row = impact.iloc[0]
    load_shed = row['TOTAL_LOAD_SHED'] or 0
    customers = row['TOTAL_CUSTOMERS'] or 0
    
    context = f"""
Based on the {scenario_name} simulation:
- Total load shed: {load_shed:,.0f} MW
- Customers impacted: {customers:,}
- Nodes in cascade: {row['NODES_AFFECTED'] or 0}
- Estimated repair cost: ${row['TOTAL_COST'] or 0:,.0f}
"""
    
    # Determine reporting requirements based on thresholds
    requirements = []
    
    if load_shed >= 100:
        requirements.append("- **DOE Form OE-417** required (load shedding > 100 MW)")
    
    if load_shed >= 300:
        requirements.append("- **Regional Entity notification** required within 1 hour (voltage collapse > 300 MW)")
    
    if customers >= 50000:
        requirements.append("- **Public notification** recommended (significant customer impact)")
    
    if requirements:
        context += "\n**Regulatory Reporting Requirements:**\n"
        context += "\n".join(requirements)
    
    return context


def generate_action_recommendations(session, scenario_name: str) -> List[str]:
    """
    Generate recommended actions based on simulation results.
    
    Args:
        session: Snowflake session
        scenario_name: Name of the simulation scenario
    
    Returns:
        List of recommended actions
    """
    # Get patient zero and high-risk nodes
    high_risk = session.sql(f"""
        SELECT sr.NODE_ID, gn.NODE_NAME, gn.REGION, 
               sr.FAILURE_PROBABILITY, sr.IS_PATIENT_ZERO
        FROM SIMULATION_RESULTS sr
        JOIN GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
        WHERE sr.SCENARIO_NAME = '{scenario_name}'
        AND (sr.IS_PATIENT_ZERO = TRUE OR sr.FAILURE_PROBABILITY > 0.7)
        ORDER BY sr.FAILURE_PROBABILITY DESC
        LIMIT 5
    """).to_pandas()
    
    recommendations = []
    
    # Patient Zero recommendations
    patient_zero = high_risk[high_risk['IS_PATIENT_ZERO'] == True]
    if len(patient_zero) > 0:
        pz = patient_zero.iloc[0]
        recommendations.append(
            f"**Priority 1: Reinforce {pz['NODE_NAME']}** - Identified as cascade origin point. "
            f"Consider installing redundant protection systems and backup power supply."
        )
    
    # Regional recommendations
    if len(high_risk) > 0:
        regions = high_risk['REGION'].unique()
        for region in regions:
            recommendations.append(
                f"**Conduct {region} region assessment** - Multiple high-risk nodes identified. "
                f"Review transmission line redundancy and load balancing capabilities."
            )
    
    # General recommendations
    recommendations.extend([
        "**Update emergency response procedures** - Ensure cascade failure protocols reflect simulation findings.",
        "**Schedule infrastructure review** - Coordinate with operations team for physical inspection of vulnerable nodes.",
        "**File required regulatory reports** - Complete DOE Form OE-417 and Regional Entity notifications as applicable."
    ])
    
    return recommendations

