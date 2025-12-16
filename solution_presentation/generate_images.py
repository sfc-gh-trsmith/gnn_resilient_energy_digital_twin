#!/usr/bin/env python3
"""
Generate visual assets for GridGuard Solution Presentation.
Creates architecture diagrams, network visualizations, and dashboard mockups.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as path_effects
import numpy as np
import networkx as nx
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)

# Color palette - Snowflake-inspired with energy grid accents
COLORS = {
    'snowflake_blue': '#29B5E8',
    'snowflake_dark': '#1E3A5F',
    'data_green': '#2ECC71',
    'compute_orange': '#F39C12',
    'results_purple': '#9B59B6',
    'cortex_teal': '#1ABC9C',
    'app_pink': '#E91E63',
    'background': '#0D1B2A',
    'card_bg': '#1B2838',
    'text_light': '#FFFFFF',
    'text_muted': '#8899A6',
    'grid_active': '#27AE60',
    'grid_warning': '#F1C40F',
    'grid_failed': '#E74C3C',
    'patient_zero': '#FF6B6B',
}


def create_architecture_diagram():
    """Create the main architecture diagram showing data flow through GridGuard."""
    fig, ax = plt.subplots(figsize=(14, 10), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'GridGuard Architecture', fontsize=24, fontweight='bold',
            color=COLORS['text_light'], ha='center', va='center',
            fontfamily='sans-serif')
    ax.text(7, 9.0, 'Snowflake Data Cloud', fontsize=14,
            color=COLORS['snowflake_blue'], ha='center', va='center',
            fontfamily='sans-serif')
    
    def draw_rounded_box(x, y, w, h, color, label, sublabel=None):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2 + (0.15 if sublabel else 0), label, fontsize=11, 
                fontweight='bold', color='white', ha='center', va='center')
        if sublabel:
            ax.text(x + w/2, y + h/2 - 0.2, sublabel, fontsize=8, 
                    color=COLORS['text_muted'], ha='center', va='center')
    
    def draw_section_box(x, y, w, h, label, color):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.3",
                             facecolor='none', edgecolor=color, linewidth=2, 
                             linestyle='--', alpha=0.7)
        ax.add_patch(box)
        ax.text(x + 0.15, y + h - 0.25, label, fontsize=10, fontweight='bold',
                color=color, ha='left', va='top')
    
    # Data Foundation section
    draw_section_box(0.5, 6.5, 4.5, 2.2, 'DATA FOUNDATION', COLORS['data_green'])
    draw_rounded_box(0.7, 7.4, 2, 0.9, COLORS['data_green'], 'Grid Nodes', '45 substations')
    draw_rounded_box(2.8, 7.4, 2, 0.9, COLORS['data_green'], 'Grid Edges', '106 lines')
    draw_rounded_box(0.7, 6.7, 2, 0.6, COLORS['data_green'], 'Telemetry', '12,960 records')
    draw_rounded_box(2.8, 6.7, 2, 0.6, COLORS['data_green'], 'Compliance', '8 NERC docs')
    
    # SPCS Compute section
    draw_section_box(5.5, 6.5, 3, 2.2, 'SPCS GPU COMPUTE', COLORS['compute_orange'])
    draw_rounded_box(5.7, 6.8, 2.6, 1.6, COLORS['compute_orange'], 'PyTorch Geometric', 'GCN Model')
    
    # Results section
    draw_section_box(9, 6.5, 4.5, 2.2, 'ANALYSIS RESULTS', COLORS['results_purple'])
    draw_rounded_box(9.2, 7.4, 2, 0.9, COLORS['results_purple'], 'Simulation', 'Results Table')
    draw_rounded_box(11.3, 7.4, 2, 0.9, COLORS['results_purple'], 'Patient Zero', 'Cascade Origin')
    draw_rounded_box(9.2, 6.7, 4.1, 0.6, COLORS['results_purple'], 'Risk Scores & Financial Impact')
    
    # Cortex Intelligence section
    draw_section_box(0.5, 3.5, 6.5, 2.2, 'CORTEX INTELLIGENCE', COLORS['cortex_teal'])
    draw_rounded_box(0.7, 3.8, 3, 1.5, COLORS['cortex_teal'], 'Cortex Analyst', 'SQL from Natural Language')
    draw_rounded_box(3.9, 3.8, 3, 1.5, COLORS['cortex_teal'], 'Cortex Search', 'RAG over Documents')
    
    # Streamlit App section
    draw_section_box(7.5, 3.5, 6, 2.2, 'STREAMLIT DASHBOARD', COLORS['app_pink'])
    draw_rounded_box(7.7, 3.8, 2.8, 1.5, COLORS['app_pink'], 'Network Viz', 'Interactive Graph')
    draw_rounded_box(10.6, 3.8, 2.7, 1.5, COLORS['app_pink'], 'AI Chat', 'Query Interface')
    
    # Arrows - Data flow
    arrow_style = dict(arrowstyle='->', color='white', lw=2, mutation_scale=15)
    
    # Data to Compute
    ax.annotate('', xy=(5.5, 7.6), xytext=(4.9, 7.6), arrowprops=arrow_style)
    
    # Compute to Results
    ax.annotate('', xy=(9, 7.6), xytext=(8.5, 7.6), arrowprops=arrow_style)
    
    # Results to Cortex Analyst
    ax.annotate('', xy=(3.7, 5.7), xytext=(10, 6.5), arrowprops=arrow_style)
    
    # Compliance to Cortex Search
    ax.annotate('', xy=(5.4, 5.7), xytext=(3.8, 6.5), arrowprops=arrow_style)
    
    # Results to Network Viz
    ax.annotate('', xy=(9.1, 5.7), xytext=(11.5, 6.5), arrowprops=arrow_style)
    
    # Cortex to Chat
    ax.annotate('', xy=(10.6, 4.5), xytext=(7, 4.5), arrowprops=arrow_style)
    
    # User personas at bottom
    ax.text(7, 1.5, 'Target Users', fontsize=14, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    
    personas = [
        ('Director of\nGrid Planning', 2.5),
        ('Compliance\nOfficer', 7),
        ('Data\nScientist', 11.5),
    ]
    for name, x in personas:
        circle = Circle((x, 0.7), 0.4, facecolor=COLORS['snowflake_blue'], 
                        edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, 0.7, 'U', fontsize=16, fontweight='bold', color='white',
                ha='center', va='center')
        ax.text(x, 0.0, name, fontsize=9, color=COLORS['text_light'], 
                ha='center', va='top')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'architecture.png', dpi=150, facecolor=COLORS['background'],
                edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'architecture.png'}")


def create_cascade_network():
    """Create a network visualization showing cascade failure states."""
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    
    # Create a sample grid network
    np.random.seed(42)
    G = nx.random_geometric_graph(45, 0.25, seed=42)
    
    # Get positions and scale them
    pos = nx.get_node_attributes(G, 'pos')
    pos = {k: (v[0] * 10, v[1] * 8) for k, v in pos.items()}
    
    # Assign node states: most active, some warning, some failed
    # Node 7 will be Patient Zero
    patient_zero = 7
    failed_nodes = {7, 12, 15, 23, 31, 38}  # Cascade path
    warning_nodes = {8, 14, 16, 22, 24, 30, 32, 37, 39}
    
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node == patient_zero:
            node_colors.append(COLORS['patient_zero'])
            node_sizes.append(800)
        elif node in failed_nodes:
            node_colors.append(COLORS['grid_failed'])
            node_sizes.append(500)
        elif node in warning_nodes:
            node_colors.append(COLORS['grid_warning'])
            node_sizes.append(400)
        else:
            node_colors.append(COLORS['grid_active'])
            node_sizes.append(300)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.4, edge_color=COLORS['text_muted'], 
                           width=1.5, ax=ax)
    
    # Highlight cascade path edges
    cascade_edges = [(7, 12), (12, 15), (15, 23), (23, 31), (31, 38)]
    cascade_edges_in_graph = [(u, v) for u, v in cascade_edges if G.has_edge(u, v)]
    if cascade_edges_in_graph:
        nx.draw_networkx_edges(G, pos, edgelist=cascade_edges_in_graph,
                               edge_color=COLORS['grid_failed'], width=3, 
                               alpha=0.8, ax=ax)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                           edgecolors='white', linewidths=2, ax=ax)
    
    # Add labels for key nodes
    labels = {patient_zero: 'P0', 12: 'N12', 15: 'N15', 23: 'N23', 31: 'N31', 38: 'N38'}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color='white',
                            font_weight='bold', ax=ax)
    
    # Title
    ax.text(5, 8.8, 'Grid Cascade Analysis', fontsize=22, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    ax.text(5, 8.3, 'WINTER_STORM_2021 Scenario', fontsize=14,
            color=COLORS['snowflake_blue'], ha='center')
    
    # Legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['patient_zero'],
               markersize=15, label='Patient Zero (P0)', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['grid_failed'],
               markersize=12, label='Failed Nodes', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['grid_warning'],
               markersize=10, label='Warning State', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['grid_active'],
               markersize=8, label='Active Nodes', linestyle='None'),
        Line2D([0], [0], color=COLORS['grid_failed'], linewidth=3, 
               label='Cascade Path'),
    ]
    legend = ax.legend(handles=legend_elements, loc='lower right', 
                       facecolor=COLORS['card_bg'], edgecolor='white',
                       fontsize=10, framealpha=0.9)
    for text in legend.get_texts():
        text.set_color(COLORS['text_light'])
    
    # Metrics box
    metrics_text = "Cascade Statistics\n\n"
    metrics_text += "Failed Nodes: 6\n"
    metrics_text += "Warning Nodes: 9\n"
    metrics_text += "Load Shed: 847 MW\n"
    metrics_text += "Customers: 142,500\n"
    metrics_text += "Est. Repair: $12.4M"
    
    props = dict(boxstyle='round,pad=0.5', facecolor=COLORS['card_bg'], 
                 edgecolor='white', alpha=0.9)
    ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', color=COLORS['text_light'], bbox=props,
            fontfamily='monospace')
    
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 9)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'cascade-network.png', dpi=150, 
                facecolor=COLORS['background'], edgecolor='none',
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'cascade-network.png'}")


def create_patient_zero_visual():
    """Create a focused visualization of Patient Zero identification."""
    fig, ax = plt.subplots(figsize=(12, 8), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    
    # Create a smaller, focused network around Patient Zero
    G = nx.Graph()
    
    # Patient Zero at center, with 2 levels of connected nodes
    center = 'SUB_007'
    level1 = ['SUB_012', 'SUB_015', 'SUB_008', 'SUB_003']
    level2 = ['SUB_023', 'SUB_031', 'SUB_019', 'SUB_025', 'SUB_014', 'SUB_006']
    
    G.add_node(center)
    G.add_nodes_from(level1)
    G.add_nodes_from(level2)
    
    # Connect Patient Zero to level 1
    for node in level1:
        G.add_edge(center, node)
    
    # Connect level 1 to level 2
    G.add_edge('SUB_012', 'SUB_023')
    G.add_edge('SUB_012', 'SUB_031')
    G.add_edge('SUB_015', 'SUB_019')
    G.add_edge('SUB_015', 'SUB_025')
    G.add_edge('SUB_008', 'SUB_014')
    G.add_edge('SUB_003', 'SUB_006')
    
    # Position nodes in concentric circles
    pos = {center: (0, 0)}
    angles1 = np.linspace(0, 2*np.pi, len(level1), endpoint=False)
    for i, node in enumerate(level1):
        pos[node] = (2 * np.cos(angles1[i]), 2 * np.sin(angles1[i]))
    
    angles2 = np.linspace(np.pi/6, 2*np.pi + np.pi/6, len(level2), endpoint=False)
    for i, node in enumerate(level2):
        pos[node] = (4 * np.cos(angles2[i]), 4 * np.sin(angles2[i]))
    
    # Scale positions
    pos = {k: (v[0] * 1.2 + 6, v[1] * 0.8 + 4) for k, v in pos.items()}
    
    # Node colors and sizes
    failed_nodes = {center, 'SUB_012', 'SUB_015', 'SUB_023'}
    
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node == center:
            node_colors.append(COLORS['patient_zero'])
            node_sizes.append(2000)
        elif node in failed_nodes:
            node_colors.append(COLORS['grid_failed'])
            node_sizes.append(800)
        elif node in level1:
            node_colors.append(COLORS['grid_warning'])
            node_sizes.append(600)
        else:
            node_colors.append(COLORS['grid_active'])
            node_sizes.append(500)
    
    # Draw edges with varying opacity based on cascade
    cascade_edges = [(center, 'SUB_012'), ('SUB_012', 'SUB_023'), 
                     (center, 'SUB_015'), ('SUB_015', 'SUB_019')]
    
    for edge in G.edges():
        if edge in cascade_edges or (edge[1], edge[0]) in cascade_edges:
            ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                   [pos[edge[0]][1], pos[edge[1]][1]],
                   color=COLORS['grid_failed'], linewidth=4, alpha=0.8, zorder=1)
        else:
            ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                   [pos[edge[0]][1], pos[edge[1]][1]],
                   color=COLORS['text_muted'], linewidth=2, alpha=0.4, zorder=1)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                           edgecolors='white', linewidths=3, ax=ax)
    
    # Labels with probabilities
    labels_probs = {
        center: 'SUB_007\n0.94',
        'SUB_012': 'SUB_012\n0.87',
        'SUB_015': 'SUB_015\n0.82',
        'SUB_023': 'SUB_023\n0.71',
        'SUB_008': 'SUB_008\n0.45',
        'SUB_003': 'SUB_003\n0.38',
    }
    
    for node, label in labels_probs.items():
        x, y = pos[node]
        ax.text(x, y, label, fontsize=9, fontweight='bold', color='white',
                ha='center', va='center')
    
    # Draw other labels
    for node in G.nodes():
        if node not in labels_probs:
            x, y = pos[node]
            ax.text(x, y, node.replace('SUB_', ''), fontsize=8, color='white',
                    ha='center', va='center')
    
    # Title
    ax.text(6, 7.5, 'Patient Zero Identification', fontsize=22, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    ax.text(6, 7.0, 'GCN Model Output: Failure Probability per Node', fontsize=12,
            color=COLORS['snowflake_blue'], ha='center')
    
    # Patient Zero callout
    callout_text = "PATIENT ZERO: SUB_007\n\n"
    callout_text += "Failure Probability: 94.2%\n"
    callout_text += "Criticality Score: 0.92\n"
    callout_text += "Capacity: 1,200 MW\n"
    callout_text += "Type: TRANSMISSION_HUB\n\n"
    callout_text += "AI Analysis:\n"
    callout_text += "High criticality combined with\n"
    callout_text += "network position makes this\n"
    callout_text += "node the cascade origin point."
    
    props = dict(boxstyle='round,pad=0.5', facecolor=COLORS['patient_zero'], 
                 edgecolor='white', alpha=0.95)
    ax.text(0.02, 0.98, callout_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', color='white', bbox=props,
            fontfamily='sans-serif')
    
    # Cascade depth legend
    depth_text = "Cascade Depth\n\n"
    depth_text += "Depth 0: SUB_007 (Origin)\n"
    depth_text += "Depth 1: SUB_012, SUB_015\n"
    depth_text += "Depth 2: SUB_023, SUB_019\n"
    depth_text += "Depth 3+: Warning state"
    
    props2 = dict(boxstyle='round,pad=0.5', facecolor=COLORS['card_bg'], 
                  edgecolor='white', alpha=0.9)
    ax.text(0.98, 0.02, depth_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', horizontalalignment='right',
            color=COLORS['text_light'], bbox=props2, fontfamily='monospace')
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'patient-zero.png', dpi=150, 
                facecolor=COLORS['background'], edgecolor='none',
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'patient-zero.png'}")


def create_dashboard_preview():
    """Create a mockup of the Streamlit dashboard interface."""
    fig = plt.figure(figsize=(14, 10), facecolor='#0E1117')
    
    # Main layout
    gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 3, 2], width_ratios=[1, 2, 1.5],
                          hspace=0.15, wspace=0.15, left=0.02, right=0.98, 
                          top=0.95, bottom=0.05)
    
    # Header
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_facecolor('#0E1117')
    ax_header.axis('off')
    ax_header.text(0.02, 0.5, 'GridGuard Dashboard', fontsize=24, fontweight='bold',
                   color='white', va='center', transform=ax_header.transAxes)
    ax_header.text(0.98, 0.5, 'WINTER_STORM_2021 Scenario', fontsize=14,
                   color=COLORS['snowflake_blue'], va='center', ha='right',
                   transform=ax_header.transAxes)
    
    # Sidebar
    ax_sidebar = fig.add_subplot(gs[1:, 0])
    ax_sidebar.set_facecolor('#262730')
    ax_sidebar.axis('off')
    
    # Sidebar content
    sidebar_y = 0.95
    ax_sidebar.text(0.1, sidebar_y, 'Scenario Selection', fontsize=12, fontweight='bold',
                    color='white', transform=ax_sidebar.transAxes)
    
    scenarios = ['BASE_CASE', 'HIGH_LOAD', 'WINTER_STORM_2021']
    for i, scenario in enumerate(scenarios):
        y = sidebar_y - 0.08 - i * 0.06
        color = COLORS['snowflake_blue'] if scenario == 'WINTER_STORM_2021' else COLORS['text_muted']
        marker = '◉' if scenario == 'WINTER_STORM_2021' else '○'
        ax_sidebar.text(0.1, y, f'{marker} {scenario}', fontsize=10, color=color,
                        transform=ax_sidebar.transAxes)
    
    ax_sidebar.text(0.1, 0.65, 'Filters', fontsize=12, fontweight='bold',
                    color='white', transform=ax_sidebar.transAxes)
    ax_sidebar.text(0.1, 0.58, 'Node Type: All', fontsize=10, color=COLORS['text_muted'],
                    transform=ax_sidebar.transAxes)
    ax_sidebar.text(0.1, 0.52, 'Region: All', fontsize=10, color=COLORS['text_muted'],
                    transform=ax_sidebar.transAxes)
    ax_sidebar.text(0.1, 0.46, 'Risk Threshold: 0.5', fontsize=10, color=COLORS['text_muted'],
                    transform=ax_sidebar.transAxes)
    
    # Run button
    btn = FancyBboxPatch((0.1, 0.3), 0.8, 0.08, boxstyle="round,pad=0.02",
                         facecolor=COLORS['snowflake_blue'], edgecolor='none',
                         transform=ax_sidebar.transAxes)
    ax_sidebar.add_patch(btn)
    ax_sidebar.text(0.5, 0.34, 'Run Simulation', fontsize=11, fontweight='bold',
                    color='white', ha='center', transform=ax_sidebar.transAxes)
    
    # Main network visualization
    ax_network = fig.add_subplot(gs[1, 1])
    ax_network.set_facecolor('#1E1E2E')
    ax_network.set_title('Network Topology', fontsize=14, color='white', pad=10)
    
    # Draw a mini network
    np.random.seed(42)
    G = nx.random_geometric_graph(25, 0.35, seed=42)
    pos = nx.get_node_attributes(G, 'pos')
    
    failed = {3, 7, 12}
    warning = {4, 8, 11, 13}
    
    node_colors = []
    for node in G.nodes():
        if node == 7:
            node_colors.append(COLORS['patient_zero'])
        elif node in failed:
            node_colors.append(COLORS['grid_failed'])
        elif node in warning:
            node_colors.append(COLORS['grid_warning'])
        else:
            node_colors.append(COLORS['grid_active'])
    
    nx.draw(G, pos, node_color=node_colors, node_size=150, 
            edge_color=COLORS['text_muted'], width=1, alpha=0.7, ax=ax_network)
    ax_network.axis('off')
    
    # Metrics cards
    ax_metrics = fig.add_subplot(gs[1, 2])
    ax_metrics.set_facecolor('#0E1117')
    ax_metrics.axis('off')
    
    metrics = [
        ('Load Shed', '847 MW', COLORS['grid_failed']),
        ('Customers', '142,500', COLORS['grid_warning']),
        ('Repair Cost', '$12.4M', COLORS['results_purple']),
        ('Risk Score', '0.78', COLORS['snowflake_blue']),
    ]
    
    for i, (label, value, color) in enumerate(metrics):
        y = 0.85 - i * 0.22
        card = FancyBboxPatch((0.05, y - 0.08), 0.9, 0.18, boxstyle="round,pad=0.02",
                              facecolor=COLORS['card_bg'], edgecolor=color, linewidth=2,
                              transform=ax_metrics.transAxes)
        ax_metrics.add_patch(card)
        ax_metrics.text(0.5, y + 0.03, value, fontsize=20, fontweight='bold',
                        color=color, ha='center', transform=ax_metrics.transAxes)
        ax_metrics.text(0.5, y - 0.04, label, fontsize=10, color=COLORS['text_muted'],
                        ha='center', transform=ax_metrics.transAxes)
    
    # Chat interface
    ax_chat = fig.add_subplot(gs[2, 1:])
    ax_chat.set_facecolor('#1E1E2E')
    ax_chat.axis('off')
    ax_chat.set_title('AI Assistant', fontsize=14, color='white', pad=10, loc='left')
    
    # Chat messages
    messages = [
        ('user', 'What was the total repair cost for failed substations?'),
        ('ai', 'Based on the WINTER_STORM_2021 simulation, the total estimated repair cost for all 6 failed substations is $12,418,750. The highest individual cost is SUB_007 (Patient Zero) at $3.2M.'),
    ]
    
    y_pos = 0.85
    for role, msg in messages:
        if role == 'user':
            props = dict(boxstyle='round,pad=0.4', facecolor='#3B3B4F', edgecolor='none')
            ax_chat.text(0.98, y_pos, msg, fontsize=10, color='white', ha='right',
                        transform=ax_chat.transAxes, bbox=props, wrap=True)
            y_pos -= 0.15
        else:
            props = dict(boxstyle='round,pad=0.4', facecolor=COLORS['snowflake_blue'], 
                        edgecolor='none', alpha=0.3)
            ax_chat.text(0.02, y_pos, msg, fontsize=10, color='white', ha='left',
                        transform=ax_chat.transAxes, bbox=props, wrap=True)
            y_pos -= 0.35
    
    # Input field
    input_box = FancyBboxPatch((0.02, 0.05), 0.85, 0.12, boxstyle="round,pad=0.02",
                               facecolor='#3B3B4F', edgecolor=COLORS['text_muted'],
                               transform=ax_chat.transAxes)
    ax_chat.add_patch(input_box)
    ax_chat.text(0.04, 0.11, 'Ask about simulation results or compliance...', 
                 fontsize=10, color=COLORS['text_muted'], transform=ax_chat.transAxes)
    
    send_btn = FancyBboxPatch((0.89, 0.05), 0.09, 0.12, boxstyle="round,pad=0.02",
                              facecolor=COLORS['snowflake_blue'], edgecolor='none',
                              transform=ax_chat.transAxes)
    ax_chat.add_patch(send_btn)
    ax_chat.text(0.935, 0.11, '→', fontsize=14, fontweight='bold', color='white',
                 ha='center', transform=ax_chat.transAxes)
    
    plt.savefig(OUTPUT_DIR / 'dashboard-preview.png', dpi=150, facecolor='#0E1117',
                edgecolor='none', bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'dashboard-preview.png'}")


def create_problem_impact():
    """Create an infographic showing the business impact of grid failures (Texas Winter Storm)."""
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')
    
    # Title
    ax.text(7, 8.5, 'The Cost of Cascade Failures', fontsize=26, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    ax.text(7, 7.9, 'Texas Winter Storm Uri (February 2021) - A Preventable Disaster',
            fontsize=14, color=COLORS['grid_failed'], ha='center')
    
    # Main impact statistics - large cards
    stats = [
        ('$195B', 'Economic\nDamages', COLORS['grid_failed'], 2.5),
        ('4.5M', 'Customers\nWithout Power', COLORS['grid_warning'], 7),
        ('246+', 'Lives\nLost', COLORS['results_purple'], 11.5),
    ]
    
    for value, label, color, x in stats:
        # Card background
        card = FancyBboxPatch((x - 1.8, 5.2), 3.6, 2.3, boxstyle="round,pad=0.05",
                             facecolor=COLORS['card_bg'], edgecolor=color, 
                             linewidth=3, alpha=0.95)
        ax.add_patch(card)
        
        # Value
        ax.text(x, 6.5, value, fontsize=36, fontweight='bold', color=color,
                ha='center', va='center')
        # Label
        ax.text(x, 5.6, label, fontsize=12, color=COLORS['text_light'],
                ha='center', va='center', linespacing=1.3)
    
    # Timeline bar showing duration
    ax.text(7, 4.5, 'Crisis Timeline', fontsize=16, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    
    # Timeline background
    timeline_bar = FancyBboxPatch((1, 3.5), 12, 0.6, boxstyle="round,pad=0.02",
                                  facecolor=COLORS['card_bg'], edgecolor='white',
                                  linewidth=1)
    ax.add_patch(timeline_bar)
    
    # Timeline progress (showing outage duration)
    progress_bar = FancyBboxPatch((1, 3.5), 8, 0.6, boxstyle="round,pad=0.02",
                                  facecolor=COLORS['grid_failed'], edgecolor='none',
                                  alpha=0.8)
    ax.add_patch(progress_bar)
    
    # Timeline labels
    ax.text(1, 3.2, 'Feb 14', fontsize=9, color=COLORS['text_muted'], ha='center')
    ax.text(5, 3.2, 'Peak Outage\n4+ Days', fontsize=9, color=COLORS['grid_failed'], 
            ha='center', fontweight='bold')
    ax.text(9, 3.2, 'Partial\nRestoration', fontsize=9, color=COLORS['grid_warning'], ha='center')
    ax.text(13, 3.2, 'Feb 20', fontsize=9, color=COLORS['text_muted'], ha='center')
    
    # Root cause callout
    cause_text = "ROOT CAUSE: Cascade Failure\n\n"
    cause_text += "A single generator failure triggered a\n"
    cause_text += "chain reaction across interconnected\n"
    cause_text += "substations. Without predictive analytics,\n"
    cause_text += "operators could not identify the cascade\n"
    cause_text += "origin or prevent propagation."
    
    props = dict(boxstyle='round,pad=0.6', facecolor='#2C1810', 
                 edgecolor=COLORS['grid_failed'], linewidth=2)
    ax.text(3.5, 1.5, cause_text, fontsize=11, color=COLORS['text_light'],
            ha='center', va='center', bbox=props, linespacing=1.4)
    
    # Solution callout
    solution_text = "WITH GRIDGUARD\n\n"
    solution_text += "GNN-based prediction identifies\n"
    solution_text += "vulnerable nodes BEFORE failure.\n"
    solution_text += "Patient Zero detection enables\n"
    solution_text += "targeted intervention within minutes,\n"
    solution_text += "not days."
    
    props2 = dict(boxstyle='round,pad=0.6', facecolor='#102820', 
                  edgecolor=COLORS['data_green'], linewidth=2)
    ax.text(10.5, 1.5, solution_text, fontsize=11, color=COLORS['text_light'],
            ha='center', va='center', bbox=props2, linespacing=1.4)
    
    # Arrow between cause and solution
    ax.annotate('', xy=(8.2, 1.5), xytext=(6.2, 1.5),
                arrowprops=dict(arrowstyle='->', color=COLORS['snowflake_blue'], 
                               lw=3, mutation_scale=20))
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'problem-impact.png', dpi=150, facecolor=COLORS['background'],
                edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'problem-impact.png'}")


def create_before_after():
    """Create a before/after comparison showing reactive vs proactive approaches."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), facecolor=COLORS['background'])
    
    for ax in axes:
        ax.set_facecolor(COLORS['background'])
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 8)
        ax.axis('off')
    
    # Main title
    fig.suptitle('Transformation: From Reactive to Proactive', fontsize=24, 
                 fontweight='bold', color=COLORS['text_light'], y=0.96)
    
    # LEFT SIDE: Before (Reactive)
    ax_before = axes[0]
    
    # Header
    header_box = FancyBboxPatch((0.3, 7), 6.4, 0.7, boxstyle="round,pad=0.02",
                                facecolor=COLORS['grid_failed'], edgecolor='white',
                                linewidth=2)
    ax_before.add_patch(header_box)
    ax_before.text(3.5, 7.35, 'BEFORE: Reactive Response', fontsize=16, 
                   fontweight='bold', color='white', ha='center')
    
    # Pain points
    pain_points = [
        ('Manual topology analysis', 'Weeks to model scenarios'),
        ('Post-incident investigation', 'Root cause found too late'),
        ('Siloed compliance data', 'Manual PDF searches'),
        ('No cascade prediction', 'Failures spread unchecked'),
        ('Delayed decision making', 'Millions in avoidable damage'),
    ]
    
    y_pos = 6.3
    for title, subtitle in pain_points:
        # X mark
        ax_before.text(0.6, y_pos, 'X', fontsize=18, fontweight='bold',
                       color=COLORS['grid_failed'], ha='center', va='center')
        # Text
        ax_before.text(1.1, y_pos + 0.1, title, fontsize=12, fontweight='bold',
                       color=COLORS['text_light'], va='center')
        ax_before.text(1.1, y_pos - 0.25, subtitle, fontsize=10,
                       color=COLORS['text_muted'], va='center')
        y_pos -= 1.1
    
    # Time indicator
    time_box = FancyBboxPatch((1.5, 0.3), 3.5, 0.8, boxstyle="round,pad=0.02",
                              facecolor=COLORS['card_bg'], edgecolor=COLORS['grid_failed'],
                              linewidth=2)
    ax_before.add_patch(time_box)
    ax_before.text(3.25, 0.7, 'Response Time: WEEKS', fontsize=13,
                   fontweight='bold', color=COLORS['grid_failed'], ha='center')
    
    # RIGHT SIDE: After (Proactive)
    ax_after = axes[1]
    
    # Header
    header_box2 = FancyBboxPatch((0.3, 7), 6.4, 0.7, boxstyle="round,pad=0.02",
                                 facecolor=COLORS['data_green'], edgecolor='white',
                                 linewidth=2)
    ax_after.add_patch(header_box2)
    ax_after.text(3.5, 7.35, 'AFTER: Proactive Prevention', fontsize=16,
                  fontweight='bold', color='white', ha='center')
    
    # Benefits
    benefits = [
        ('GNN topology analysis', 'Minutes to simulate any scenario'),
        ('Patient Zero prediction', 'Cascade origin identified instantly'),
        ('Cortex Search RAG', 'Natural language compliance queries'),
        ('Real-time risk scoring', 'Failures prevented before spread'),
        ('AI-powered insights', 'Decisions backed by data'),
    ]
    
    y_pos = 6.3
    for title, subtitle in benefits:
        # Check mark
        ax_after.text(0.6, y_pos, '>', fontsize=18, fontweight='bold',
                      color=COLORS['data_green'], ha='center', va='center')
        # Text
        ax_after.text(1.1, y_pos + 0.1, title, fontsize=12, fontweight='bold',
                      color=COLORS['text_light'], va='center')
        ax_after.text(1.1, y_pos - 0.25, subtitle, fontsize=10,
                      color=COLORS['text_muted'], va='center')
        y_pos -= 1.1
    
    # Time indicator
    time_box2 = FancyBboxPatch((1.5, 0.3), 3.5, 0.8, boxstyle="round,pad=0.02",
                               facecolor=COLORS['card_bg'], edgecolor=COLORS['data_green'],
                               linewidth=2)
    ax_after.add_patch(time_box2)
    ax_after.text(3.25, 0.7, 'Response Time: MINUTES', fontsize=13,
                  fontweight='bold', color=COLORS['data_green'], ha='center')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'before-after.png', dpi=150, facecolor=COLORS['background'],
                edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'before-after.png'}")


def create_roi_value():
    """Create a business value / ROI visualization."""
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')
    
    # Title
    ax.text(7, 8.5, 'Business Value of Predictive Grid Analytics', fontsize=24,
            fontweight='bold', color=COLORS['text_light'], ha='center')
    ax.text(7, 7.9, 'Quantified ROI from GridGuard Implementation', fontsize=14,
            color=COLORS['snowflake_blue'], ha='center')
    
    # Value metrics in horizontal layout
    metrics = [
        ('85%', 'Faster\nScenario Analysis', 'Weeks to minutes', COLORS['snowflake_blue']),
        ('60%', 'Reduced\nDowntime', 'Proactive intervention', COLORS['data_green']),
        ('$2.4M', 'Annual\nSavings', 'Per major utility', COLORS['compute_orange']),
        ('40%', 'Faster\nCompliance', 'AI-assisted reporting', COLORS['cortex_teal']),
    ]
    
    x_positions = [1.75, 5.25, 8.75, 12.25]
    for i, (value, label, sublabel, color) in enumerate(metrics):
        x = x_positions[i]
        
        # Card
        card = FancyBboxPatch((x - 1.5, 5), 3, 2.5, boxstyle="round,pad=0.05",
                             facecolor=COLORS['card_bg'], edgecolor=color,
                             linewidth=3)
        ax.add_patch(card)
        
        # Value (large)
        ax.text(x, 6.7, value, fontsize=32, fontweight='bold', color=color,
                ha='center', va='center')
        
        # Label
        ax.text(x, 5.8, label, fontsize=11, fontweight='bold',
                color=COLORS['text_light'], ha='center', va='center',
                linespacing=1.2)
        
        # Sublabel
        ax.text(x, 5.25, sublabel, fontsize=9, color=COLORS['text_muted'],
                ha='center', va='center')
    
    # How it works section
    ax.text(7, 4.2, 'How GridGuard Delivers Value', fontsize=18, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    
    # Process flow
    steps = [
        ('1', 'INGEST', 'Grid topology &\ntelemetry data', COLORS['data_green']),
        ('2', 'ANALYZE', 'GNN identifies\nrisk patterns', COLORS['compute_orange']),
        ('3', 'PREDICT', 'Patient Zero\ndetection', COLORS['results_purple']),
        ('4', 'ACT', 'Targeted\nintervention', COLORS['app_pink']),
    ]
    
    step_x = [2, 5, 8, 11]
    for i, (num, title, desc, color) in enumerate(steps):
        x = step_x[i]
        
        # Circle with number
        circle = Circle((x, 2.8), 0.4, facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, 2.8, num, fontsize=14, fontweight='bold', color='white',
                ha='center', va='center')
        
        # Title and description
        ax.text(x, 2.2, title, fontsize=12, fontweight='bold', color=color,
                ha='center')
        ax.text(x, 1.6, desc, fontsize=10, color=COLORS['text_muted'],
                ha='center', va='center', linespacing=1.2)
        
        # Arrow to next step
        if i < len(steps) - 1:
            ax.annotate('', xy=(step_x[i+1] - 0.6, 2.8), xytext=(x + 0.6, 2.8),
                       arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Bottom tagline
    tagline_box = FancyBboxPatch((3, 0.3), 8, 0.7, boxstyle="round,pad=0.02",
                                 facecolor=COLORS['snowflake_blue'], edgecolor='none',
                                 alpha=0.3)
    ax.add_patch(tagline_box)
    ax.text(7, 0.65, 'Prevent cascade failures before they happen. Save millions.', 
            fontsize=13, fontweight='bold', color=COLORS['text_light'], ha='center')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'roi-value.png', dpi=150, facecolor=COLORS['background'],
                edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'roi-value.png'}")


def create_timeline_comparison():
    """Create a timeline comparison showing speed improvement."""
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    
    # Title
    ax.text(7, 6.5, 'Speed to Insight: Traditional vs. GridGuard', fontsize=22,
            fontweight='bold', color=COLORS['text_light'], ha='center')
    
    # Traditional approach timeline (top)
    ax.text(0.5, 5.3, 'Traditional Approach', fontsize=14, fontweight='bold',
            color=COLORS['grid_failed'])
    
    # Timeline bar - traditional (long)
    trad_bar = FancyBboxPatch((0.5, 4.5), 13, 0.5, boxstyle="round,pad=0.02",
                              facecolor=COLORS['grid_failed'], edgecolor='white',
                              linewidth=1, alpha=0.8)
    ax.add_patch(trad_bar)
    
    # Traditional milestones
    trad_milestones = [
        (1.5, 'Data\nCollection', '2 days'),
        (4, 'Topology\nMapping', '1 week'),
        (7, 'Manual\nAnalysis', '2 weeks'),
        (10, 'Report\nGeneration', '3 days'),
        (12.5, 'Decision', '2-4 weeks\ntotal'),
    ]
    
    for x, label, time in trad_milestones:
        ax.plot([x, x], [4.5, 5.0], color='white', linewidth=2)
        ax.text(x, 4.2, label, fontsize=9, color=COLORS['text_muted'],
                ha='center', va='top', linespacing=1.1)
        ax.text(x, 5.15, time, fontsize=8, color='white', ha='center',
                fontweight='bold')
    
    # GridGuard approach timeline (bottom)
    ax.text(0.5, 2.8, 'With GridGuard', fontsize=14, fontweight='bold',
            color=COLORS['data_green'])
    
    # Timeline bar - GridGuard (short)
    gg_bar = FancyBboxPatch((0.5, 2.0), 3.5, 0.5, boxstyle="round,pad=0.02",
                            facecolor=COLORS['data_green'], edgecolor='white',
                            linewidth=1, alpha=0.8)
    ax.add_patch(gg_bar)
    
    # Remaining time (saved)
    saved_bar = FancyBboxPatch((4, 2.0), 9.5, 0.5, boxstyle="round,pad=0.02",
                               facecolor=COLORS['card_bg'], edgecolor=COLORS['data_green'],
                               linewidth=2, linestyle='--', alpha=0.5)
    ax.add_patch(saved_bar)
    ax.text(8.75, 2.25, 'TIME SAVED', fontsize=12, fontweight='bold',
            color=COLORS['data_green'], ha='center', alpha=0.8)
    
    # GridGuard milestones
    gg_milestones = [
        (1.2, 'Data\nLoaded', '< 1 min'),
        (2.5, 'GNN\nInference', '< 5 min'),
        (3.7, 'Results &\nDecision', '< 15 min\ntotal'),
    ]
    
    for x, label, time in gg_milestones:
        ax.plot([x, x], [2.0, 2.5], color='white', linewidth=2)
        ax.text(x, 1.7, label, fontsize=9, color=COLORS['text_muted'],
                ha='center', va='top', linespacing=1.1)
        ax.text(x, 2.65, time, fontsize=8, color='white', ha='center',
                fontweight='bold')
    
    # Improvement callout
    improvement_box = FancyBboxPatch((4.5, 0.3), 5, 1.2, boxstyle="round,pad=0.1",
                                     facecolor=COLORS['snowflake_blue'], 
                                     edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(improvement_box)
    ax.text(7, 1.05, '99% Faster', fontsize=28, fontweight='bold',
            color='white', ha='center')
    ax.text(7, 0.55, 'From weeks to minutes', fontsize=12,
            color='white', ha='center', alpha=0.9)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'timeline-comparison.png', dpi=150, 
                facecolor=COLORS['background'], edgecolor='none',
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'timeline-comparison.png'}")


def create_data_erd():
    """Create an ERD-style diagram showing source data structure and relationships."""
    fig, ax = plt.subplots(figsize=(14, 10), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'GridGuard Data Model', fontsize=24, fontweight='bold',
            color=COLORS['text_light'], ha='center')
    ax.text(7, 9.0, 'Source Tables and Relationships', fontsize=13,
            color=COLORS['snowflake_blue'], ha='center')
    
    def draw_table(x, y, w, h, name, table_type, columns, color):
        """Draw an ERD-style table box."""
        # Header
        header = FancyBboxPatch((x, y + h - 0.6), w, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                                facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 0.3, name, fontsize=11, fontweight='bold',
                color='white', ha='center', va='center')
        
        # Type badge
        type_colors = {'DIM': COLORS['data_green'], 'FACT': COLORS['compute_orange'], 
                      'REF': COLORS['cortex_teal'], 'OUTPUT': COLORS['results_purple']}
        badge_color = type_colors.get(table_type, COLORS['text_muted'])
        ax.text(x + w - 0.15, y + h - 0.3, table_type, fontsize=7, fontweight='bold',
                color=badge_color, ha='right', va='center',
                bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['card_bg'], 
                         edgecolor=badge_color, linewidth=1))
        
        # Body
        body = FancyBboxPatch((x, y), w, h - 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                              facecolor=COLORS['card_bg'], edgecolor='white', linewidth=2)
        ax.add_patch(body)
        
        # Columns
        col_y = y + h - 0.85
        for col_name, col_type, is_pk, is_fk in columns:
            prefix = ''
            col_color = COLORS['text_light']
            if is_pk:
                prefix = 'PK '
                col_color = COLORS['grid_warning']
            elif is_fk:
                prefix = 'FK '
                col_color = COLORS['snowflake_blue']
            
            ax.text(x + 0.15, col_y, f"{prefix}{col_name}", fontsize=8, 
                    color=col_color, va='center', fontfamily='monospace')
            ax.text(x + w - 0.15, col_y, col_type, fontsize=7,
                    color=COLORS['text_muted'], ha='right', va='center')
            col_y -= 0.28
    
    # GRID_NODES - Central dimension table
    nodes_cols = [
        ('NODE_ID', 'VARCHAR', True, False),
        ('NODE_NAME', 'VARCHAR', False, False),
        ('NODE_TYPE', 'VARCHAR', False, False),
        ('LAT, LON', 'FLOAT', False, False),
        ('CAPACITY_MW', 'FLOAT', False, False),
        ('VOLTAGE_KV', 'FLOAT', False, False),
        ('CRITICALITY_SCORE', 'FLOAT', False, False),
    ]
    draw_table(5.5, 5.5, 3, 2.8, 'GRID_NODES', 'DIM', nodes_cols, COLORS['data_green'])
    
    # GRID_EDGES - Dimension table
    edges_cols = [
        ('EDGE_ID', 'VARCHAR', True, False),
        ('SRC_NODE', 'VARCHAR', False, True),
        ('DST_NODE', 'VARCHAR', False, True),
        ('EDGE_TYPE', 'VARCHAR', False, False),
        ('CAPACITY_MW', 'FLOAT', False, False),
        ('LENGTH_MILES', 'FLOAT', False, False),
    ]
    draw_table(0.5, 5.5, 3, 2.4, 'GRID_EDGES', 'DIM', edges_cols, COLORS['data_green'])
    
    # HISTORICAL_TELEMETRY - Fact table
    telemetry_cols = [
        ('TELEMETRY_ID', 'VARCHAR', True, False),
        ('TIMESTAMP', 'TIMESTAMP', False, False),
        ('NODE_ID', 'VARCHAR', False, True),
        ('SCENARIO_NAME', 'VARCHAR', False, False),
        ('VOLTAGE_KV', 'FLOAT', False, False),
        ('LOAD_MW', 'FLOAT', False, False),
        ('STATUS', 'VARCHAR', False, False),
    ]
    draw_table(10.5, 5.5, 3, 2.6, 'HISTORICAL_TELEMETRY', 'FACT', telemetry_cols, COLORS['compute_orange'])
    
    # COMPLIANCE_DOCS - Reference table
    docs_cols = [
        ('DOC_ID', 'VARCHAR', True, False),
        ('REGULATION_CODE', 'VARCHAR', False, False),
        ('TITLE', 'VARCHAR', False, False),
        ('CONTENT', 'TEXT', False, False),
        ('DOC_TYPE', 'VARCHAR', False, False),
    ]
    draw_table(0.5, 1.5, 3, 2.0, 'COMPLIANCE_DOCS', 'REF', docs_cols, COLORS['cortex_teal'])
    
    # SIMULATION_RESULTS - Output table
    results_cols = [
        ('SIMULATION_ID', 'VARCHAR', True, False),
        ('SCENARIO_NAME', 'VARCHAR', False, False),
        ('NODE_ID', 'VARCHAR', False, True),
        ('FAILURE_PROBABILITY', 'FLOAT', False, False),
        ('IS_PATIENT_ZERO', 'BOOLEAN', False, False),
        ('CASCADE_ORDER', 'INT', False, False),
        ('LOAD_SHED_MW', 'FLOAT', False, False),
    ]
    draw_table(5.5, 1.5, 3, 2.6, 'SIMULATION_RESULTS', 'OUTPUT', results_cols, COLORS['results_purple'])
    
    # MODEL_ARTIFACTS - Metadata table
    artifacts_cols = [
        ('ARTIFACT_ID', 'VARCHAR', True, False),
        ('MODEL_NAME', 'VARCHAR', False, False),
        ('VERSION', 'VARCHAR', False, False),
        ('METRICS', 'VARIANT', False, False),
        ('STATUS', 'VARCHAR', False, False),
    ]
    draw_table(10.5, 1.5, 3, 2.0, 'MODEL_ARTIFACTS', 'REF', artifacts_cols, COLORS['cortex_teal'])
    
    # Draw relationships (arrows)
    arrow_style = dict(arrowstyle='->', color=COLORS['snowflake_blue'], lw=2, 
                      connectionstyle='arc3,rad=0.1')
    
    # GRID_EDGES → GRID_NODES (SRC_NODE)
    ax.annotate('', xy=(5.5, 7.2), xytext=(3.5, 7.2), arrowprops=arrow_style)
    ax.text(4.5, 7.4, 'SRC_NODE', fontsize=7, color=COLORS['snowflake_blue'], ha='center')
    
    # GRID_EDGES → GRID_NODES (DST_NODE)
    ax.annotate('', xy=(5.5, 6.6), xytext=(3.5, 6.6), 
                arrowprops=dict(arrowstyle='->', color=COLORS['snowflake_blue'], lw=2,
                               connectionstyle='arc3,rad=-0.1'))
    ax.text(4.5, 6.3, 'DST_NODE', fontsize=7, color=COLORS['snowflake_blue'], ha='center')
    
    # HISTORICAL_TELEMETRY → GRID_NODES
    ax.annotate('', xy=(8.5, 6.8), xytext=(10.5, 6.8), arrowprops=arrow_style)
    ax.text(9.5, 7.0, 'NODE_ID', fontsize=7, color=COLORS['snowflake_blue'], ha='center')
    
    # SIMULATION_RESULTS → GRID_NODES
    ax.annotate('', xy=(7, 5.5), xytext=(7, 4.1), 
                arrowprops=dict(arrowstyle='->', color=COLORS['snowflake_blue'], lw=2))
    ax.text(7.2, 4.8, 'NODE_ID', fontsize=7, color=COLORS['snowflake_blue'], ha='left')
    
    # Data flow annotation
    flow_text = "Data Flow: Source → GNN Model → Results"
    ax.text(7, 0.7, flow_text, fontsize=10, color=COLORS['text_muted'], ha='center',
            style='italic')
    
    # Legend
    legend_items = [
        ('DIM', 'Dimension', COLORS['data_green']),
        ('FACT', 'Fact Table', COLORS['compute_orange']),
        ('REF', 'Reference', COLORS['cortex_teal']),
        ('OUTPUT', 'Model Output', COLORS['results_purple']),
    ]
    
    legend_x = 11.5
    legend_y = 9.2
    ax.text(legend_x, legend_y, 'Table Types:', fontsize=9, fontweight='bold',
            color=COLORS['text_light'])
    for i, (code, label, color) in enumerate(legend_items):
        ax.plot([legend_x + i * 0.9], [legend_y - 0.35], 's', color=color, markersize=8)
        ax.text(legend_x + 0.15 + i * 0.9, legend_y - 0.35, code, fontsize=7,
                color=COLORS['text_light'], va='center')
    
    # Record counts
    counts_text = "Record Counts:\n"
    counts_text += "GRID_NODES: 45\n"
    counts_text += "GRID_EDGES: 106\n"
    counts_text += "TELEMETRY: 12,960\n"
    counts_text += "COMPLIANCE: 8 docs"
    
    props = dict(boxstyle='round,pad=0.4', facecolor=COLORS['card_bg'], 
                 edgecolor='white', alpha=0.9)
    ax.text(0.7, 9.0, counts_text, fontsize=9, color=COLORS['text_light'],
            va='top', bbox=props, linespacing=1.4, fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'data-erd.png', dpi=150, facecolor=COLORS['background'],
                edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'data-erd.png'}")


def create_compliance_flow():
    """Create a compliance journey visualization showing NERC reporting flow."""
    fig, ax = plt.subplots(figsize=(14, 8), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Title
    ax.text(7, 7.5, 'AI-Assisted Compliance Reporting', fontsize=22,
            fontweight='bold', color=COLORS['text_light'], ha='center')
    ax.text(7, 7.0, 'From Simulation Results to NERC Compliance in Minutes',
            fontsize=13, color=COLORS['cortex_teal'], ha='center')
    
    # Flow steps
    steps = [
        ('Simulation\nComplete', 'GNN identifies\nfailure cascade', COLORS['results_purple'], 1.5),
        ('Impact\nAssessment', 'Load shed, customers,\nrepair costs', COLORS['grid_failed'], 4.5),
        ('Compliance\nQuery', '"What forms do\nI need to file?"', COLORS['cortex_teal'], 7.5),
        ('AI\nResponse', 'NERC requirements\nretrieved via RAG', COLORS['data_green'], 10.5),
    ]
    
    for label, desc, color, x in steps:
        # Box
        box = FancyBboxPatch((x - 1.2, 4.5), 2.4, 2, boxstyle="round,pad=0.05",
                            facecolor=COLORS['card_bg'], edgecolor=color,
                            linewidth=2)
        ax.add_patch(box)
        
        # Label
        ax.text(x, 6, label, fontsize=12, fontweight='bold', color=color,
                ha='center', va='center', linespacing=1.2)
        
        # Description
        ax.text(x, 5, desc, fontsize=9, color=COLORS['text_muted'],
                ha='center', va='center', linespacing=1.2)
        
        # Arrow to next
        if x < 10:
            ax.annotate('', xy=(x + 1.5, 5.5), xytext=(x + 1.0, 5.5),
                       arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Example output panel
    output_box = FancyBboxPatch((1, 0.5), 12, 3.5, boxstyle="round,pad=0.1",
                                facecolor='#1a2634', edgecolor=COLORS['cortex_teal'],
                                linewidth=2)
    ax.add_patch(output_box)
    
    ax.text(7, 3.7, 'Cortex Search Response', fontsize=14, fontweight='bold',
            color=COLORS['cortex_teal'], ha='center')
    
    response_text = '''User: "Based on the simulation showing 847 MW load shed, what NERC reporting is required?"

AI: Based on the WINTER_STORM_2021 simulation results showing 847 MW of load shed affecting
142,500 customers, you are required to file:

  1. NERC EOP-004-4 Event Reporting - Required within 24 hours for events > 300 MW
  2. NERC FAC-003-4 Vegetation Management Report - If transmission line failure involved  
  3. Regional Entity Notification - ERCOT Form within 1 hour of qualifying event

The simulation indicates SUB_007 as Patient Zero. Cross-reference maintenance logs for
this substation against NERC PRC-005-6 protection system maintenance standards.'''
    
    ax.text(1.3, 3.2, response_text, fontsize=9, color=COLORS['text_light'],
            va='top', fontfamily='monospace', linespacing=1.4)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'compliance-flow.png', dpi=150, 
                facecolor=COLORS['background'], edgecolor='none',
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"Created: {OUTPUT_DIR / 'compliance-flow.png'}")


if __name__ == '__main__':
    print("Generating GridGuard Solution Presentation images...")
    print("=" * 50)
    
    # Original images
    create_architecture_diagram()
    create_cascade_network()
    create_patient_zero_visual()
    create_dashboard_preview()
    
    # New business story images
    create_problem_impact()
    create_before_after()
    create_roi_value()
    create_timeline_comparison()
    create_data_erd()
    create_compliance_flow()
    
    print("=" * 50)
    print("All images generated successfully!")
    print(f"Output directory: {OUTPUT_DIR}")

