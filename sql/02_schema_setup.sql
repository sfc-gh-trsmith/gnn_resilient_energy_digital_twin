-- ============================================================================
-- GridGuard - Schema-Level Setup
-- ============================================================================
-- Creates tables, stages, and file formats for the GridGuard demo
-- Run with project role after 01_account_setup.sql
-- ============================================================================

-- ============================================================================
-- 1. Create Stages
-- ============================================================================
CREATE STAGE IF NOT EXISTS DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for data files (CSVs, documents)';

CREATE STAGE IF NOT EXISTS MODELS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for model artifacts and notebooks';

-- ============================================================================
-- 2. Create File Formats
-- ============================================================================
CREATE FILE FORMAT IF NOT EXISTS CSV_FORMAT
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('', 'NULL', 'null')
    EMPTY_FIELD_AS_NULL = TRUE
    COMMENT = 'Standard CSV format with header';

-- ============================================================================
-- 3. Create Dimension Tables
-- ============================================================================

-- Grid Nodes: Substations and assets in the power grid
CREATE TABLE IF NOT EXISTS GRID_NODES (
    NODE_ID VARCHAR(50) PRIMARY KEY,
    NODE_NAME VARCHAR(200) NOT NULL,
    NODE_TYPE VARCHAR(50) NOT NULL,  -- SUBSTATION, GENERATOR, LOAD_CENTER, TRANSMISSION_HUB
    LAT FLOAT NOT NULL,
    LON FLOAT NOT NULL,
    REGION VARCHAR(100),
    CAPACITY_MW FLOAT,
    VOLTAGE_KV FLOAT,
    INSTALL_YEAR INT,
    CRITICALITY_SCORE FLOAT,  -- 0-1, higher = more critical
    COMMENT VARCHAR(500)
)
COMMENT = 'Grid topology nodes - substations and power assets';

-- Grid Edges: Transmission lines connecting nodes
CREATE TABLE IF NOT EXISTS GRID_EDGES (
    EDGE_ID VARCHAR(50) PRIMARY KEY,
    SRC_NODE VARCHAR(50) NOT NULL,
    DST_NODE VARCHAR(50) NOT NULL,
    EDGE_TYPE VARCHAR(50) NOT NULL,  -- TRANSMISSION, DISTRIBUTION, TIE_LINE
    CAPACITY_MW FLOAT,
    LENGTH_MILES FLOAT,
    VOLTAGE_KV FLOAT,
    REDUNDANCY_LEVEL INT,  -- 1 = single path, 2+ = redundant
    COMMENT VARCHAR(500),
    FOREIGN KEY (SRC_NODE) REFERENCES GRID_NODES(NODE_ID),
    FOREIGN KEY (DST_NODE) REFERENCES GRID_NODES(NODE_ID)
)
COMMENT = 'Grid topology edges - transmission lines';

-- ============================================================================
-- 4. Create Fact Tables
-- ============================================================================

-- Historical Telemetry: Time-series sensor data from grid nodes
CREATE TABLE IF NOT EXISTS HISTORICAL_TELEMETRY (
    TELEMETRY_ID VARCHAR(100) PRIMARY KEY,
    TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    NODE_ID VARCHAR(50) NOT NULL,
    SCENARIO_NAME VARCHAR(100) NOT NULL,  -- BASE_CASE, HIGH_LOAD, WINTER_STORM_2021
    VOLTAGE_KV FLOAT,
    LOAD_MW FLOAT,
    FREQUENCY_HZ FLOAT,
    TEMPERATURE_F FLOAT,
    STATUS VARCHAR(20) NOT NULL,  -- ACTIVE, WARNING, FAILED, OFFLINE
    ALERT_CODE VARCHAR(50),
    FOREIGN KEY (NODE_ID) REFERENCES GRID_NODES(NODE_ID)
)
COMMENT = 'Historical telemetry snapshots for scenario simulation';

-- Simulation Results: Output from GNN cascade analysis
CREATE TABLE IF NOT EXISTS SIMULATION_RESULTS (
    SIMULATION_ID VARCHAR(100) PRIMARY KEY,
    SCENARIO_NAME VARCHAR(100) NOT NULL,
    NODE_ID VARCHAR(50) NOT NULL,
    RUN_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FAILURE_PROBABILITY FLOAT NOT NULL,  -- 0-1
    IS_PATIENT_ZERO BOOLEAN DEFAULT FALSE,
    CASCADE_ORDER INT,  -- Order in cascade sequence (1 = first to fail)
    CASCADE_DEPTH INT,  -- Hops from patient zero
    LOAD_SHED_MW FLOAT,
    CUSTOMERS_IMPACTED INT,
    REPAIR_COST FLOAT,
    RISK_SCORE FLOAT,  -- Composite risk score
    AI_EXPLANATION VARCHAR(2000),
    FOREIGN KEY (NODE_ID) REFERENCES GRID_NODES(NODE_ID)
)
COMMENT = 'GNN model simulation results for cascade analysis';

-- ============================================================================
-- 5. Create Compliance Documents Table (for Cortex Search)
-- ============================================================================

CREATE TABLE IF NOT EXISTS COMPLIANCE_DOCS (
    DOC_ID VARCHAR(50) PRIMARY KEY,
    REGULATION_CODE VARCHAR(50) NOT NULL,  -- NERC-CIP-008-6, NERC-EOP-004, etc.
    TITLE VARCHAR(500) NOT NULL,
    SECTION VARCHAR(100),
    CONTENT VARCHAR(16000) NOT NULL,  -- Document text for RAG
    EFFECTIVE_DATE DATE,
    KEYWORDS VARCHAR(1000),
    DOC_TYPE VARCHAR(50)  -- REGULATION, PROCEDURE, FORM, GUIDANCE
)
COMMENT = 'Compliance documents for Cortex Search RAG';

-- ============================================================================
-- 6. Create Model Artifacts Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS MODEL_ARTIFACTS (
    ARTIFACT_ID VARCHAR(100) PRIMARY KEY,
    MODEL_NAME VARCHAR(200) NOT NULL,
    VERSION VARCHAR(50) NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    TRAINING_SCENARIOS VARCHAR(500),
    METRICS VARIANT,  -- JSON with training metrics
    STAGE_PATH VARCHAR(500),  -- Path to serialized model in stage
    STATUS VARCHAR(20) DEFAULT 'ACTIVE'  -- ACTIVE, ARCHIVED
)
COMMENT = 'Trained model metadata and artifact references';

-- ============================================================================
-- 7. Create Summary Views
-- ============================================================================

CREATE OR REPLACE VIEW VW_SCENARIO_SUMMARY AS
SELECT 
    SCENARIO_NAME,
    COUNT(DISTINCT NODE_ID) AS NODES_ANALYZED,
    SUM(CASE WHEN STATUS = 'FAILED' THEN 1 ELSE 0 END) AS FAILED_NODES,
    SUM(CASE WHEN STATUS = 'WARNING' THEN 1 ELSE 0 END) AS WARNING_NODES,
    AVG(LOAD_MW) AS AVG_LOAD_MW,
    MAX(TIMESTAMP) AS LATEST_TIMESTAMP
FROM HISTORICAL_TELEMETRY
GROUP BY SCENARIO_NAME;

CREATE OR REPLACE VIEW VW_CASCADE_ANALYSIS AS
SELECT 
    sr.SCENARIO_NAME,
    sr.NODE_ID,
    gn.NODE_NAME,
    gn.NODE_TYPE,
    gn.REGION,
    sr.FAILURE_PROBABILITY,
    sr.IS_PATIENT_ZERO,
    sr.CASCADE_ORDER,
    sr.CASCADE_DEPTH,
    sr.LOAD_SHED_MW,
    sr.CUSTOMERS_IMPACTED,
    sr.REPAIR_COST,
    sr.RISK_SCORE,
    sr.AI_EXPLANATION
FROM SIMULATION_RESULTS sr
JOIN GRID_NODES gn ON sr.NODE_ID = gn.NODE_ID
ORDER BY sr.SCENARIO_NAME, sr.CASCADE_ORDER;

CREATE OR REPLACE VIEW VW_SCENARIO_IMPACT AS
SELECT 
    SCENARIO_NAME,
    COUNT(*) AS TOTAL_NODES_AFFECTED,
    SUM(CASE WHEN IS_PATIENT_ZERO THEN 1 ELSE 0 END) AS PATIENT_ZERO_COUNT,
    MAX(CASCADE_DEPTH) AS MAX_CASCADE_DEPTH,
    SUM(LOAD_SHED_MW) AS TOTAL_LOAD_SHED_MW,
    SUM(CUSTOMERS_IMPACTED) AS TOTAL_CUSTOMERS_IMPACTED,
    SUM(REPAIR_COST) AS TOTAL_REPAIR_COST,
    AVG(FAILURE_PROBABILITY) AS AVG_FAILURE_PROBABILITY
FROM SIMULATION_RESULTS
WHERE CASCADE_ORDER IS NOT NULL
GROUP BY SCENARIO_NAME;

-- ============================================================================
-- 8. Summary
-- ============================================================================
SELECT 'Schema-level setup completed successfully!' AS STATUS;

-- Show created objects
SELECT 'TABLES' AS OBJECT_TYPE, TABLE_NAME AS OBJECT_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_TYPE = 'BASE TABLE'
UNION ALL
SELECT 'VIEWS', TABLE_NAME 
FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
UNION ALL
SELECT 'STAGES', STAGE_NAME 
FROM INFORMATION_SCHEMA.STAGES 
WHERE STAGE_SCHEMA = CURRENT_SCHEMA()
ORDER BY OBJECT_TYPE, OBJECT_NAME;

