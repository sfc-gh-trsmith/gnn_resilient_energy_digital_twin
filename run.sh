#!/bin/bash
###############################################################################
# run.sh - Runtime Operations for GridGuard
#
# Commands:
#   main       - Execute the notebook (train model + batch inference)
#   status     - Check status of resources and data
#   streamlit  - Get Streamlit app URL
#   notebook   - Get notebook URL
#
# Usage:
#   ./run.sh main              # Train model and generate all results
#   ./run.sh status            # Check resource status
#   ./run.sh streamlit         # Get Streamlit URL
#   ./run.sh -c prod main      # Use 'prod' connection
###############################################################################

set -e
set -o pipefail

# Configuration
CONNECTION_NAME="demo"
ENV_PREFIX=""
COMMAND=""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Read project prefix from PROJECT_NAME.md and convert to uppercase
PROJECT_NAME_FILE="$SCRIPT_DIR/.cursor/PROJECT_NAME.md"
if [ -f "$PROJECT_NAME_FILE" ]; then
    PROJECT_PREFIX=$(head -1 "$PROJECT_NAME_FILE" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
else
    echo -e "${RED}[ERROR] PROJECT_NAME.md not found at $PROJECT_NAME_FILE${NC}" >&2
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Error handler
error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMMAND

Runtime operations for GridGuard energy grid resilience demo.

Commands:
  main       Train the GNN model and generate all scenario results
  status     Check status of Snowflake resources and data
  streamlit  Get the Streamlit app URL
  notebook   Get the notebook URL

Options:
  -c, --connection NAME    Snowflake CLI connection name (default: demo)
  -p, --prefix PREFIX      Environment prefix for resources (e.g., DEV, PROD)
  -h, --help               Show this help message

Examples:
  $0 main                  # Train model and generate results
  $0 status                # Check resource status
  $0 streamlit             # Get Streamlit URL
  $0 -c prod main          # Use 'prod' connection
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -c|--connection)
            CONNECTION_NAME="$2"
            shift 2
            ;;
        -p|--prefix)
            ENV_PREFIX="$2"
            shift 2
            ;;
        main|status|streamlit|notebook)
            COMMAND="$1"
            shift
            ;;
        *)
            error_exit "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# Require a command
if [ -z "$COMMAND" ]; then
    usage
fi

# Build connection string
SNOW_CONN="-c $CONNECTION_NAME"

# Compute full prefix
if [ -n "$ENV_PREFIX" ]; then
    FULL_PREFIX="${ENV_PREFIX}_${PROJECT_PREFIX}"
else
    FULL_PREFIX="${PROJECT_PREFIX}"
fi

# Derive resource names
DATABASE="${FULL_PREFIX}"
SCHEMA="${PROJECT_PREFIX}"
ROLE="${FULL_PREFIX}_ROLE"
WAREHOUSE="${FULL_PREFIX}_WH"
COMPUTE_POOL="${FULL_PREFIX}_COMPUTE_POOL"
NOTEBOOK_NAME="${FULL_PREFIX}_CASCADE_NOTEBOOK"
STREAMLIT_APP="${FULL_PREFIX}_APP"

###############################################################################
# Command: main - Execute notebook for training and inference
###############################################################################
cmd_main() {
    echo "=================================================="
    echo "GridGuard - Model Training & Inference"
    echo "=================================================="
    echo ""
    echo "This will:"
    echo "  1. Train the GNN model on historical cascade patterns"
    echo "  2. Run batch inference for ALL scenarios"
    echo "  3. Write results to SIMULATION_RESULTS table"
    echo ""
    echo "Configuration:"
    echo "  Database: $DATABASE"
    echo "  Notebook: $NOTEBOOK_NAME"
    echo "  Compute Pool: $COMPUTE_POOL"
    echo ""
    
    # Check compute pool status
    echo "Checking compute pool status..."
    POOL_STATUS=$(snow sql $SNOW_CONN -q "
        SELECT STATE FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) 
        WHERE 1=0;
        SHOW COMPUTE POOLS LIKE '${COMPUTE_POOL}';
    " -o tsv 2>/dev/null | tail -1 | awk '{print $4}') || POOL_STATUS="UNKNOWN"
    
    echo "  Compute Pool State: $POOL_STATUS"
    
    if [ "$POOL_STATUS" = "SUSPENDED" ]; then
        echo "  Resuming compute pool..."
        snow sql $SNOW_CONN -q "ALTER COMPUTE POOL ${COMPUTE_POOL} RESUME;" 2>/dev/null || true
        echo "  Waiting for compute pool to start (this may take 2-5 minutes)..."
        sleep 30
    fi
    
    echo ""
    echo "Executing notebook..."
    echo "------------------------------------------------"
    
    # Execute notebook
    START_TIME=$(date +%s)
    
    snow notebook execute $NOTEBOOK_NAME \
        $SNOW_CONN \
        --database $DATABASE \
        --schema $SCHEMA \
        --role $ROLE 2>&1 || {
            echo -e "${YELLOW}[WARN]${NC} Notebook execution may have encountered issues"
            echo "Check the notebook in Snowsight for details"
        }
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "------------------------------------------------"
    echo -e "${GREEN}[OK]${NC} Notebook execution completed in ${DURATION}s"
    echo ""
    
    # Show results
    echo "Checking results..."
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        USE DATABASE ${DATABASE};
        USE SCHEMA ${SCHEMA};
        
        SELECT SCENARIO_NAME, COUNT(*) AS NODE_COUNT, 
               SUM(CASE WHEN IS_PATIENT_ZERO THEN 1 ELSE 0 END) AS PATIENT_ZERO_COUNT,
               SUM(LOAD_SHED_MW) AS TOTAL_LOAD_SHED_MW,
               SUM(REPAIR_COST) AS TOTAL_REPAIR_COST
        FROM SIMULATION_RESULTS
        GROUP BY SCENARIO_NAME
        ORDER BY SCENARIO_NAME;
    "
    
    echo ""
    echo -e "${GREEN}Model training and inference complete!${NC}"
    echo "Results are now available in SIMULATION_RESULTS table."
    echo ""
    echo "Next: Open the dashboard with ./run.sh streamlit"
}

###############################################################################
# Command: status - Check resource status
###############################################################################
cmd_status() {
    echo "=================================================="
    echo "GridGuard - Status"
    echo "=================================================="
    echo ""
    echo "Configuration:"
    echo "  Database: $DATABASE"
    echo "  Role: $ROLE"
    echo ""
    
    # Check compute pool
    echo "Compute Pool:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "SHOW COMPUTE POOLS LIKE '${COMPUTE_POOL}';" 2>/dev/null || echo "  Not found or no access"
    echo ""
    
    # Check warehouse
    echo "Warehouse:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "SHOW WAREHOUSES LIKE '${WAREHOUSE}';" 2>/dev/null || echo "  Not found or no access"
    echo ""
    
    # Check table row counts
    echo "Table Row Counts:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        USE DATABASE ${DATABASE};
        USE SCHEMA ${SCHEMA};
        
        SELECT 'GRID_NODES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM GRID_NODES
        UNION ALL SELECT 'GRID_EDGES', COUNT(*) FROM GRID_EDGES
        UNION ALL SELECT 'HISTORICAL_TELEMETRY', COUNT(*) FROM HISTORICAL_TELEMETRY
        UNION ALL SELECT 'COMPLIANCE_DOCS', COUNT(*) FROM COMPLIANCE_DOCS
        UNION ALL SELECT 'SIMULATION_RESULTS', COUNT(*) FROM SIMULATION_RESULTS
        ORDER BY TABLE_NAME;
    " 2>/dev/null || echo "  Error querying tables"
    echo ""
    
    # Check simulation results by scenario
    echo "Simulation Results by Scenario:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        USE DATABASE ${DATABASE};
        USE SCHEMA ${SCHEMA};
        
        SELECT * FROM VW_SCENARIO_IMPACT ORDER BY SCENARIO_NAME;
    " 2>/dev/null || echo "  No simulation results yet. Run: ./run.sh main"
    echo ""
    
    # Check notebook
    echo "Notebooks:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        SHOW NOTEBOOKS IN SCHEMA ${DATABASE}.${SCHEMA};
    " 2>/dev/null || echo "  Not found or no access"
    echo ""
    
    # Check Streamlit apps
    echo "Streamlit Apps:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        SHOW STREAMLITS IN SCHEMA ${DATABASE}.${SCHEMA};
    " 2>/dev/null || echo "  Not found or no access"
}

###############################################################################
# Command: streamlit - Get Streamlit URL
###############################################################################
cmd_streamlit() {
    echo "=================================================="
    echo "GridGuard - Streamlit Dashboard"
    echo "=================================================="
    echo ""
    
    # Try to get URL
    URL=$(snow streamlit get-url ${STREAMLIT_APP} \
        $SNOW_CONN \
        --database $DATABASE \
        --schema $SCHEMA \
        --role $ROLE 2>/dev/null) || true
    
    if [ -n "$URL" ]; then
        echo "Streamlit Dashboard URL:"
        echo ""
        echo -e "  ${CYAN}$URL${NC}"
        echo ""
    else
        echo "Could not retrieve URL automatically."
        echo ""
        echo "To open the dashboard:"
        echo "  1. Go to Snowsight (https://app.snowflake.com)"
        echo "  2. Navigate to: Projects > Streamlit"
        echo "  3. Open: ${STREAMLIT_APP}"
        echo ""
        echo "Or use this direct pattern:"
        echo "  https://<account>.snowflakecomputing.com/#/streamlit-apps/${DATABASE}.${SCHEMA}.${STREAMLIT_APP}"
    fi
}

###############################################################################
# Command: notebook - Get notebook URL
###############################################################################
cmd_notebook() {
    echo "=================================================="
    echo "GridGuard - Notebook"
    echo "=================================================="
    echo ""
    
    echo "To open the notebook:"
    echo "  1. Go to Snowsight (https://app.snowflake.com)"
    echo "  2. Navigate to: Projects > Notebooks"
    echo "  3. Open: ${NOTEBOOK_NAME}"
    echo ""
    echo "Or execute headlessly with:"
    echo "  ./run.sh main"
}

###############################################################################
# Execute command
###############################################################################
case $COMMAND in
    main)
        cmd_main
        ;;
    status)
        cmd_status
        ;;
    streamlit)
        cmd_streamlit
        ;;
    notebook)
        cmd_notebook
        ;;
    *)
        error_exit "Unknown command: $COMMAND"
        ;;
esac

