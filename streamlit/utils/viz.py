"""
viz.py - Visualization Utilities for GridGuard

Provides Plotly + NetworkX based network graph rendering.
Note: PyVis is NOT used due to Snowflake CSP blocking external JS CDNs.
"""

import plotly.graph_objects as go
import networkx as nx
import pandas as pd
from typing import Dict, Optional, List


# Snowflake brand colors
COLORS = {
    'snowflake_blue': '#29B5E8',
    'snowflake_dark': '#1B2A41',
    'active': '#22C55E',      # Green
    'warning': '#EAB308',     # Yellow
    'failed': '#EF4444',      # Red
    'patient_zero': '#8B5CF6', # Purple
    'edge': '#94A3B8',        # Gray
    'edge_highlight': '#F97316'  # Orange
}


def create_network_graph(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    simulation_df: Optional[pd.DataFrame] = None,
    highlight_patient_zero: bool = True,
    title: str = "Grid Network Topology"
) -> go.Figure:
    """
    Create an interactive network graph using Plotly + NetworkX.
    
    Args:
        nodes_df: DataFrame with NODE_ID, NODE_NAME, NODE_TYPE, LAT, LON
        edges_df: DataFrame with SRC_NODE, DST_NODE
        simulation_df: Optional DataFrame with simulation results
        highlight_patient_zero: Whether to highlight Patient Zero node
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    # Build NetworkX graph
    G = nx.Graph()
    
    # Add nodes
    for _, row in nodes_df.iterrows():
        G.add_node(row['NODE_ID'], **row.to_dict())
    
    # Add edges
    for _, row in edges_df.iterrows():
        if row['SRC_NODE'] in G.nodes and row['DST_NODE'] in G.nodes:
            G.add_edge(row['SRC_NODE'], row['DST_NODE'])
    
    # Calculate layout using spring layout
    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)
    
    # Prepare node data
    node_x = []
    node_y = []
    node_colors = []
    node_sizes = []
    node_texts = []
    node_hovers = []
    
    # Create simulation lookup if available
    sim_lookup = {}
    if simulation_df is not None and len(simulation_df) > 0:
        for _, row in simulation_df.iterrows():
            sim_lookup[row['NODE_ID']] = row
    
    for node_id in G.nodes():
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        
        node_data = G.nodes[node_id]
        sim_data = sim_lookup.get(node_id, {})
        
        # Determine color based on status
        is_patient_zero = sim_data.get('IS_PATIENT_ZERO', False) if isinstance(sim_data, dict) else (sim_data.get('IS_PATIENT_ZERO') if len(sim_data) > 0 else False)
        cascade_order = sim_data.get('CASCADE_ORDER') if isinstance(sim_data, dict) else None
        
        if is_patient_zero and highlight_patient_zero:
            color = COLORS['patient_zero']
            size = 25
        elif cascade_order is not None:
            color = COLORS['failed']
            size = 18
        elif isinstance(sim_data, dict) and sim_data.get('FAILURE_PROBABILITY', 0) > 0.5:
            color = COLORS['warning']
            size = 15
        else:
            color = COLORS['active']
            size = 12
        
        node_colors.append(color)
        node_sizes.append(size)
        node_texts.append(node_data.get('NODE_NAME', node_id)[:15])
        
        # Hover text
        hover = f"<b>{node_data.get('NODE_NAME', node_id)}</b><br>"
        hover += f"Type: {node_data.get('NODE_TYPE', 'Unknown')}<br>"
        hover += f"Region: {node_data.get('REGION', 'Unknown')}<br>"
        hover += f"Capacity: {node_data.get('CAPACITY_MW', 0):.0f} MW<br>"
        
        if isinstance(sim_data, dict) and sim_data:
            hover += f"<br><b>Simulation Results:</b><br>"
            hover += f"Failure Prob: {sim_data.get('FAILURE_PROBABILITY', 0):.2%}<br>"
            if is_patient_zero:
                hover += "<b>PATIENT ZERO</b><br>"
            if cascade_order:
                hover += f"Cascade Order: {cascade_order}<br>"
        
        node_hovers.append(hover)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(width=1, color=COLORS['edge']),
        hoverinfo='none',
        name='Transmission Lines'
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=1, color='white')
        ),
        text=node_texts,
        textposition='top center',
        textfont=dict(size=8, color='white'),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=node_hovers,
        name='Grid Nodes'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color='white')
        ),
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=50, b=20),
        height=500
    )
    
    # Add legend annotation
    legend_items = [
        ('Active', COLORS['active']),
        ('Warning', COLORS['warning']),
        ('Failed', COLORS['failed']),
        ('Patient Zero', COLORS['patient_zero'])
    ]
    
    for i, (label, color) in enumerate(legend_items):
        fig.add_annotation(
            x=1.02,
            y=1 - i * 0.08,
            xref='paper',
            yref='paper',
            text=f'<span style="color:{color}">●</span> {label}',
            showarrow=False,
            font=dict(size=10, color='white'),
            align='left'
        )
    
    return fig


def create_cascade_flow_diagram(
    cascade_df: pd.DataFrame,
    value_col: str = 'LOAD_SHED_MW'
) -> go.Figure:
    """
    Create a Sankey diagram showing cascade failure propagation by infrastructure type.
    
    Groups nodes by NODE_TYPE (Generator, Substation, etc.) for a clean, readable
    visualization showing how failures propagate through different asset types.
    
    Args:
        cascade_df: DataFrame with CASCADE_ORDER, NODE_NAME, NODE_TYPE, and impact metrics
        value_col: Column to use for link values ('LOAD_SHED_MW', 'CUSTOMERS_IMPACTED', 'REPAIR_COST')
    
    Returns:
        Plotly Figure object with Sankey diagram
    """
    # Handle empty or invalid data
    if cascade_df is None or len(cascade_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No cascade data available",
            showarrow=False,
            font=dict(size=14, color='white')
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    # Filter to nodes with valid CASCADE_ORDER
    cascade_nodes = cascade_df[cascade_df['CASCADE_ORDER'].notna()].copy()
    cascade_nodes = cascade_nodes.sort_values('CASCADE_ORDER')
    
    if len(cascade_nodes) < 2:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Insufficient cascade data (need at least 2 nodes)",
            showarrow=False,
            font=dict(size=14, color='white')
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    # Ensure required columns exist
    if value_col not in cascade_nodes.columns:
        value_col = 'LOAD_SHED_MW'
    cascade_nodes[value_col] = cascade_nodes[value_col].fillna(0)
    
    if 'NODE_TYPE' not in cascade_nodes.columns:
        cascade_nodes['NODE_TYPE'] = 'Unknown'
    
    if 'CUSTOMERS_IMPACTED' not in cascade_nodes.columns:
        cascade_nodes['CUSTOMERS_IMPACTED'] = 0
    cascade_nodes['CUSTOMERS_IMPACTED'] = cascade_nodes['CUSTOMERS_IMPACTED'].fillna(0)
    
    # Identify Patient Zero
    if 'IS_PATIENT_ZERO' in cascade_nodes.columns:
        patient_zero_mask = cascade_nodes['IS_PATIENT_ZERO'] == True
    else:
        # Assume first cascade order is patient zero
        min_order = cascade_nodes['CASCADE_ORDER'].min()
        patient_zero_mask = cascade_nodes['CASCADE_ORDER'] == min_order
    
    patient_zero_df = cascade_nodes[patient_zero_mask]
    other_nodes_df = cascade_nodes[~patient_zero_mask]
    
    # Get Patient Zero info
    if len(patient_zero_df) > 0:
        pz = patient_zero_df.iloc[0]
        pz_name = pz.get('NODE_NAME', pz.get('NODE_ID', 'Unknown'))[:25]
        pz_type = pz.get('NODE_TYPE', 'Unknown')
        pz_value = patient_zero_df[value_col].sum()
        pz_customers = patient_zero_df['CUSTOMERS_IMPACTED'].sum()
    else:
        pz_name = 'Unknown'
        pz_type = 'Unknown'
        pz_value = 0
        pz_customers = 0
    
    # Group other nodes by NODE_TYPE
    type_groups = other_nodes_df.groupby('NODE_TYPE').agg({
        value_col: 'sum',
        'CUSTOMERS_IMPACTED': 'sum',
        'CASCADE_ORDER': 'mean',  # Average cascade order for sorting
        'NODE_ID': 'count',  # Count of nodes
        'NODE_NAME': lambda x: list(x)  # List of node names
    }).reset_index()
    
    type_groups.columns = ['node_type', 'value', 'customers', 'avg_order', 'count', 'node_names']
    
    # Sort by average cascade order (which type fails first)
    type_groups = type_groups.sort_values('avg_order')
    
    # Format type labels for display
    type_display_names = {
        'GENERATOR': 'Generators',
        'SUBSTATION': 'Substations',
        'TRANSMISSION_HUB': 'Trans. Hubs',
        'LOAD_CENTER': 'Load Centers',
        'Unknown': 'Other'
    }
    
    # Build Sankey nodes
    # Node 0: Patient Zero
    # Nodes 1+: Each NODE_TYPE group
    node_labels = []
    node_colors = []
    node_customdata = []
    
    # Patient Zero node
    node_labels.append(f"Patient Zero<br>({pz_name})")
    node_colors.append(COLORS['patient_zero'])
    node_customdata.append(f"Type: {pz_type}<br>Load Shed: {pz_value:,.0f} MW<br>Customers: {int(pz_customers):,}")
    
    # Type group nodes
    for _, row in type_groups.iterrows():
        type_name = type_display_names.get(row['node_type'], row['node_type'])
        count = int(row['count'])
        node_labels.append(f"{type_name}<br>({count} node{'s' if count > 1 else ''})")
        node_colors.append(COLORS['failed'])
        
        # Build hover info with node names
        names_list = row['node_names'][:5]  # Show first 5
        names_str = '<br>'.join([f"• {n[:30]}" for n in names_list])
        if len(row['node_names']) > 5:
            names_str += f"<br>...and {len(row['node_names']) - 5} more"
        
        node_customdata.append(
            f"Load Shed: {row['value']:,.0f} MW<br>"
            f"Customers: {int(row['customers']):,}<br>"
            f"<br>Affected nodes:<br>{names_str}"
        )
    
    # Build links from Patient Zero to each type
    sources = []
    targets = []
    values = []
    link_colors = []
    
    for i, (_, row) in enumerate(type_groups.iterrows()):
        sources.append(0)  # From Patient Zero
        targets.append(i + 1)  # To this type group
        values.append(max(row['value'], 1))  # Minimum 1 for visibility
        link_colors.append('rgba(139, 92, 246, 0.4)')  # Purple with transparency
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=30,
            thickness=40,
            line=dict(color='rgba(255,255,255,0.3)', width=1),
            label=node_labels,
            color=node_colors,
            customdata=node_customdata,
            hovertemplate='<b>%{label}</b><br>%{customdata}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate=(
                '<b>Cascade Impact</b><br>'
                'Load Shed: %{value:,.0f} MW<br>'
                '<extra></extra>'
            )
        )
    )])
    
    # Calculate totals for subtitle
    total_nodes = len(cascade_nodes)
    total_impact = cascade_nodes[value_col].sum()
    total_customers = cascade_nodes['CUSTOMERS_IMPACTED'].sum()
    num_types = len(type_groups) + 1  # +1 for patient zero type
    
    fig.update_layout(
        title=dict(
            text=(
                f'Cascade Flow by Infrastructure Type<br>'
                f'<sup style="color:#94A3B8">{total_nodes} nodes affected • '
                f'{num_types} asset types • '
                f'Total Load Shed: {total_impact:,.0f} MW • '
                f'Customers: {int(total_customers):,}</sup>'
            ),
            font=dict(size=16, color='white'),
            x=0.5,
            xanchor='center'
        ),
        font=dict(size=12, color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=40, r=40, t=100, b=40)
    )
    
    return fig


def create_animated_cascade_graph(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    simulation_df: pd.DataFrame,
    current_step: int = None,
    title: str = "Cascade Propagation"
) -> go.Figure:
    """
    Create a network graph showing cascade propagation up to a specific step.
    Used for animation of cascade spread.
    
    Args:
        nodes_df: DataFrame with node information
        edges_df: DataFrame with edge information
        simulation_df: DataFrame with simulation results including CASCADE_ORDER
        current_step: Show cascade up to this step (None = show all)
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    # Build NetworkX graph
    G = nx.Graph()
    
    for _, row in nodes_df.iterrows():
        G.add_node(row['NODE_ID'], **row.to_dict())
    
    for _, row in edges_df.iterrows():
        if row['SRC_NODE'] in G.nodes and row['DST_NODE'] in G.nodes:
            G.add_edge(row['SRC_NODE'], row['DST_NODE'])
    
    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)
    
    # Create simulation lookup
    sim_lookup = {}
    if simulation_df is not None and len(simulation_df) > 0:
        for _, row in simulation_df.iterrows():
            sim_lookup[row['NODE_ID']] = row
    
    # Prepare node data
    node_x, node_y, node_colors, node_sizes = [], [], [], []
    
    for node_id in G.nodes():
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        
        sim_data = sim_lookup.get(node_id, {})
        is_patient_zero = sim_data.get('IS_PATIENT_ZERO', False) if isinstance(sim_data, dict) else False
        cascade_order = sim_data.get('CASCADE_ORDER') if isinstance(sim_data, dict) else None
        
        # Determine visibility based on current step
        if current_step is not None:
            if is_patient_zero and current_step >= 1:
                color = COLORS['patient_zero']
                size = 30
            elif cascade_order is not None and cascade_order <= current_step:
                color = COLORS['failed']
                size = 22
            elif cascade_order is not None and cascade_order == current_step + 1:
                # Next to fail - show as warning
                color = COLORS['warning']
                size = 18
            else:
                color = COLORS['active']
                size = 12
        else:
            # Show all states
            if is_patient_zero:
                color = COLORS['patient_zero']
                size = 25
            elif cascade_order is not None:
                color = COLORS['failed']
                size = 18
            else:
                color = COLORS['active']
                size = 12
        
        node_colors.append(color)
        node_sizes.append(size)
    
    # Create edge traces with highlighting for cascade paths
    edge_traces = []
    
    # Get cascade nodes for this step
    cascade_nodes = set()
    if simulation_df is not None:
        for _, row in simulation_df.iterrows():
            order = row.get('CASCADE_ORDER')
            if order is not None and (current_step is None or order <= current_step):
                cascade_nodes.add(row['NODE_ID'])
    
    # Regular edges
    edge_x, edge_y = [], []
    cascade_edge_x, cascade_edge_y = [], []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        if edge[0] in cascade_nodes and edge[1] in cascade_nodes:
            cascade_edge_x.extend([x0, x1, None])
            cascade_edge_y.extend([y0, y1, None])
        else:
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    
    # Create figure
    fig = go.Figure()
    
    # Add regular edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color=COLORS['edge']),
        hoverinfo='none',
        name='Transmission Lines'
    ))
    
    # Add cascade path edges
    if cascade_edge_x:
        fig.add_trace(go.Scatter(
            x=cascade_edge_x, y=cascade_edge_y,
            mode='lines',
            line=dict(width=3, color=COLORS['edge_highlight']),
            hoverinfo='none',
            name='Cascade Path'
        ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        hoverinfo='none',
        name='Grid Nodes'
    ))
    
    # Update layout
    step_text = f" (Step {current_step})" if current_step else ""
    fig.update_layout(
        title=dict(
            text=f"{title}{step_text}",
            font=dict(size=18, color='white')
        ),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=50, b=20),
        height=450
    )
    
    return fig


def create_counterfactual_chart(
    actual_impact: Dict,
    prevented_impact: Dict
) -> go.Figure:
    """
    Create a comparison chart showing actual vs prevented impact.
    
    Args:
        actual_impact: Dict with 'load_shed', 'customers', 'cost'
        prevented_impact: Dict with 'load_shed', 'customers', 'cost'
    
    Returns:
        Plotly Figure object
    """
    categories = ['Load Shed (MW)', 'Customers (K)', 'Repair Cost ($M)']
    
    actual_values = [
        actual_impact.get('load_shed', 0),
        actual_impact.get('customers', 0) / 1000,
        actual_impact.get('cost', 0) / 1000000
    ]
    
    prevented_values = [
        prevented_impact.get('load_shed', 0),
        prevented_impact.get('customers', 0) / 1000,
        prevented_impact.get('cost', 0) / 1000000
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Actual Impact',
        x=categories,
        y=actual_values,
        marker_color=COLORS['failed'],
        text=[f'{v:,.1f}' for v in actual_values],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='If Patient Zero Reinforced',
        x=categories,
        y=prevented_values,
        marker_color=COLORS['active'],
        text=[f'{v:,.1f}' for v in prevented_values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=dict(
            text='Impact Comparison: Actual vs. Prevention Scenario',
            font=dict(size=16, color='white')
        ),
        barmode='group',
        xaxis=dict(color='white'),
        yaxis=dict(
            title='Impact',
            color='white',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=80, b=60),
        height=350
    )
    
    return fig


def create_kpi_card(value: str, label: str, delta: Optional[str] = None) -> str:
    """
    Generate HTML for a KPI card.
    
    Args:
        value: Main value to display
        label: Description label
        delta: Optional delta/change indicator
    
    Returns:
        HTML string for the card
    """
    delta_html = ""
    if delta:
        delta_color = COLORS['active'] if delta.startswith('+') else COLORS['failed']
        delta_html = f'<span style="color:{delta_color};font-size:14px;">{delta}</span>'
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['snowflake_dark']} 0%, #2d3748 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(41, 181, 232, 0.3);
    ">
        <div style="font-size: 32px; font-weight: bold; color: {COLORS['snowflake_blue']};">
            {value}
        </div>
        <div style="font-size: 14px; color: #94A3B8; margin-top: 4px;">
            {label}
        </div>
        {delta_html}
    </div>
    """


# =============================================================================
# DIRECTOR PERSONA - EXECUTIVE VISUALIZATIONS
# =============================================================================

# Region color mapping for consistent visualization
# Note: Keys match the actual region names in the data (mixed case with spaces)
REGION_COLORS = {
    # ERCOT regions (as they appear in data)
    'Permian Basin': '#e74c3c',   # Red
    'Gulf Coast': '#1abc9c',      # Teal
    'Panhandle': '#e67e22',       # Dark Orange
    'East Texas': '#27ae60',      # Emerald Green
    'West Texas': '#3498db',      # Blue
    'North Central': '#9b59b6',   # Purple
    'South Central': '#f39c12',   # Orange
    # Uppercase variants (legacy/fallback)
    'WEST_TEXAS': '#3498db',      # Blue
    'NORTH_CENTRAL': '#9b59b6',   # Purple
    'COASTAL': '#1abc9c',         # Teal
    'SOUTH_TEXAS': '#f39c12',     # Orange
    'PERMIAN_BASIN': '#e74c3c',   # Red
    'GULF_COAST': '#1abc9c',      # Teal
    'PANHANDLE': '#e67e22',       # Dark Orange
    'EAST_TEXAS': '#27ae60',      # Emerald
}


def create_investment_matrix(
    priorities_df: pd.DataFrame,
    title: str = "Investment Priority Matrix"
) -> go.Figure:
    """
    Create a scatter plot investment priority matrix.
    
    X-axis: Estimated reinforcement cost
    Y-axis: Impact if node fails (potential loss)
    Bubble size: Network centrality (node degree)
    Color: Region
    
    Quadrants help executives prioritize:
    - Top-Left: High impact, low cost -> MUST FIX
    - Top-Right: High impact, high cost -> CONSIDER
    - Bottom-Left: Low impact, low cost -> MONITOR
    - Bottom-Right: Low impact, high cost -> LOW PRIORITY
    """
    if priorities_df is None or len(priorities_df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No priority data available",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    # Create a clean copy and handle missing/null values
    df = priorities_df.copy()
    
    # Ensure required columns exist and have valid values
    if 'EST_REINFORCEMENT_COST' not in df.columns:
        df['EST_REINFORCEMENT_COST'] = 10000000  # Default $10M
    if 'IMPACT_IF_FAILS' not in df.columns:
        df['IMPACT_IF_FAILS'] = 5000000  # Default $5M
    if 'NODE_DEGREE' not in df.columns:
        df['NODE_DEGREE'] = 3
    if 'REGION' not in df.columns:
        df['REGION'] = 'Unknown'
    if 'NODE_NAME' not in df.columns:
        df['NODE_NAME'] = df.get('NODE_ID', 'Node')
    
    # Fill NaN values and convert to proper types
    try:
        df['EST_REINFORCEMENT_COST'] = pd.to_numeric(df['EST_REINFORCEMENT_COST'], errors='coerce').fillna(10000000)
        df['IMPACT_IF_FAILS'] = pd.to_numeric(df['IMPACT_IF_FAILS'], errors='coerce').fillna(5000000)
        df['NODE_DEGREE'] = pd.to_numeric(df['NODE_DEGREE'], errors='coerce').fillna(3)
        df['REGION'] = df['REGION'].fillna('Unknown').astype(str)
        df['NODE_NAME'] = df['NODE_NAME'].fillna('Unknown').astype(str)
    except Exception:
        # Fallback if conversion fails
        pass
    
    # Ensure we have positive values for the chart
    df = df[df['EST_REINFORCEMENT_COST'] >= 0]
    df = df[df['IMPACT_IF_FAILS'] >= 0]
    
    if len(df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No valid data points for matrix",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    # Calculate axis midpoints for quadrant lines
    x_mid = float(df['EST_REINFORCEMENT_COST'].median())
    y_mid = float(df['IMPACT_IF_FAILS'].median())
    x_max = float(df['EST_REINFORCEMENT_COST'].max())
    y_max = float(df['IMPACT_IF_FAILS'].max())
    
    # Calculate marker sizes (ensure minimum size for visibility)
    df['marker_size'] = (df['NODE_DEGREE'] * 2 + 12).clip(lower=12, upper=35)
    
    # Create figure
    fig = go.Figure()
    
    # Get unique regions for coloring
    regions = sorted(df['REGION'].unique())
    
    for region in regions:
        region_df = df[df['REGION'] == region]
        
        # Get color with fallback
        color = REGION_COLORS.get(region, REGION_COLORS.get(str(region).upper().replace(' ', '_'), '#3498db'))
        
        fig.add_trace(go.Scatter(
            x=region_df['EST_REINFORCEMENT_COST'].tolist(),
            y=region_df['IMPACT_IF_FAILS'].tolist(),
            mode='markers',
            name=region,
            marker=dict(
                size=region_df['marker_size'].tolist(),
                color=color,
                opacity=0.85,
                line=dict(width=1, color='white'),
                sizemode='diameter'
            ),
            text=region_df['NODE_NAME'].tolist(),
            hovertemplate=(
                '<b>%{text}</b><br>' +
                f'Region: {region}<br>' +
                'Reinforcement Cost: $%{x:,.0f}<br>' +
                'Impact if Fails: $%{y:,.0f}<br>' +
                '<extra></extra>'
            )
        ))
    
    # Add quadrant divider lines
    fig.add_hline(y=y_mid, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.add_vline(x=x_mid, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    
    # Add quadrant labels
    quadrants = [
        (x_mid * 0.3, y_mid * 1.8, "MUST FIX", COLORS['failed']),
        (x_mid * 1.7, y_mid * 1.8, "CONSIDER", COLORS['warning']),
        (x_mid * 0.3, y_mid * 0.2, "MONITOR", COLORS['active']),
        (x_mid * 1.7, y_mid * 0.2, "LOW PRIORITY", '#64748B'),
    ]
    
    for x, y, text, color in quadrants:
        fig.add_annotation(
            x=x, y=y, text=text,
            showarrow=False,
            font=dict(size=12, color=color, family='Arial Black'),
            opacity=0.7
        )
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white')),
        xaxis=dict(
            title='Estimated Reinforcement Cost ($)',
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='$,.0f',
            range=[0, x_max * 1.1]
        ),
        yaxis=dict(
            title='Impact if Node Fails ($)',
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='$,.0f',
            range=[0, y_max * 1.1]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=20, t=80, b=60),
        height=500
    )
    
    return fig


def create_scenario_comparison_chart(
    comparison_df: pd.DataFrame,
    title: str = "Scenario Comparison"
) -> go.Figure:
    """
    Create a multi-subplot bar chart comparing scenarios across metrics.
    
    Uses subplots so each metric has its own scale, making all values visible.
    Shows: Failures, Load Shed, Customer Impact, Repair Cost
    """
    from plotly.subplots import make_subplots
    
    if comparison_df is None or len(comparison_df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No scenario data available",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    scenarios = comparison_df['SCENARIO_NAME'].tolist()
    scenario_labels = [s.replace('_', ' ').title() for s in scenarios]
    
    # Define metrics with their display values and colors
    metrics = [
        ('Failures', comparison_df['FAILURES'].values, '#3498db', ''),
        ('Load Shed', comparison_df['TOTAL_LOAD_SHED_MW'].values / 1000, '#e74c3c', ' GW'),
        ('Customers', comparison_df['TOTAL_CUSTOMERS'].values / 1000, '#f39c12', 'K'),
        ('Cost', comparison_df['TOTAL_REPAIR_COST'].values / 1000000, '#9b59b6', '$M'),
    ]
    
    # Create 2x2 subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"{m[0]}" for m in metrics],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    for idx, (metric_name, values, color, unit) in enumerate(metrics):
        row, col = positions[idx]
        
        # Format text labels
        if unit == '$M':
            text_labels = [f'${v:.1f}M' for v in values]
        elif unit == 'K':
            text_labels = [f'{v:.0f}K' for v in values]
        elif unit == ' GW':
            text_labels = [f'{v:.1f} GW' for v in values]
        else:
            text_labels = [f'{v:.0f}' for v in values]
        
        fig.add_trace(
            go.Bar(
                x=scenario_labels,
            y=values,
                marker_color=color,
                text=text_labels,
            textposition='outside',
                textfont=dict(size=11, color='white'),
                showlegend=False
            ),
            row=row, col=col
        )
    
    # Find worst scenario for highlighting
    worst_idx = comparison_df['TOTAL_REPAIR_COST'].idxmax()
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=80, b=40),
        height=450
    )
    
    # Update all axes
    for i in range(1, 5):
        fig.update_xaxes(
            color='white', 
            tickangle=-20,
            tickfont=dict(size=10),
            row=(i-1)//2 + 1, 
            col=(i-1)%2 + 1
        )
        fig.update_yaxes(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            row=(i-1)//2 + 1,
            col=(i-1)%2 + 1
        )
    
    # Style subplot titles
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=13, color='white')
    
    return fig


def create_regional_heatmap(
    regional_df: pd.DataFrame,
    title: str = "Regional Risk Overview"
) -> go.Figure:
    """
    Create a horizontal bar chart showing regional risk metrics.
    
    Displays exposure, node count, and risk level by region.
    Color intensity indicates risk level.
    """
    if regional_df is None or len(regional_df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No regional data available",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    # Sort by exposure
    regional_df = regional_df.sort_values('TOTAL_EXPOSURE', ascending=True)
    
    # Color based on average failure probability
    colors = []
    for prob in regional_df['AVG_FAILURE_PROB']:
        if prob > 0.6:
            colors.append(COLORS['failed'])
        elif prob > 0.4:
            colors.append(COLORS['warning'])
        else:
            colors.append(COLORS['active'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=regional_df['REGION'].str.replace('_', ' ').str.title(),
        x=regional_df['TOTAL_EXPOSURE'],
        orientation='h',
        marker_color=colors,
        text=[f"${v/1000000:.1f}M" for v in regional_df['TOTAL_EXPOSURE']],
        textposition='outside',
        textfont=dict(color='white'),
        customdata=regional_df[['NODE_COUNT', 'HIGH_RISK_NODES', 'AVG_FAILURE_PROB', 'NODES_FAILED']].values,
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Total Exposure: $%{x:,.0f}<br>'
            'Nodes: %{customdata[0]}<br>'
            'High Risk Nodes: %{customdata[1]}<br>'
            'Avg Failure Prob: %{customdata[2]:.1%}<br>'
            'Nodes Failed: %{customdata[3]}<br>'
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white')),
        xaxis=dict(
            title='Total Exposure ($)',
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='$,.0f'
        ),
        yaxis=dict(
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=120, r=80, t=60, b=60),
        height=300
    )
    
    return fig


def create_regional_failures_chart(
    failures_df: pd.DataFrame,
    title: str = "Regional Failures by Scenario"
) -> go.Figure:
    """
    Create a grouped bar chart showing failure counts by region and scenario.
    """
    if failures_df is None or len(failures_df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No failure data available",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    scenarios = failures_df['SCENARIO_NAME'].unique()
    regions = failures_df['REGION'].unique()
    
    scenario_colors = {
        'BASE_CASE': '#3498db',
        'HIGH_LOAD': '#f39c12', 
        'WINTER_STORM_2021': '#e74c3c'
    }
    
    fig = go.Figure()
    
    for scenario in scenarios:
        scenario_data = failures_df[failures_df['SCENARIO_NAME'] == scenario]
        
        fig.add_trace(go.Bar(
            name=scenario.replace('_', ' ').title(),
            x=[r.replace('_', ' ').title() for r in scenario_data['REGION']],
            y=scenario_data['FAILURE_COUNT'],
            marker_color=scenario_colors.get(scenario, '#888888'),
            text=scenario_data['FAILURE_COUNT'],
            textposition='outside',
            textfont=dict(size=10, color='white')
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white')),
        barmode='group',
        xaxis=dict(
            title='Region',
            color='white',
            tickangle=-15
        ),
        yaxis=dict(
            title='Failure Count',
            color='white',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=80, b=80),
        height=400
    )
    
    return fig


def create_sankey_diagram(
    flows_df: pd.DataFrame,
    title: str = "Cross-Region Power Flow"
) -> go.Figure:
    """
    Create a Sankey diagram showing transmission capacity between regions.
    
    Width of flow indicates total transmission capacity (MW).
    """
    if flows_df is None or len(flows_df) == 0:
        fig = go.Figure()
        fig.add_annotation(x=0.5, y=0.5, text="No cross-region flow data available",
                          showarrow=False, font=dict(size=14, color='white'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    # Get unique regions and create node indices
    all_regions = list(set(flows_df['SOURCE_REGION'].tolist() + flows_df['TARGET_REGION'].tolist()))
    region_to_idx = {region: idx for idx, region in enumerate(all_regions)}
    
    # Prepare Sankey data
    sources = [region_to_idx[r] for r in flows_df['SOURCE_REGION']]
    targets = [region_to_idx[r] for r in flows_df['TARGET_REGION']]
    values = flows_df['TOTAL_CAPACITY_MW'].tolist()
    
    # Node colors
    node_colors = [REGION_COLORS.get(r, '#888888') for r in all_regions]
    
    # Link colors (lighter versions of source colors)
    link_colors = [f"rgba{tuple(list(int(REGION_COLORS.get(flows_df.iloc[i]['SOURCE_REGION'], '#888888').lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.4])}" 
                   for i in range(len(flows_df))]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="white", width=1),
            label=[r.replace('_', ' ').title() for r in all_regions],
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate=(
                'From: %{source.label}<br>'
                'To: %{target.label}<br>'
                'Capacity: %{value:,.0f} MW<br>'
                '<extra></extra>'
            )
        )
    )])
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white')),
        font=dict(size=12, color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=20),
        height=400
    )
    
    return fig


def create_priority_gauge(
    high_priority: int,
    medium_priority: int, 
    low_priority: int,
    title: str = "Node Priority Distribution"
) -> go.Figure:
    """
    Create a donut chart showing distribution of node priorities.
    """
    total = high_priority + medium_priority + low_priority
    if total == 0:
        total = 1  # Avoid division by zero
    
    fig = go.Figure(data=[go.Pie(
        labels=['High Priority', 'Medium Priority', 'Low Priority'],
        values=[high_priority, medium_priority, low_priority],
        hole=0.6,
        marker=dict(colors=[COLORS['failed'], COLORS['warning'], COLORS['active']]),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(color='white', size=11),
        hovertemplate='%{label}: %{value} nodes<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='white')),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=20),
        height=300,
        annotations=[dict(
            text=f'{total}<br>Nodes',
            x=0.5, y=0.5,
            font=dict(size=20, color='white'),
            showarrow=False
        )]
    )
    
    return fig


def create_executive_summary_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "",
    color: str = None,
    trend: str = None
) -> str:
    """
    Generate HTML for an executive summary card with optional trend indicator.
    """
    card_color = color or COLORS['snowflake_blue']
    
    trend_html = ""
    if trend:
        trend_icon = "↑" if trend.startswith('+') else "↓" if trend.startswith('-') else ""
        trend_color = COLORS['failed'] if trend.startswith('+') else COLORS['active']
        trend_html = f'<div style="color: {trend_color}; font-size: 14px; margin-top: 4px;">{trend_icon} {trend}</div>'
    
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(27, 42, 65, 0.8) 0%, rgba(15, 20, 25, 0.9) 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(41, 181, 232, 0.3);
        border-left: 4px solid {card_color};
        height: 100%;
    ">
        <div style="font-size: 14px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            {icon} {title}
        </div>
        <div style="font-size: 36px; font-weight: 700; color: {card_color}; line-height: 1.1;">
            {value}
        </div>
        <div style="font-size: 13px; color: #64748B; margin-top: 8px;">
            {subtitle}
        </div>
        {trend_html}
    </div>
    """

