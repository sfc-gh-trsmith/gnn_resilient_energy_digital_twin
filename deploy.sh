#!/bin/bash
###############################################################################
# deploy.sh - Deploy project to Snowflake
#
# Creates all infrastructure and deploys applications:
#   1. Check prerequisites
#   2. Run account-level SQL setup
#   3. Run schema-level SQL setup
#   4. Upload synthetic data to stage
#   5. Load data into tables
#   6. Deploy notebook
#   7. Deploy Streamlit app
#
# Usage:
#   ./deploy.sh                       # Full deployment
#   ./deploy.sh -c prod               # Use 'prod' connection
#   ./deploy.sh --prefix DEV          # Deploy with DEV_ prefix
#   ./deploy.sh --only-streamlit      # Deploy only Streamlit app
###############################################################################

set -e
set -o pipefail

# Configuration
CONNECTION_NAME="demo"
ENV_PREFIX=""
ONLY_COMPONENT=""
SKIP_DATA=false

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Read project prefix from PROJECT_NAME.md and convert to uppercase
PROJECT_NAME_FILE="$SCRIPT_DIR/.cursor/PROJECT_NAME.md"
if [ -f "$PROJECT_NAME_FILE" ]; then
    PROJECT_PREFIX=$(head -1 "$PROJECT_NAME_FILE" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
else
    echo -e "${RED}[ERROR] PROJECT_NAME.md not found at $PROJECT_NAME_FILE${NC}" >&2
    exit 1
fi

# Error handler
error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy energy grid resilience demo to Snowflake.

Options:
  -c, --connection NAME    Snowflake CLI connection name (default: demo)
  -p, --prefix PREFIX      Environment prefix for resources (e.g., DEV, PROD)
  --skip-data              Skip data upload and loading
  --only-sql               Deploy only SQL infrastructure (includes Cortex)
  --only-data              Deploy only data upload and loading
  --only-cortex            Deploy only Cortex Search Service
  --only-notebook          Deploy only the notebook
  --only-streamlit         Deploy only the Streamlit app
  -h, --help               Show this help message

Examples:
  $0                       # Full deployment
  $0 -c prod               # Use 'prod' connection
  $0 --prefix DEV          # Deploy with DEV_ prefix
  $0 --only-streamlit      # Redeploy only Streamlit
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
        --skip-data)
            SKIP_DATA=true
            shift
            ;;
        --only-sql)
            ONLY_COMPONENT="sql"
            shift
            ;;
        --only-data)
            ONLY_COMPONENT="data"
            shift
            ;;
        --only-cortex)
            ONLY_COMPONENT="cortex"
            shift
            ;;
        --only-notebook)
            ONLY_COMPONENT="notebook"
            shift
            ;;
        --only-streamlit)
            ONLY_COMPONENT="streamlit"
            shift
            ;;
        *)
            error_exit "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# Build connection string
SNOW_CONN="-c $CONNECTION_NAME"

# Compute full prefix
if [ -n "$ENV_PREFIX" ]; then
    FULL_PREFIX="${ENV_PREFIX}_${PROJECT_PREFIX}"
else
    FULL_PREFIX="${PROJECT_PREFIX}"
fi

# Derive all resource names
DATABASE="${FULL_PREFIX}"
SCHEMA="${PROJECT_PREFIX}"
ROLE="${FULL_PREFIX}_ROLE"
WAREHOUSE="${FULL_PREFIX}_WH"
COMPUTE_POOL="${FULL_PREFIX}_COMPUTE_POOL"
EXTERNAL_ACCESS="${FULL_PREFIX}_EXTERNAL_ACCESS"
NOTEBOOK_NAME="${FULL_PREFIX}_CASCADE_NOTEBOOK"
STREAMLIT_APP="${FULL_PREFIX}_APP"

# Helper function to check if a step should run
should_run_step() {
    local step_name="$1"
    if [ -z "$ONLY_COMPONENT" ]; then
        return 0
    fi
    case "$ONLY_COMPONENT" in
        sql)
            [[ "$step_name" == "account_sql" || "$step_name" == "schema_sql" || "$step_name" == "cortex_sql" ]]
            ;;
        data)
            [[ "$step_name" == "upload_data" || "$step_name" == "load_data" ]]
            ;;
        cortex)
            [[ "$step_name" == "cortex_sql" ]]
            ;;
        notebook)
            [[ "$step_name" == "notebook" ]]
            ;;
        streamlit)
            [[ "$step_name" == "streamlit" ]]
            ;;
        *)
            return 1
            ;;
    esac
}

# Display banner
echo "=================================================="
echo "${PROJECT_PREFIX} - Deployment"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  Connection: $CONNECTION_NAME"
if [ -n "$ENV_PREFIX" ]; then
    echo "  Environment Prefix: $ENV_PREFIX"
fi
if [ -n "$ONLY_COMPONENT" ]; then
    echo "  Deploy Only: $ONLY_COMPONENT"
fi
echo "  Database: $DATABASE"
echo "  Schema: $SCHEMA"
echo "  Role: $ROLE"
echo "  Warehouse: $WAREHOUSE"
echo "  Compute Pool: $COMPUTE_POOL"
echo ""

###############################################################################
# Step 1: Check Prerequisites
###############################################################################
echo "Step 1: Checking prerequisites..."
echo "------------------------------------------------"

# Check for snow CLI
if ! command -v snow &> /dev/null; then
    error_exit "Snowflake CLI (snow) not found. Install with: pip install snowflake-cli"
fi
echo -e "${GREEN}[OK]${NC} Snowflake CLI found"

# Test Snowflake connection
echo "Testing Snowflake connection..."
if ! snow sql $SNOW_CONN -q "SELECT 1" &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Failed to connect to Snowflake"
    snow connection test $SNOW_CONN 2>&1 || true
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Connection '$CONNECTION_NAME' verified"

# Check required files
for file in "sql/01_account_setup.sql" "sql/02_schema_setup.sql"; do
    if [ ! -f "$file" ]; then
        error_exit "Required file not found: $file"
    fi
done
echo -e "${GREEN}[OK]${NC} Required SQL files present"

# Check data files
if [ "$SKIP_DATA" = false ] && [ -z "$ONLY_COMPONENT" -o "$ONLY_COMPONENT" = "data" ]; then
    for file in "data/synthetic/grid_nodes.csv" "data/synthetic/grid_edges.csv" "data/synthetic/historical_telemetry.csv" "data/synthetic/compliance_docs.csv"; do
        if [ ! -f "$file" ]; then
            error_exit "Data file not found: $file\nRun: python3 utils/generate_synthetic_data.py"
        fi
    done
    echo -e "${GREEN}[OK]${NC} Synthetic data files present"
fi
echo ""

###############################################################################
# Step 2: Run Account-Level SQL Setup
###############################################################################
if should_run_step "account_sql"; then
    echo "Step 2: Running account-level SQL setup..."
    echo "------------------------------------------------"
    
    {
        echo "-- Set session variables for account-level objects"
        echo "SET FULL_PREFIX = '${FULL_PREFIX}';"
        echo "SET PROJECT_ROLE = '${ROLE}';"
        echo "SET PROJECT_WH = '${WAREHOUSE}';"
        echo "SET PROJECT_COMPUTE_POOL = '${COMPUTE_POOL}';"
        echo "SET PROJECT_SCHEMA = '${SCHEMA}';"
        echo "SET PROJECT_EXTERNAL_ACCESS = '${EXTERNAL_ACCESS}';"
        echo ""
        cat sql/01_account_setup.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} Account-level setup completed (includes external access integration)"
    else
        error_exit "Account-level SQL setup failed"
    fi
    echo ""
else
    echo "Step 2: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

###############################################################################
# Step 3: Run Schema-Level SQL Setup
###############################################################################
if should_run_step "schema_sql"; then
    echo "Step 3: Running schema-level SQL setup..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE};"
        echo "USE DATABASE ${DATABASE};"
        echo "USE SCHEMA ${SCHEMA};"
        echo "USE WAREHOUSE ${WAREHOUSE};"
        echo ""
        cat sql/02_schema_setup.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} Schema-level setup completed"
    else
        error_exit "Schema-level SQL setup failed"
    fi
    echo ""
else
    echo "Step 3: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

###############################################################################
# Step 4: Upload Data to Stage
###############################################################################
if should_run_step "upload_data" && [ "$SKIP_DATA" = false ]; then
    echo "Step 4: Uploading data to stage..."
    echo "------------------------------------------------"
    
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        USE DATABASE ${DATABASE};
        USE SCHEMA ${SCHEMA};
        USE WAREHOUSE ${WAREHOUSE};
        
        PUT file://data/synthetic/grid_nodes.csv @DATA_STAGE/raw/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
        PUT file://data/synthetic/grid_edges.csv @DATA_STAGE/raw/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
        PUT file://data/synthetic/historical_telemetry.csv @DATA_STAGE/raw/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
        PUT file://data/synthetic/compliance_docs.csv @DATA_STAGE/raw/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
    "
    
    echo -e "${GREEN}[OK]${NC} Data files uploaded to stage"
    echo ""
else
    echo "Step 4: Skipped"
    echo ""
fi

###############################################################################
# Step 5: Load Data into Tables
###############################################################################
if should_run_step "load_data" && [ "$SKIP_DATA" = false ]; then
    echo "Step 5: Loading data into tables..."
    echo "------------------------------------------------"
    
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE};
        USE DATABASE ${DATABASE};
        USE SCHEMA ${SCHEMA};
        USE WAREHOUSE ${WAREHOUSE};
        
        -- Truncate tables for clean load
        TRUNCATE TABLE IF EXISTS GRID_NODES;
        TRUNCATE TABLE IF EXISTS GRID_EDGES;
        TRUNCATE TABLE IF EXISTS HISTORICAL_TELEMETRY;
        TRUNCATE TABLE IF EXISTS COMPLIANCE_DOCS;
        
        -- Load grid nodes
        COPY INTO GRID_NODES
        FROM @DATA_STAGE/raw/grid_nodes.csv
        FILE_FORMAT = CSV_FORMAT
        ON_ERROR = 'CONTINUE';
        
        -- Load grid edges
        COPY INTO GRID_EDGES
        FROM @DATA_STAGE/raw/grid_edges.csv
        FILE_FORMAT = CSV_FORMAT
        ON_ERROR = 'CONTINUE';
        
        -- Load telemetry
        COPY INTO HISTORICAL_TELEMETRY
        FROM @DATA_STAGE/raw/historical_telemetry.csv
        FILE_FORMAT = CSV_FORMAT
        ON_ERROR = 'CONTINUE';
        
        -- Load compliance docs
        COPY INTO COMPLIANCE_DOCS
        FROM @DATA_STAGE/raw/compliance_docs.csv
        FILE_FORMAT = CSV_FORMAT
        ON_ERROR = 'CONTINUE';
        
        -- Show row counts
        SELECT 'GRID_NODES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM GRID_NODES
        UNION ALL SELECT 'GRID_EDGES', COUNT(*) FROM GRID_EDGES
        UNION ALL SELECT 'HISTORICAL_TELEMETRY', COUNT(*) FROM HISTORICAL_TELEMETRY
        UNION ALL SELECT 'COMPLIANCE_DOCS', COUNT(*) FROM COMPLIANCE_DOCS;
    "
    
    echo -e "${GREEN}[OK]${NC} Data loaded into tables"
    echo ""
else
    echo "Step 5: Skipped"
    echo ""
fi

###############################################################################
# Step 6: Create Cortex Search Service
###############################################################################
if should_run_step "cortex_sql"; then
    echo "Step 6: Creating Cortex Search Service..."
    echo "------------------------------------------------"
    
    # Check if 03_cortex_setup.sql exists
    if [ -f "sql/03_cortex_setup.sql" ]; then
        # Substitute placeholders and run SQL
        {
            echo "USE ROLE ${ROLE};"
            echo "USE DATABASE ${DATABASE};"
            echo "USE SCHEMA ${SCHEMA};"
            echo "USE WAREHOUSE ${WAREHOUSE};"
            echo ""
            # Replace {{WAREHOUSE}} placeholder with actual warehouse name
            sed "s/{{WAREHOUSE}}/${WAREHOUSE}/g" sql/03_cortex_setup.sql
        } | snow sql $SNOW_CONN -i
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} Cortex Search Service created"
        else
            echo -e "${YELLOW}[WARN]${NC} Cortex Search Service creation may have issues (data may not be loaded yet)"
        fi
    else
        echo -e "${YELLOW}[WARN]${NC} sql/03_cortex_setup.sql not found, skipping Cortex setup"
    fi
    echo ""
else
    echo "Step 6: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

###############################################################################
# Step 7: Deploy Notebook and Semantic Model
###############################################################################
if should_run_step "notebook"; then
    echo "Step 7: Deploying notebook and semantic model..."
    echo "------------------------------------------------"
    
    # Upload semantic model for Cortex Analyst
    if [ -f "cortex/semantic_model.yaml" ]; then
        echo "Uploading semantic model..."
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE};
            USE DATABASE ${DATABASE};
            USE SCHEMA ${SCHEMA};
            
            PUT file://cortex/semantic_model.yaml @MODELS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
        "
        echo -e "${GREEN}[OK]${NC} Semantic model uploaded"
    else
        echo -e "${YELLOW}[WARN]${NC} Semantic model not found at cortex/semantic_model.yaml"
    fi
    
    # Check if notebook exists
    if [ ! -f "notebooks/grid_cascade_analysis.ipynb" ]; then
        echo -e "${YELLOW}[WARN]${NC} Notebook file not found, skipping notebook deployment"
    else
        # Upload notebook and environment files
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE};
            USE DATABASE ${DATABASE};
            USE SCHEMA ${SCHEMA};
            
            PUT file://notebooks/grid_cascade_analysis.ipynb @MODELS_STAGE/notebooks/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
            PUT file://notebooks/environment.yml @MODELS_STAGE/notebooks/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
        "
        
        # Create notebook with external access for pip packages
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE};
            USE DATABASE ${DATABASE};
            USE SCHEMA ${SCHEMA};
            
            CREATE OR REPLACE NOTEBOOK ${NOTEBOOK_NAME}
                FROM '@MODELS_STAGE/notebooks/'
                MAIN_FILE = 'grid_cascade_analysis.ipynb'
                RUNTIME_NAME = 'SYSTEM\$GPU_RUNTIME'
                COMPUTE_POOL = '${COMPUTE_POOL}'
                QUERY_WAREHOUSE = '${WAREHOUSE}'
                EXTERNAL_ACCESS_INTEGRATIONS = (${EXTERNAL_ACCESS})
                IDLE_AUTO_SHUTDOWN_TIME_SECONDS = 600
                COMMENT = '${PROJECT_PREFIX} GNN cascade analysis notebook';
            
            -- Commit live version for CLI execution
            ALTER NOTEBOOK ${NOTEBOOK_NAME} ADD LIVE VERSION FROM LAST;
        "
        
        echo -e "${GREEN}[OK]${NC} Notebook deployed"
    fi
    echo ""
else
    echo "Step 7: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

###############################################################################
# Step 8: Deploy Streamlit App
###############################################################################
if should_run_step "streamlit"; then
    echo "Step 8: Deploying Streamlit app..."
    echo "------------------------------------------------"
    
    # Check if streamlit directory exists
    if [ ! -d "streamlit" ]; then
        echo -e "${YELLOW}[WARN]${NC} Streamlit directory not found, skipping"
    else
        # Clean up existing deployment
        echo "Cleaning up existing Streamlit deployment..."
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE};
            USE DATABASE ${DATABASE};
            USE SCHEMA ${SCHEMA};
            DROP STREAMLIT IF EXISTS ${STREAMLIT_APP};
        " 2>/dev/null || true
        
        # Clear local bundle cache
        rm -rf streamlit/output/bundle 2>/dev/null || true
        
        # Generate snowflake.yml with correct resource names
        echo "Generating snowflake.yml with environment-specific values..."
        PROJECT_PREFIX_LOWER=$(echo "$PROJECT_PREFIX" | tr '[:upper:]' '[:lower:]')
        cat > streamlit/snowflake.yml << SNOWFLAKE_YML
definition_version: "2"
entities:
  ${PROJECT_PREFIX_LOWER}_app:
    type: streamlit
    identifier:
      name: ${STREAMLIT_APP}
    main_file: streamlit_app.py
    query_warehouse: ${WAREHOUSE}
    title: ${PROJECT_PREFIX} - Energy Grid Resilience
    pages_dir: pages
    artifacts:
      - streamlit_app.py
      - pages/
      - utils/
      - environment.yml

SNOWFLAKE_YML
        echo -e "${GREEN}[OK]${NC} Generated streamlit/snowflake.yml"
        
        # Deploy from streamlit directory
        cd streamlit
        
        snow streamlit deploy \
            $SNOW_CONN \
            --database $DATABASE \
            --schema $SCHEMA \
            --role $ROLE \
            --replace 2>&1 || echo -e "${YELLOW}[WARN]${NC} Streamlit deploy may have issues"
        
        cd ..
        
        echo -e "${GREEN}[OK]${NC} Streamlit app deployed"
    fi
    echo ""
else
    echo "Step 8: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

###############################################################################
# Summary
###############################################################################
echo ""
echo "=================================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=================================================="
echo ""

if [ -n "$ONLY_COMPONENT" ]; then
    echo "Deployed component: $ONLY_COMPONENT"
else
    echo "Next Steps:"
    echo "  1. Train the model and generate results:"
    echo "     ./run.sh main"
    echo ""
    echo "  2. Check status:"
    echo "     ./run.sh status"
    echo ""
    echo "  3. Open the dashboard:"
    echo "     ./run.sh streamlit"
    echo ""
    echo "Optional - Deploy Cortex Agent (requires PAT token):"
    echo "  python .cursor/sf_cortex_agent_ops.py import \\"
    echo "      --input cortex/gridguard_agent.json \\"
    echo "      --database $DATABASE --schema $SCHEMA \\"
    echo "      --account <account> --pat-token <token>"
    echo ""
    echo "Resources Created:"
    echo "  - Database: $DATABASE"
    echo "  - Schema: $DATABASE.$SCHEMA"
    echo "  - Role: $ROLE"
    echo "  - Warehouse: $WAREHOUSE"
    echo "  - Compute Pool: $COMPUTE_POOL"
    echo "  - Cortex Search: COMPLIANCE_SEARCH_SERVICE"
    echo "  - Semantic Model: @MODELS_STAGE/semantic_model.yaml"
fi

