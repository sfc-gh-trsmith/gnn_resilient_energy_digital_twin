# GridGuard - Energy Grid Resilience Digital Twin

A Snowflake-native demo showcasing Graph Neural Networks (GNN) for predicting cascade failures in power grid infrastructure.

## Overview

GridGuard demonstrates how Snowflake's unified data platform enables advanced AI/ML applications for critical infrastructure monitoring. The solution combines:

- **Graph Neural Networks (GNN)** for topology-aware cascade prediction using PyTorch Geometric
- **Snowpark Container Services (SPCS)** for GPU-accelerated model training
- **Cortex AI** for natural language querying and document retrieval
- **Streamlit in Snowflake** for interactive business dashboards

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SNOWFLAKE DATA CLOUD                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│   │  GRID_NODES  │     │  GRID_EDGES  │     │  TELEMETRY   │              │
│   │  (Topology)  │     │ (Connections)│     │ (Time Series)│              │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘              │
│          │                    │                    │                       │
│          └────────────────────┼────────────────────┘                       │
│                               ▼                                            │
│                    ┌──────────────────────┐                                │
│                    │   PyTorch Geometric  │                                │
│                    │   GCN Model (GPU)    │                                │
│                    │   via SPCS Notebook  │                                │
│                    └──────────┬───────────┘                                │
│                               ▼                                            │
│                    ┌──────────────────────┐                                │
│                    │  SIMULATION_RESULTS  │                                │
│                    │  - Patient Zero ID   │                                │
│                    │  - Cascade Order     │                                │
│                    │  - Risk Scores       │                                │
│                    └──────────┬───────────┘                                │
│                               │                                            │
│          ┌────────────────────┼────────────────────┐                       │
│          ▼                    ▼                    ▼                       │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│   │ Cortex       │     │ Cortex       │     │ Streamlit    │              │
│   │ Analyst      │     │ Search       │     │ Dashboard    │              │
│   │ (SQL Q&A)    │     │ (Compliance) │     │ (Business)   │              │
│   └──────────────┘     └──────────────┘     └──────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Snowflake CLI (`snow`) installed: `pip install snowflake-cli`
- Configured Snowflake connection (default: `demo`)

### Deployment

```bash
# 1. Deploy infrastructure and applications
./deploy.sh

# 2. Train the model and generate simulation results
./run.sh main

# 3. Check deployment status
./run.sh status

# 4. Get the Streamlit dashboard URL
./run.sh streamlit
```

### Cleanup

```bash
./clean.sh --force
```

## Project Structure

```
gridguard/
├── data/
│   └── synthetic/                    # Pre-generated demo data
│       ├── grid_nodes.csv            # 45 substations/assets
│       ├── grid_edges.csv            # 106 transmission lines
│       ├── historical_telemetry.csv  # 12,960 time-series records
│       └── compliance_docs.csv       # 8 NERC regulation excerpts
├── notebooks/
│   ├── grid_cascade_analysis.ipynb   # GCN training & inference
│   ├── environment.yml               # PyG dependencies
│   └── snowflake.yml                 # Notebook deployment config
├── sql/
│   ├── 01_account_setup.sql          # Role, DB, WH, compute pool
│   ├── 02_schema_setup.sql           # Tables, stages, views
│   └── 03_cortex_setup.sql           # Cortex Search service
├── cortex/
│   └── semantic_model.yaml           # Cortex Analyst semantic model
├── streamlit/
│   ├── streamlit_app.py              # Landing page
│   ├── pages/
│   │   ├── 1_Data_Foundation.py      # Grid topology visualization
│   │   ├── 2_Simulation_Results.py   # GNN results & network graph
│   │   ├── 3_Key_Insights.py         # Patient Zero discovery
│   │   ├── 4_Take_Action.py          # Cortex Search for compliance
│   │   └── 5_About.py                # Technical documentation
│   ├── utils/
│   │   ├── viz.py                    # Plotly network rendering
│   │   ├── cortex.py                 # Cortex integration
│   │   └── data_loader.py            # Parallel query utility
│   ├── snowflake.yml
│   └── environment.yml
├── utils/
│   └── generate_synthetic_data.py    # Deterministic data generator
├── deploy.sh                          # Deployment script
├── run.sh                             # Runtime operations
├── clean.sh                           # Cleanup script
└── README.md
```

## Key Features

### Graph Neural Network Analysis

- 3-layer Graph Convolutional Network (GCN)
- Trained on historical cascade failure patterns
- Identifies "Patient Zero" - the cascade origin node
- Outputs per-node failure probabilities and risk scores

### Simulation Scenarios

| Scenario | Description |
|----------|-------------|
| BASE_CASE | Normal operating conditions |
| HIGH_LOAD | Peak demand stress test |
| WINTER_STORM_2021 | 2021 Texas winter storm simulation |

### Cortex AI Integration

- **Cortex Search**: RAG over NERC compliance documents
- **Semantic Model**: Natural language queries over simulation results

## Snowflake Objects Created

| Object Type | Name | Description |
|-------------|------|-------------|
| Database | GRIDGUARD | Main project database |
| Schema | GRIDGUARD | Primary schema |
| Role | GRIDGUARD_ROLE | Project access role |
| Warehouse | GRIDGUARD_WH | Query warehouse (XS) |
| Compute Pool | GRIDGUARD_COMPUTE_POOL | GPU pool for PyG |
| Notebook | GRIDGUARD_CASCADE_NOTEBOOK | GCN training notebook |
| Streamlit | GRIDGUARD_APP | Dashboard application |

## Command Reference

### deploy.sh

```bash
./deploy.sh                       # Full deployment
./deploy.sh -c prod               # Use 'prod' connection
./deploy.sh --prefix DEV          # Deploy with DEV_ prefix
./deploy.sh --only-streamlit      # Deploy only Streamlit app
```

### run.sh

```bash
./run.sh main                     # Train model, generate results
./run.sh status                   # Check resource status
./run.sh streamlit                # Get dashboard URL
./run.sh notebook                 # Get notebook URL
```

### clean.sh

```bash
./clean.sh                        # Interactive cleanup
./clean.sh --force                # Non-interactive cleanup
./clean.sh --prefix DEV           # Clean DEV environment
```

## Technical Notes

### Visualization Approach

This demo uses **Plotly + NetworkX** for network visualization instead of PyVis. Snowflake's Content Security Policy (CSP) blocks external JavaScript CDNs required by PyVis, making Plotly the reliable choice for Streamlit in Snowflake.

### Data Generation

All demo data is pre-generated with a fixed random seed (`RANDOM_SEED = 42`) for reproducibility. The data files are version-controlled and uploaded during deployment - no local Python execution is required.

### Execution Model

Model training runs **offline** via `run.sh main` before demo presentation. The Streamlit app displays pre-computed results for instant scenario switching without GPU wait times.

## License

This demo is provided for educational and demonstration purposes.
