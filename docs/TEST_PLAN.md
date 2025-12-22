# GridGuard - Full Test Cycle Plan

This document provides a comprehensive test plan for the GridGuard Energy Grid Resilience Digital Twin project. It follows the methodology outlined in [SNOWFLAKE_DEMO_FULL_TEST_CYCLE.md](../.cursor/SNOWFLAKE_DEMO_FULL_TEST_CYCLE.md).

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Test Cycle Phases](#2-test-cycle-phases)
3. [Quick Diagnostic Commands](#3-quick-diagnostic-commands)
4. [Common Issues & Recovery](#4-common-issues--recovery)
5. [Full Test Cycle Commands](#5-full-test-cycle-commands)
6. [Success Criteria](#6-success-criteria)
7. [Test Automation Script](#7-test-automation-script)

---

## 1. Project Overview

**Project:** GridGuard - Energy Grid Resilience Digital Twin  
**Purpose:** Simulate grid cascade failures using PyTorch Geometric GNN on Snowflake SPCS

### The "Wow" Moment (from DRD)

> The user selects a historical "Storm Event" from a dropdown. The system instantly reconstructs the grid topology for that timeframe, runs the PyTorch Geometric model (on-demand via SPCS) to identify the "Patient Zero" node that caused the cascade, and Cortex Analyst generates a SQL-backed report on the financial impact.

### Components Inventory

| Component | Type | Resource Name |
|-----------|------|---------------|
| Role | Account-level | `GRIDGUARD_ROLE` |
| Database | Account-level | `GRIDGUARD` |
| Schema | Database-level | `GRIDGUARD.GRIDGUARD` |
| Warehouse | Account-level | `GRIDGUARD_WH` |
| Compute Pool | Account-level (GPU) | `GRIDGUARD_COMPUTE_POOL` |
| External Access | Account-level | `GRIDGUARD_EXTERNAL_ACCESS` |
| Network Rule | Schema-level | `GRIDGUARD_EGRESS_RULE` |
| Notebook | Schema-level | `GRIDGUARD_CASCADE_NOTEBOOK` |
| Streamlit App | Schema-level | `GRIDGUARD_APP` |
| Cortex Search | Schema-level | `COMPLIANCE_SEARCH_SERVICE` |

### Data Tables

| Table | Type | Purpose | Expected Rows |
|-------|------|---------|---------------|
| `GRID_NODES` | Dimension | Substations and assets | ~50 nodes |
| `GRID_EDGES` | Dimension | Transmission lines | ~100 edges |
| `HISTORICAL_TELEMETRY` | Fact | Time-series sensor data | ~5,000+ records |
| `COMPLIANCE_DOCS` | RAG Source | Regulatory documents | ~20 documents |
| `SIMULATION_RESULTS` | Output | GNN cascade analysis | ~150+ (after notebook) |
| `MODEL_ARTIFACTS` | Metadata | Trained model tracking | Variable |

### Views

| View | Purpose |
|------|---------|
| `VW_SCENARIO_SUMMARY` | Aggregate telemetry by scenario |
| `VW_CASCADE_ANALYSIS` | Detailed cascade results with node info |
| `VW_SCENARIO_IMPACT` | Impact summary per scenario |

### Three-Script Model

| Script | Purpose | Typical Duration |
|--------|---------|------------------|
| `clean.sh` | Remove all project resources | 15-60 seconds |
| `deploy.sh` | Create infrastructure and load data | 3-10 minutes |
| `run.sh` | Execute notebook, check status, get URLs | Varies |

### Cursor AI Execution Requirements

When running the test cycle through Cursor AI, all commands must run **outside the sandbox** because they require:
- Network access to communicate with Snowflake
- File system access to upload data to stages
- Git state access for some operations

**Required permissions for Cursor AI:**
```
required_permissions: ["all"]
```

This disables the sandbox entirely and allows full network and filesystem access needed for Snowflake CLI operations.

**Example Cursor AI command execution:**
```
./clean.sh --force    # Requires: network (Snowflake API calls)
./deploy.sh           # Requires: network + filesystem (stage uploads)
./run.sh main         # Requires: network (notebook execution)
./run.sh status       # Requires: network (Snowflake queries)
```

> **Note:** When asking Cursor AI to run a full test cycle, specify "run outside sandbox" or the commands may fail due to network restrictions.

---

## 2. Test Cycle Phases

### Phase 1: Clean Slate (Estimated: 30s)

**Command:**
```bash
./clean.sh --force
```

**Verification Checklist:**

| Step | What's Removed | Expected Output |
|------|----------------|-----------------|
| 1 | Compute Pool stopped & dropped | `[OK]` or `[WARN]` (if not exists) |
| 2 | Warehouse dropped | `[OK]` or `[WARN]` |
| 3 | External Access Integration dropped | `[OK]` or `[WARN]` |
| 4 | Database dropped (cascades all objects) | `[OK]` or `[WARN]` |
| 5 | Role dropped | `[OK]` or `[WARN]` |

**Post-Clean Validation:**
```bash
# Verify compute pool removed
snow sql -c demo -q "SHOW COMPUTE POOLS LIKE 'GRIDGUARD%';"
# Expected: Empty result

# Verify database removed
snow sql -c demo -q "SHOW DATABASES LIKE 'GRIDGUARD%';"
# Expected: Empty result

# Verify role removed
snow sql -c demo -q "SHOW ROLES LIKE 'GRIDGUARD%';"
# Expected: Empty result
```

---

### Phase 2: Deploy Infrastructure (Estimated: 3-8 min)

**Command:**
```bash
./deploy.sh
```

#### Step 2a: Prerequisites Check

| Check | How to Verify | Expected |
|-------|---------------|----------|
| Snowflake CLI | `snow --version` | Version printed |
| Connection | `snow connection test -c demo` | Success |
| SQL files exist | File check | All 3 SQL files present |
| Data files exist | File check | 4 CSV files in `data/synthetic/` |

**Regenerate synthetic data if missing:**
```bash
python3 utils/generate_synthetic_data.py
```

#### Step 2b: Account-Level Setup (01_account_setup.sql)

```bash
# Verify role created
snow sql -c demo -q "SHOW ROLES LIKE 'GRIDGUARD_ROLE';"
# Expected: 1 row

# Verify database created
snow sql -c demo -q "SHOW DATABASES LIKE 'GRIDGUARD';"
# Expected: 1 row

# Verify warehouse created
snow sql -c demo -q "SHOW WAREHOUSES LIKE 'GRIDGUARD_WH';"
# Expected: 1 row, state STARTED or SUSPENDED

# Verify compute pool created
snow sql -c demo -q "DESCRIBE COMPUTE POOL GRIDGUARD_COMPUTE_POOL;"
# Expected: State = IDLE, STARTING, or ACTIVE

# Verify external access integration created
snow sql -c demo -q "SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'GRIDGUARD%';"
# Expected: 1 row

# Verify network rule created
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW NETWORK RULES IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 1 row (GRIDGUARD_EGRESS_RULE)
```

#### Step 2c: Schema-Level Setup (02_schema_setup.sql)

```bash
# Verify tables created
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW TABLES IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 6 tables:
#   - GRID_NODES
#   - GRID_EDGES
#   - HISTORICAL_TELEMETRY
#   - COMPLIANCE_DOCS
#   - SIMULATION_RESULTS
#   - MODEL_ARTIFACTS

# Verify views created
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW VIEWS IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 3 views:
#   - VW_SCENARIO_SUMMARY
#   - VW_CASCADE_ANALYSIS
#   - VW_SCENARIO_IMPACT

# Verify stages created
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW STAGES IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 2 stages:
#   - DATA_STAGE
#   - MODELS_STAGE

# Verify file format created
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW FILE FORMATS IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: CSV_FORMAT
```

#### Step 2d: Data Upload & Loading

```bash
# Verify staged files
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    LIST @GRIDGUARD.GRIDGUARD.DATA_STAGE/raw/;
"
# Expected: 4 files:
#   - grid_nodes.csv
#   - grid_edges.csv
#   - historical_telemetry.csv
#   - compliance_docs.csv

# Verify row counts
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    USE DATABASE GRIDGUARD;
    USE SCHEMA GRIDGUARD;
    
    SELECT 'GRID_NODES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM GRID_NODES
    UNION ALL SELECT 'GRID_EDGES', COUNT(*) FROM GRID_EDGES
    UNION ALL SELECT 'HISTORICAL_TELEMETRY', COUNT(*) FROM HISTORICAL_TELEMETRY
    UNION ALL SELECT 'COMPLIANCE_DOCS', COUNT(*) FROM COMPLIANCE_DOCS
    ORDER BY TABLE_NAME;
"
# Expected: Non-zero counts for all 4 tables
```

#### Step 2e: Notebook Deployment

```bash
# Verify notebook exists
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW NOTEBOOKS IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 1 notebook (GRIDGUARD_CASCADE_NOTEBOOK)

# Verify notebook has live version
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    DESCRIBE NOTEBOOK GRIDGUARD.GRIDGUARD.GRIDGUARD_CASCADE_NOTEBOOK;
"
# Expected: LIVE_VERSION is not NULL
```

#### Step 2f: Streamlit Deployment

```bash
# Verify Streamlit app exists
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SHOW STREAMLITS IN SCHEMA GRIDGUARD.GRIDGUARD;
"
# Expected: 1 app (GRIDGUARD_APP)

# Get Streamlit URL
./run.sh streamlit
```

---

### Phase 3: Execute Workflow (Estimated: 2-15 min)

**Command:**
```bash
./run.sh main
```

#### Pre-Execution Check

```bash
# Verify compute pool is ready for notebook execution
snow sql -c demo -q "DESCRIBE COMPUTE POOL GRIDGUARD_COMPUTE_POOL;"
# Expected: STATE = 'ACTIVE' or 'IDLE'

# If SUSPENDED, it will auto-resume, but you can manually trigger:
snow sql -c demo -q "ALTER COMPUTE POOL GRIDGUARD_COMPUTE_POOL RESUME;"
```

#### Notebook Execution Checkpoints

| Checkpoint | Verification | Expected |
|------------|--------------|----------|
| Notebook starts | CLI output | "Executing notebook..." message |
| PyG installs | Notebook logs | PyTorch Geometric installed successfully |
| Data loads | Notebook logs | Grid topology loaded |
| Model trains | Notebook logs | Training epochs complete |
| Inference runs | Notebook logs | Scenarios processed |
| Results written | Table query | `SIMULATION_RESULTS` populated |
| Execution completes | CLI exit code | 0 (success) |

#### Post-Execution Validation

```bash
# Check simulation results were generated
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    USE DATABASE GRIDGUARD;
    USE SCHEMA GRIDGUARD;
    
    SELECT SCENARIO_NAME, 
           COUNT(*) AS NODE_COUNT,
           SUM(CASE WHEN IS_PATIENT_ZERO THEN 1 ELSE 0 END) AS PATIENT_ZERO_COUNT,
           SUM(LOAD_SHED_MW) AS TOTAL_LOAD_SHED_MW,
           SUM(REPAIR_COST) AS TOTAL_REPAIR_COST
    FROM SIMULATION_RESULTS
    GROUP BY SCENARIO_NAME
    ORDER BY SCENARIO_NAME;
"
# Expected: 3 scenarios with results:
#   - BASE_CASE
#   - HIGH_LOAD
#   - WINTER_STORM_2021
# Each should have NODE_COUNT > 0 and exactly 1 PATIENT_ZERO

# Verify cascade analysis view works
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SELECT * FROM GRIDGUARD.GRIDGUARD.VW_SCENARIO_IMPACT;
"
# Expected: Summary stats for each scenario

# Check Patient Zero nodes are identified
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SELECT sr.SCENARIO_NAME, sr.NODE_ID, gn.NODE_NAME, gn.REGION, sr.FAILURE_PROBABILITY
    FROM GRIDGUARD.GRIDGUARD.SIMULATION_RESULTS sr
    JOIN GRIDGUARD.GRIDGUARD.GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
    WHERE sr.IS_PATIENT_ZERO = TRUE;
"
# Expected: One Patient Zero per scenario
```

---

### Phase 4: Verify Applications

#### 4a: Streamlit App Accessibility

```bash
./run.sh streamlit
```

**Manual Verification Checklist:**

| Page | URL Path | Verification | Expected Behavior |
|------|----------|--------------|-------------------|
| Home | `/` | Load without errors | Title "GridGuard" visible |
| Data Foundation | `/1_Data_Foundation` | Tables display | Node/Edge counts shown |
| Simulation Results | `/2_Simulation_Results` | Chart renders | Cascade visualization with failed nodes |
| Key Insights | `/3_Key_Insights` | Metrics display | Load shed, cost totals, Patient Zero ID |
| Take Action | `/4_Take_Action` | Chat works | Cortex responds to queries |
| About | `/5_About` | Content displays | Project description |

#### 4b: Cortex Search Service

```bash
# Deploy Cortex Search if not already done (run 03_cortex_setup.sql)
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    USE DATABASE GRIDGUARD;
    USE SCHEMA GRIDGUARD;
    USE WAREHOUSE GRIDGUARD_WH;
"
snow sql -c demo -f sql/03_cortex_setup.sql

# Test Cortex Search
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SELECT * FROM TABLE(
        GRIDGUARD.GRIDGUARD.COMPLIANCE_SEARCH_SERVICE!SEARCH(
            QUERY => 'voltage collapse reporting requirements',
            COLUMNS => ['REGULATION_CODE', 'TITLE', 'CONTENT'],
            TOP_K => 3
        )
    );
"
# Expected: Relevant compliance documents returned
```

#### 4c: Semantic Model Verification (Cortex Analyst)

The semantic model at `cortex/semantic_model.yaml` defines queries for Cortex Analyst. Verify the golden queries:

```bash
# Golden Query 1: Total repair cost by scenario
snow sql -c demo -q "
    SELECT SCENARIO_NAME, SUM(REPAIR_COST) as TOTAL_REPAIR_COST
    FROM GRIDGUARD.GRIDGUARD.SIMULATION_RESULTS
    GROUP BY SCENARIO_NAME
    ORDER BY TOTAL_REPAIR_COST DESC;
"

# Golden Query 2: Failed substations in winter storm
snow sql -c demo -q "
    SELECT SUM(sr.REPAIR_COST) as TOTAL_REPAIR_COST
    FROM GRIDGUARD.GRIDGUARD.SIMULATION_RESULTS sr
    JOIN GRIDGUARD.GRIDGUARD.GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
    WHERE sr.SCENARIO_NAME = 'WINTER_STORM_2021'
      AND sr.CASCADE_ORDER IS NOT NULL;
"

# Golden Query 3: Customers impacted by region
snow sql -c demo -q "
    SELECT gn.REGION, SUM(sr.CUSTOMERS_IMPACTED) as TOTAL_CUSTOMERS
    FROM GRIDGUARD.GRIDGUARD.SIMULATION_RESULTS sr
    JOIN GRIDGUARD.GRIDGUARD.GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
    WHERE sr.SCENARIO_NAME = 'WINTER_STORM_2021'
    GROUP BY gn.REGION
    ORDER BY TOTAL_CUSTOMERS DESC;
"
```

---

## 3. Quick Diagnostic Commands

### Status Overview
```bash
./run.sh status
```

### Connection Verification
```bash
snow sql -c demo -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();"
```

### Resource Health Check
```bash
# Compute pool state
snow sql -c demo -q "DESCRIBE COMPUTE POOL GRIDGUARD_COMPUTE_POOL;"

# Warehouse state  
snow sql -c demo -q "SHOW WAREHOUSES LIKE 'GRIDGUARD_WH';"

# All project resources
snow sql -c demo -q "
    SHOW COMPUTE POOLS LIKE 'GRIDGUARD%';
    SHOW DATABASES LIKE 'GRIDGUARD%';
    SHOW ROLES LIKE 'GRIDGUARD%';
"
```

### Data Integrity Check
```bash
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    USE DATABASE GRIDGUARD;
    USE SCHEMA GRIDGUARD;
    
    -- Check foreign key integrity (orphaned edges)
    SELECT 'ORPHAN_EDGES_SRC' AS CHECK_TYPE, COUNT(*) AS COUNT
    FROM GRID_EDGES e
    LEFT JOIN GRID_NODES n ON e.SRC_NODE = n.NODE_ID
    WHERE n.NODE_ID IS NULL
    
    UNION ALL
    
    SELECT 'ORPHAN_EDGES_DST', COUNT(*)
    FROM GRID_EDGES e
    LEFT JOIN GRID_NODES n ON e.DST_NODE = n.NODE_ID
    WHERE n.NODE_ID IS NULL
    
    UNION ALL
    
    -- Check orphaned telemetry
    SELECT 'ORPHAN_TELEMETRY', COUNT(*)
    FROM HISTORICAL_TELEMETRY t
    LEFT JOIN GRID_NODES n ON t.NODE_ID = n.NODE_ID
    WHERE n.NODE_ID IS NULL
    
    UNION ALL
    
    -- Check orphaned simulation results
    SELECT 'ORPHAN_RESULTS', COUNT(*)
    FROM SIMULATION_RESULTS sr
    LEFT JOIN GRID_NODES n ON sr.NODE_ID = n.NODE_ID
    WHERE n.NODE_ID IS NULL;
"
# Expected: All counts = 0
```

### Notebook Logs
```bash
# Check notebook execution history (if available)
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SELECT * FROM GRIDGUARD.GRIDGUARD.MODEL_ARTIFACTS
    ORDER BY CREATED_AT DESC
    LIMIT 5;
"
```

---

## 4. Common Issues & Recovery

### Issue: Compute Pool Won't Start

**Symptoms:** 
- Stuck in `STARTING` state for > 10 minutes
- Notebook execution times out

**Diagnosis:**
```bash
snow sql -c demo -q "DESCRIBE COMPUTE POOL GRIDGUARD_COMPUTE_POOL;"
```

**Recovery:**
```bash
# If suspended, manually resume
snow sql -c demo -q "ALTER COMPUTE POOL GRIDGUARD_COMPUTE_POOL RESUME;"

# Wait 2-5 minutes, then verify
snow sql -c demo -q "DESCRIBE COMPUTE POOL GRIDGUARD_COMPUTE_POOL;"

# If still stuck, check account limits
snow sql -c demo -q "SHOW COMPUTE POOLS;"
```

---

### Issue: Live Version Not Found

**Symptoms:** 
- Error: `099108 (22000): Live version is not found`
- Notebook execute command fails

**Cause:** Container runtime notebooks require a committed "live version" for CLI execution.

**Recovery:**
```bash
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    ALTER NOTEBOOK GRIDGUARD.GRIDGUARD.GRIDGUARD_CASCADE_NOTEBOOK 
        ADD LIVE VERSION FROM LAST;
"
```

---

### Issue: Streamlit Not Deploying

**Symptoms:** 
- Deploy fails with errors
- 404 when accessing URL
- Old version still showing

**Recovery:**
```bash
# Clean up cached artifacts
rm -rf streamlit/output/bundle

# Drop existing app
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    DROP STREAMLIT IF EXISTS GRIDGUARD.GRIDGUARD.GRIDGUARD_APP;
"

# Redeploy
./deploy.sh --only-streamlit
```

---

### Issue: Data Not Loading

**Symptoms:** 
- Tables have 0 rows
- COPY INTO shows no files processed

**Diagnosis:**
```bash
# Check if staged files exist
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    LIST @GRIDGUARD.GRIDGUARD.DATA_STAGE/raw/;
"

# Check for load errors
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    SELECT * FROM TABLE(VALIDATE(GRIDGUARD.GRIDGUARD.GRID_NODES, JOB_ID => '_last'));
"
```

**Recovery:**
```bash
# Regenerate synthetic data
python3 utils/generate_synthetic_data.py

# Re-upload and load
./deploy.sh --only-data
```

---

### Issue: Permission Denied

**Symptoms:** 
- `Insufficient privileges` errors
- Cannot access database/schema objects

**Diagnosis:**
```bash
snow sql -c demo -q "SELECT CURRENT_ROLE();"
```

**Recovery:**
```bash
# Verify role grants
snow sql -c demo -q "
    USE ROLE ACCOUNTADMIN;
    SHOW GRANTS TO ROLE GRIDGUARD_ROLE;
"

# Re-run account setup if needed
./deploy.sh --only-sql
```

---

### Issue: Cortex Search Service Error

**Symptoms:**
- Search queries fail
- "Service not found" error

**Recovery:**
```bash
# Deploy Cortex services
snow sql -c demo -q "
    USE ROLE GRIDGUARD_ROLE;
    USE DATABASE GRIDGUARD;
    USE SCHEMA GRIDGUARD;
    USE WAREHOUSE GRIDGUARD_WH;
"
snow sql -c demo -f sql/03_cortex_setup.sql

# Verify service exists
snow sql -c demo -q "SHOW CORTEX SEARCH SERVICES IN SCHEMA GRIDGUARD.GRIDGUARD;"
```

---

## 5. Full Test Cycle Commands

> **Cursor AI Users:** All commands in this section require running outside the sandbox.
> Use `required_permissions: ["all"]` when executing through Cursor AI.

### One-Liner (Non-Interactive Full Cycle)
```bash
./clean.sh --force && ./deploy.sh && ./run.sh main && ./run.sh status
```

### Step-by-Step (Interactive)
```bash
# Step 1: Clean
./clean.sh

# Step 2: Deploy
./deploy.sh

# Step 3: Execute notebook
./run.sh main

# Step 4: Verify
./run.sh status
./run.sh streamlit
```

### Component-Only Operations

| Purpose | Command |
|---------|---------|
| SQL infrastructure only | `./deploy.sh --only-sql` |
| Data reload only | `./deploy.sh --only-data` |
| Notebook redeploy | `./deploy.sh --only-notebook` |
| Streamlit redeploy | `./deploy.sh --only-streamlit` |
| Skip data upload | `./deploy.sh --skip-data` |
| Check status | `./run.sh status` |
| Execute notebook | `./run.sh main` |
| Get Streamlit URL | `./run.sh streamlit` |
| Get notebook URL | `./run.sh notebook` |

### Environment Prefix Examples
```bash
# Deploy to DEV environment
./deploy.sh --prefix DEV

# Clean DEV environment
./clean.sh --prefix DEV --force

# Execute in DEV
./run.sh --prefix DEV main
```

### Alternative Connection
```bash
# Use production connection
./clean.sh -c prod --force
./deploy.sh -c prod
./run.sh -c prod main
```

---

## 6. Success Criteria

### Technical Validators

| Criterion | Threshold | Verification Command |
|-----------|-----------|---------------------|
| Deployment completes | All steps `[OK]` | `./deploy.sh` exit code 0 |
| Base tables populated | All 4 tables > 0 rows | See data load query |
| Notebook executes | Completes < 15 min | `./run.sh main` exit code 0 |
| Results generated | 3 scenarios in results | `SIMULATION_RESULTS` query |
| Streamlit accessible | URL responds with 200 | Browser navigation |
| Patient Zero identified | 1 per scenario | IS_PATIENT_ZERO query |

### Business Validators (from DRD)

| Criterion | Verification Method | Expected |
|-----------|---------------------|----------|
| Simulation Efficiency | `./run.sh main` timing | < 15 minutes end-to-end |
| "Patient Zero" identified | Query SIMULATION_RESULTS | IS_PATIENT_ZERO = TRUE for each scenario |
| Cascade path traced | Query SIMULATION_RESULTS | CASCADE_ORDER, CASCADE_DEPTH populated |
| Financial impact calculated | Query SIMULATION_RESULTS | REPAIR_COST, LOAD_SHED_MW non-null |
| Compliance search works | Cortex Search query | Relevant docs returned |

### Minimum Row Count Expectations

| Table | Minimum Rows |
|-------|-------------|
| GRID_NODES | 20 |
| GRID_EDGES | 40 |
| HISTORICAL_TELEMETRY | 1000 |
| COMPLIANCE_DOCS | 10 |
| SIMULATION_RESULTS (after notebook) | 50 |

---

## 7. Test Automation Script

> **Cursor AI Users:** When running `test_cycle.sh` through Cursor AI, use `required_permissions: ["all"]` to run outside the sandbox.

Create `test_cycle.sh` in the project root for automated CI/CD testing:

```bash
#!/bin/bash
###############################################################################
# test_cycle.sh - Automated Full Test Cycle for GridGuard
#
# Usage:
#   ./test_cycle.sh              # Use default 'demo' connection
#   ./test_cycle.sh prod         # Use 'prod' connection
#   ./test_cycle.sh demo DEV     # Use 'demo' connection with DEV prefix
###############################################################################

set -e
set -o pipefail

# Configuration
CONNECTION_NAME="${1:-demo}"
ENV_PREFIX="${2:-}"
MIN_RESULT_ROWS=50
MIN_SCENARIOS=3
TIMEOUT_SECONDS=900

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build prefix args
PREFIX_ARG=""
if [ -n "$ENV_PREFIX" ]; then
    PREFIX_ARG="--prefix $ENV_PREFIX"
fi

echo "=========================================="
echo "GridGuard - Full Test Cycle"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Connection: $CONNECTION_NAME"
echo "  Prefix: ${ENV_PREFIX:-<none>}"
echo "  Started: $(date)"
echo ""

###############################################################################
# Phase 1: Clean
###############################################################################
echo "Phase 1: Cleanup..."
echo "----------------------------------------"
./clean.sh -c $CONNECTION_NAME $PREFIX_ARG --force
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

###############################################################################
# Phase 2: Deploy
###############################################################################
echo "Phase 2: Deploy..."
echo "----------------------------------------"
./deploy.sh -c $CONNECTION_NAME $PREFIX_ARG
echo -e "${GREEN}✓ Deployment complete${NC}"
echo ""

###############################################################################
# Phase 3: Execute
###############################################################################
echo "Phase 3: Execute notebook..."
echo "----------------------------------------"
timeout $TIMEOUT_SECONDS ./run.sh -c $CONNECTION_NAME $PREFIX_ARG main || {
    echo -e "${RED}✗ Notebook execution failed or timed out${NC}"
    exit 1
}
echo -e "${GREEN}✓ Notebook execution complete${NC}"
echo ""

###############################################################################
# Phase 4: Validate
###############################################################################
echo "Phase 4: Validate results..."
echo "----------------------------------------"

# Determine database name
if [ -n "$ENV_PREFIX" ]; then
    DATABASE="${ENV_PREFIX}_GRIDGUARD"
else
    DATABASE="GRIDGUARD"
fi

# Check result count
RESULT_COUNT=$(snow sql -c $CONNECTION_NAME -q "
    SELECT COUNT(*) FROM ${DATABASE}.GRIDGUARD.SIMULATION_RESULTS;
" -o tsv 2>/dev/null | tail -1)

# Check scenario count
SCENARIO_COUNT=$(snow sql -c $CONNECTION_NAME -q "
    SELECT COUNT(DISTINCT SCENARIO_NAME) FROM ${DATABASE}.GRIDGUARD.SIMULATION_RESULTS;
" -o tsv 2>/dev/null | tail -1)

# Check Patient Zero count
PATIENT_ZERO_COUNT=$(snow sql -c $CONNECTION_NAME -q "
    SELECT COUNT(*) FROM ${DATABASE}.GRIDGUARD.SIMULATION_RESULTS WHERE IS_PATIENT_ZERO = TRUE;
" -o tsv 2>/dev/null | tail -1)

echo "  Results rows: $RESULT_COUNT (min: $MIN_RESULT_ROWS)"
echo "  Scenarios: $SCENARIO_COUNT (min: $MIN_SCENARIOS)"
echo "  Patient Zeros: $PATIENT_ZERO_COUNT (expected: $MIN_SCENARIOS)"
echo ""

###############################################################################
# Final Assessment
###############################################################################
PASS=true

if [ "$RESULT_COUNT" -lt "$MIN_RESULT_ROWS" ]; then
    echo -e "${RED}✗ Insufficient result rows${NC}"
    PASS=false
fi

if [ "$SCENARIO_COUNT" -lt "$MIN_SCENARIOS" ]; then
    echo -e "${RED}✗ Missing scenarios${NC}"
    PASS=false
fi

if [ "$PATIENT_ZERO_COUNT" -ne "$MIN_SCENARIOS" ]; then
    echo -e "${YELLOW}⚠ Patient Zero count mismatch (got $PATIENT_ZERO_COUNT, expected $MIN_SCENARIOS)${NC}"
fi

echo ""
echo "=========================================="
if [ "$PASS" = true ]; then
    echo -e "${GREEN}✅ TEST CYCLE PASSED${NC}"
    echo "=========================================="
    echo "Completed: $(date)"
    exit 0
else
    echo -e "${RED}❌ TEST CYCLE FAILED${NC}"
    echo "=========================================="
    echo "Completed: $(date)"
    exit 1
fi
```

### Making the Script Executable

```bash
chmod +x test_cycle.sh
```

### Running the Automated Test

```bash
# Default test
./test_cycle.sh

# With specific connection
./test_cycle.sh prod

# With environment prefix
./test_cycle.sh demo DEV
```

---

## Appendix A: Resource Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GridGuard Resource Hierarchy                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ACCOUNTADMIN                                                       │
│       │                                                              │
│       ├── GRIDGUARD_ROLE ◄────────────────────────────────────┐     │
│       │       │                                                │     │
│       │       └── GRIDGUARD (Database)                         │     │
│       │               │                                        │     │
│       │               └── GRIDGUARD (Schema)                   │     │
│       │                       │                                │     │
│       │                       ├── Tables                       │     │
│       │                       │   ├── GRID_NODES               │     │
│       │                       │   ├── GRID_EDGES               │     │
│       │                       │   ├── HISTORICAL_TELEMETRY     │     │
│       │                       │   ├── COMPLIANCE_DOCS          │     │
│       │                       │   ├── SIMULATION_RESULTS       │     │
│       │                       │   └── MODEL_ARTIFACTS          │     │
│       │                       │                                │     │
│       │                       ├── Views                        │     │
│       │                       │   ├── VW_SCENARIO_SUMMARY      │     │
│       │                       │   ├── VW_CASCADE_ANALYSIS      │     │
│       │                       │   └── VW_SCENARIO_IMPACT       │     │
│       │                       │                                │     │
│       │                       ├── Stages                       │     │
│       │                       │   ├── DATA_STAGE               │     │
│       │                       │   └── MODELS_STAGE             │     │
│       │                       │                                │     │
│       │                       ├── GRIDGUARD_CASCADE_NOTEBOOK ──┼──┐  │
│       │                       │                                │  │  │
│       │                       ├── GRIDGUARD_APP (Streamlit)    │  │  │
│       │                       │                                │  │  │
│       │                       ├── COMPLIANCE_SEARCH_SERVICE    │  │  │
│       │                       │                                │  │  │
│       │                       └── GRIDGUARD_EGRESS_RULE ───────┼──┼──┤
│       │                                                        │  │  │
│       ├── GRIDGUARD_WH ────────────────────────────────────────┘  │  │
│       │                                                           │  │
│       ├── GRIDGUARD_COMPUTE_POOL (GPU) ◄──────────────────────────┘  │
│       │                                                              │
│       └── GRIDGUARD_EXTERNAL_ACCESS ◄────────────────────────────────┘
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GridGuard Data Flow                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Local Files                     Snowflake                          │
│   ────────────                    ─────────                          │
│                                                                      │
│   data/synthetic/                                                    │
│       │                                                              │
│       ├── grid_nodes.csv ──────► @DATA_STAGE ──────► GRID_NODES      │
│       ├── grid_edges.csv ──────► @DATA_STAGE ──────► GRID_EDGES      │
│       ├── historical_telemetry.csv ► @DATA_STAGE ► HISTORICAL_TELEMETRY│
│       └── compliance_docs.csv ──► @DATA_STAGE ──► COMPLIANCE_DOCS    │
│                                                              │       │
│   notebooks/                                                 │       │
│       └── grid_cascade_analysis.ipynb                        │       │
│               │                                              │       │
│               └──────► GRIDGUARD_CASCADE_NOTEBOOK            │       │
│                               │                              │       │
│                               │ (reads)                      │       │
│                               ▼                              │       │
│                        ┌──────────────────┐                  │       │
│                        │ GRID_NODES       │◄─────────────────┘       │
│                        │ GRID_EDGES       │                          │
│                        │ HISTORICAL_      │                          │
│                        │ TELEMETRY        │                          │
│                        └────────┬─────────┘                          │
│                                 │                                    │
│                                 │ (GNN Training + Inference)         │
│                                 ▼                                    │
│                        ┌──────────────────┐                          │
│                        │ SIMULATION_      │                          │
│                        │ RESULTS          │                          │
│                        └────────┬─────────┘                          │
│                                 │                                    │
│                                 │ (visualized by)                    │
│                                 ▼                                    │
│                        ┌──────────────────┐                          │
│                        │ GRIDGUARD_APP    │                          │
│                        │ (Streamlit)      │                          │
│                        └──────────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2025-12-21  
**See Also:**
- [DRD.md](../DRD.md) - Demo Requirements Document
- [SNOWFLAKE_DEMO_FULL_TEST_CYCLE.md](../.cursor/SNOWFLAKE_DEMO_FULL_TEST_CYCLE.md) - Test cycle methodology

