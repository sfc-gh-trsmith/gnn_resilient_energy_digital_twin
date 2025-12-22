"""
data_loader.py - Parallel Query Utility for GridGuard

Provides efficient parallel query execution for Streamlit pages.
Uses ThreadPoolExecutor to run multiple independent Snowflake queries
simultaneously, reducing page load times.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable, Any
import streamlit as st


def run_queries_parallel(
    session,
    queries: Dict[str, str],
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Execute multiple SQL queries in parallel.
    
    Args:
        session: Snowflake session object
        queries: Dictionary mapping result names to SQL queries
        max_workers: Maximum number of concurrent queries
    
    Returns:
        Dictionary mapping result names to pandas DataFrames
    
    Example:
        results = run_queries_parallel(session, {
            'nodes': 'SELECT * FROM GRID_NODES',
            'edges': 'SELECT * FROM GRID_EDGES',
            'stats': 'SELECT COUNT(*) AS cnt FROM SIMULATION_RESULTS'
        })
        nodes_df = results['nodes']
    """
    results = {}
    
    def execute_query(name: str, sql: str):
        """Execute a single query and return the result."""
        try:
            df = session.sql(sql).to_pandas()
            return name, df, None
        except Exception as e:
            return name, None, str(e)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all queries
        futures = {
            executor.submit(execute_query, name, sql): name
            for name, sql in queries.items()
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            name, df, error = future.result()
            if error:
                st.error(f"Query '{name}' failed: {error}")
                results[name] = None
            else:
                results[name] = df
    
    return results


def get_scenario_summary(session):
    """Get summary statistics for all scenarios."""
    return session.sql("""
        SELECT * FROM VW_SCENARIO_IMPACT
        ORDER BY SCENARIO_NAME
    """).to_pandas()


def get_cascade_analysis(session, scenario_name: str):
    """Get cascade analysis for a specific scenario."""
    return session.sql(f"""
        SELECT * FROM VW_CASCADE_ANALYSIS
        WHERE SCENARIO_NAME = '{scenario_name}'
        ORDER BY CASCADE_ORDER NULLS LAST
    """).to_pandas()


def get_grid_topology(session):
    """Load grid nodes and edges for visualization."""
    queries = {
        'nodes': """
            SELECT NODE_ID, NODE_NAME, NODE_TYPE, LAT, LON, REGION, 
                   CAPACITY_MW, CRITICALITY_SCORE
            FROM GRID_NODES
        """,
        'edges': """
            SELECT EDGE_ID, SRC_NODE, DST_NODE, EDGE_TYPE, CAPACITY_MW
            FROM GRID_EDGES
        """
    }
    return run_queries_parallel(session, queries)


def get_table_row_counts(session):
    """Get row counts for all main tables."""
    return session.sql("""
        SELECT 'GRID_NODES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM GRID_NODES
        UNION ALL SELECT 'GRID_EDGES', COUNT(*) FROM GRID_EDGES
        UNION ALL SELECT 'HISTORICAL_TELEMETRY', COUNT(*) FROM HISTORICAL_TELEMETRY
        UNION ALL SELECT 'COMPLIANCE_DOCS', COUNT(*) FROM COMPLIANCE_DOCS
        UNION ALL SELECT 'SIMULATION_RESULTS', COUNT(*) FROM SIMULATION_RESULTS
        ORDER BY TABLE_NAME
    """).to_pandas()


# =============================================================================
# DIRECTOR PERSONA - EXECUTIVE DASHBOARD QUERIES
# =============================================================================

def get_executive_summary(session, scenario_name: str = 'WINTER_STORM_2021'):
    """
    Get executive summary KPIs for dashboard cards.
    
    Returns:
        DataFrame with columns: TOTAL_EXPOSURE, CRITICAL_NODES, 
        TOTAL_CUSTOMERS_AT_RISK, TOTAL_LOAD_SHED, NODES_IN_CASCADE
    """
    return session.sql(f"""
        SELECT 
            ROUND(SUM(REPAIR_COST), 0) as TOTAL_EXPOSURE,
            COUNT(CASE WHEN RISK_SCORE > 0.7 THEN 1 END) as CRITICAL_NODES,
            SUM(CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS_AT_RISK,
            ROUND(SUM(LOAD_SHED_MW), 0) as TOTAL_LOAD_SHED,
            COUNT(CASE WHEN CASCADE_ORDER IS NOT NULL THEN 1 END) as NODES_IN_CASCADE,
            COUNT(*) as TOTAL_NODES
        FROM SIMULATION_RESULTS
        WHERE SCENARIO_NAME = '{scenario_name}'
    """).to_pandas()


def get_scenario_comparison(session):
    """
    Get comparison metrics across all scenarios for executive view.
    
    Returns:
        DataFrame with scenario-level aggregates for comparison charts.
    """
    return session.sql("""
        SELECT 
            SCENARIO_NAME,
            COUNT(CASE WHEN CASCADE_ORDER IS NOT NULL THEN 1 END) as FAILURES,
            ROUND(SUM(LOAD_SHED_MW), 0) as TOTAL_LOAD_SHED_MW,
            SUM(CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS,
            ROUND(SUM(REPAIR_COST), 0) as TOTAL_REPAIR_COST,
            ROUND(AVG(FAILURE_PROBABILITY), 4) as AVG_FAILURE_PROB,
            MAX(CASE WHEN IS_PATIENT_ZERO THEN NODE_ID END) as PATIENT_ZERO_ID
        FROM SIMULATION_RESULTS
        GROUP BY SCENARIO_NAME
        ORDER BY TOTAL_REPAIR_COST DESC
    """).to_pandas()


def get_investment_priorities(session, scenario_name: str = 'WINTER_STORM_2021'):
    """
    Get nodes ranked by investment priority (risk vs cost).
    
    Returns priority matrix data with reinforcement cost estimates and impact metrics.
    IMPACT_IF_FAILS is estimated for ALL nodes (not just failed ones) based on
    capacity, criticality, and failure probability to support investment planning.
    """
    return session.sql(f"""
        SELECT 
            n.NODE_ID, 
            n.NODE_NAME, 
            n.REGION, 
            n.NODE_TYPE,
            n.CAPACITY_MW,
            n.CRITICALITY_SCORE,
            sr.FAILURE_PROBABILITY, 
            sr.RISK_SCORE,
            -- Estimated impact if node fails (calculate for ALL nodes, not just failed ones)
            -- Uses actual repair cost if node failed, otherwise estimates based on capacity
            CAST(CASE 
                WHEN sr.REPAIR_COST > 0 THEN sr.REPAIR_COST
                ELSE ROUND(n.CAPACITY_MW * 10000 * (0.5 + n.CRITICALITY_SCORE) * sr.FAILURE_PROBABILITY, 0)
            END AS FLOAT) as IMPACT_IF_FAILS,
            sr.LOAD_SHED_MW,
            sr.CUSTOMERS_IMPACTED,
            sr.CASCADE_ORDER,
            sr.IS_PATIENT_ZERO,
            -- Estimated reinforcement cost (simplified: based on capacity and criticality)
            CAST(ROUND(n.CAPACITY_MW * 10000 * (1 + n.CRITICALITY_SCORE), 0) AS FLOAT) as EST_REINFORCEMENT_COST,
            -- Node degree (network centrality proxy)
            (SELECT COUNT(*) FROM GRID_EDGES e 
             WHERE e.SRC_NODE = n.NODE_ID OR e.DST_NODE = n.NODE_ID) as NODE_DEGREE,
            -- Priority score: high impact + high probability / cost
            CAST(ROUND(
                (CASE 
                    WHEN sr.REPAIR_COST > 0 THEN sr.REPAIR_COST
                    ELSE n.CAPACITY_MW * 10000 * (0.5 + n.CRITICALITY_SCORE) * sr.FAILURE_PROBABILITY
                END * sr.FAILURE_PROBABILITY) / 
                NULLIF(n.CAPACITY_MW * 10000 * (1 + n.CRITICALITY_SCORE), 0) * 1000, 
                4
            ) AS FLOAT) as PRIORITY_SCORE
        FROM GRID_NODES n
        JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
        WHERE sr.SCENARIO_NAME = '{scenario_name}'
        ORDER BY PRIORITY_SCORE DESC NULLS LAST
    """).to_pandas()


def get_regional_summary(session, scenario_name: str = 'WINTER_STORM_2021'):
    """
    Get per-region aggregated metrics for regional analysis.
    
    Returns summary statistics grouped by region.
    """
    return session.sql(f"""
        SELECT 
            n.REGION,
            COUNT(*) as NODE_COUNT,
            ROUND(SUM(n.CAPACITY_MW), 0) as TOTAL_CAPACITY_MW,
            ROUND(AVG(n.CRITICALITY_SCORE), 3) as AVG_CRITICALITY,
            ROUND(AVG(sr.FAILURE_PROBABILITY), 4) as AVG_FAILURE_PROB,
            COUNT(CASE WHEN sr.RISK_SCORE > 0.7 THEN 1 END) as HIGH_RISK_NODES,
            COUNT(CASE WHEN sr.CASCADE_ORDER IS NOT NULL THEN 1 END) as NODES_FAILED,
            ROUND(SUM(sr.REPAIR_COST), 0) as TOTAL_EXPOSURE,
            SUM(sr.CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS_AT_RISK,
            ROUND(SUM(sr.LOAD_SHED_MW), 0) as TOTAL_LOAD_SHED_MW
        FROM GRID_NODES n
        JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
        WHERE sr.SCENARIO_NAME = '{scenario_name}'
        GROUP BY n.REGION
        ORDER BY TOTAL_EXPOSURE DESC
    """).to_pandas()


def get_regional_failures_by_scenario(session):
    """
    Get failure counts by region across all scenarios.
    
    Returns data for stacked bar chart of regional failures.
    """
    return session.sql("""
        SELECT 
            n.REGION,
            sr.SCENARIO_NAME,
            COUNT(CASE WHEN sr.CASCADE_ORDER IS NOT NULL THEN 1 END) as FAILURE_COUNT,
            ROUND(SUM(sr.LOAD_SHED_MW), 0) as LOAD_SHED_MW,
            ROUND(SUM(sr.REPAIR_COST), 0) as REPAIR_COST
        FROM GRID_NODES n
        JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
        GROUP BY n.REGION, sr.SCENARIO_NAME
        ORDER BY n.REGION, sr.SCENARIO_NAME
    """).to_pandas()


def get_cross_region_flows(session):
    """
    Get edge connections between regions for Sankey diagram.
    
    Returns aggregated transmission capacity between region pairs.
    """
    return session.sql("""
        SELECT 
            n1.REGION as SOURCE_REGION,
            n2.REGION as TARGET_REGION,
            COUNT(*) as EDGE_COUNT,
            ROUND(SUM(e.CAPACITY_MW), 0) as TOTAL_CAPACITY_MW
        FROM GRID_EDGES e
        JOIN GRID_NODES n1 ON e.SRC_NODE = n1.NODE_ID
        JOIN GRID_NODES n2 ON e.DST_NODE = n2.NODE_ID
        WHERE n1.REGION != n2.REGION
        GROUP BY n1.REGION, n2.REGION
        ORDER BY TOTAL_CAPACITY_MW DESC
    """).to_pandas()


def get_regional_investment_recommendations(session, scenario_name: str = 'WINTER_STORM_2021'):
    """
    Get investment recommendations aggregated by region.
    
    Returns ROI estimates per region based on risk and reinforcement costs.
    """
    return session.sql(f"""
        WITH node_priorities AS (
            SELECT 
                n.REGION,
                n.NODE_ID,
                n.CAPACITY_MW,
                n.CRITICALITY_SCORE,
                sr.RISK_SCORE,
                sr.REPAIR_COST,
                sr.FAILURE_PROBABILITY,
                -- Nodes needing upgrade: high risk score
                CASE WHEN sr.RISK_SCORE > 0.5 THEN 1 ELSE 0 END as NEEDS_UPGRADE,
                -- Estimated reinforcement cost
                n.CAPACITY_MW * 10000 * (1 + n.CRITICALITY_SCORE) as EST_COST,
                -- Expected benefit (probability * avoided cost)
                sr.REPAIR_COST * sr.FAILURE_PROBABILITY as EXPECTED_BENEFIT
            FROM GRID_NODES n
            JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
            WHERE sr.SCENARIO_NAME = '{scenario_name}'
        )
        SELECT 
            REGION,
            COUNT(*) as TOTAL_NODES,
            SUM(NEEDS_UPGRADE) as NODES_NEEDING_UPGRADE,
            ROUND(SUM(CASE WHEN NEEDS_UPGRADE = 1 THEN EST_COST ELSE 0 END), 0) as EST_INVESTMENT_COST,
            ROUND(SUM(CASE WHEN NEEDS_UPGRADE = 1 THEN EXPECTED_BENEFIT ELSE 0 END), 0) as EXPECTED_BENEFIT,
            ROUND(
                SUM(CASE WHEN NEEDS_UPGRADE = 1 THEN EXPECTED_BENEFIT ELSE 0 END) /
                NULLIF(SUM(CASE WHEN NEEDS_UPGRADE = 1 THEN EST_COST ELSE 0 END), 0) * 100,
                1
            ) as ROI_PERCENT
        FROM node_priorities
        GROUP BY REGION
        ORDER BY EXPECTED_BENEFIT DESC
    """).to_pandas()


def get_top_priority_nodes(session, scenario_name: str = 'WINTER_STORM_2021', limit: int = 10):
    """
    Get top N priority nodes for executive action table.
    """
    return session.sql(f"""
        SELECT 
            n.NODE_NAME,
            n.REGION,
            n.NODE_TYPE,
            ROUND(sr.RISK_SCORE, 4) as RISK_SCORE,
            ROUND(sr.FAILURE_PROBABILITY, 4) as FAILURE_PROB,
            ROUND(sr.REPAIR_COST, 0) as POTENTIAL_COST,
            sr.IS_PATIENT_ZERO,
            sr.CASCADE_ORDER,
            CASE 
                WHEN sr.IS_PATIENT_ZERO THEN 'CRITICAL: Reinforce immediately'
                WHEN sr.RISK_SCORE > 0.8 THEN 'HIGH: Schedule reinforcement'
                WHEN sr.RISK_SCORE > 0.5 THEN 'MEDIUM: Plan for next budget cycle'
                ELSE 'LOW: Monitor'
            END as RECOMMENDED_ACTION
        FROM GRID_NODES n
        JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID
        WHERE sr.SCENARIO_NAME = '{scenario_name}'
        ORDER BY sr.RISK_SCORE DESC
        LIMIT {limit}
    """).to_pandas()


def get_nodes_by_region(session, region: str):
    """
    Get all nodes for a specific region with simulation results.
    """
    return session.sql(f"""
        SELECT 
            n.*,
            sr.FAILURE_PROBABILITY,
            sr.RISK_SCORE,
            sr.CASCADE_ORDER,
            sr.IS_PATIENT_ZERO,
            sr.REPAIR_COST,
            sr.LOAD_SHED_MW
        FROM GRID_NODES n
        LEFT JOIN SIMULATION_RESULTS sr ON n.NODE_ID = sr.NODE_ID 
            AND sr.SCENARIO_NAME = 'WINTER_STORM_2021'
        WHERE n.REGION = '{region}'
        ORDER BY sr.RISK_SCORE DESC NULLS LAST
    """).to_pandas()


def get_edges_by_region(session, region: str):
    """
    Get all edges where both nodes are in the specified region.
    """
    return session.sql(f"""
        SELECT e.*
        FROM GRID_EDGES e
        JOIN GRID_NODES n1 ON e.SRC_NODE = n1.NODE_ID
        JOIN GRID_NODES n2 ON e.DST_NODE = n2.NODE_ID
        WHERE n1.REGION = '{region}' AND n2.REGION = '{region}'
    """).to_pandas()

