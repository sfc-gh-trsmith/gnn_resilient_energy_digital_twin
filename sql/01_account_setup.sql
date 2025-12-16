-- ============================================================================
-- GridGuard - Account-Level Setup
-- ============================================================================
-- Creates account-level objects: role, database, warehouse, compute pool
-- Requires ACCOUNTADMIN role
-- 
-- Session variables (set by deploy.sh):
--   $FULL_PREFIX, $PROJECT_ROLE, $PROJECT_WH, $PROJECT_COMPUTE_POOL,
--   $PROJECT_SCHEMA, $PROJECT_EXTERNAL_ACCESS
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. Create Project Role
-- ============================================================================
CREATE ROLE IF NOT EXISTS IDENTIFIER($PROJECT_ROLE)
    COMMENT = 'Role for GridGuard energy grid resilience demo';

-- Grant role to current user
SET MY_USER = (SELECT CURRENT_USER());
GRANT ROLE IDENTIFIER($PROJECT_ROLE) TO USER IDENTIFIER($MY_USER);
GRANT ROLE IDENTIFIER($PROJECT_ROLE) TO ROLE SYSADMIN;

-- ============================================================================
-- 2. Create Database
-- ============================================================================
CREATE DATABASE IF NOT EXISTS IDENTIFIER($FULL_PREFIX)
    COMMENT = 'GridGuard - Energy Grid Resilience Digital Twin';

-- ============================================================================
-- 3. Create Schema
-- ============================================================================
SET FQ_SCHEMA = $FULL_PREFIX || '.' || $PROJECT_SCHEMA;
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($FQ_SCHEMA)
    COMMENT = 'Main schema for GridGuard demo';

-- ============================================================================
-- 4. Create Warehouse
-- ============================================================================
CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($PROJECT_WH)
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for GridGuard queries and Streamlit';

-- ============================================================================
-- 5. Create GPU Compute Pool for PyTorch Geometric
-- ============================================================================
CREATE COMPUTE POOL IF NOT EXISTS IDENTIFIER($PROJECT_COMPUTE_POOL)
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 300
    COMMENT = 'GPU compute pool for PyTorch Geometric GNN training';

-- ============================================================================
-- 6. Create External Access Integration using Snowflake managed PyPI rule
-- ============================================================================
-- Use the Snowflake-managed network rule for PyPI access
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION IDENTIFIER($PROJECT_EXTERNAL_ACCESS)
    ALLOWED_NETWORK_RULES = (SNOWFLAKE.EXTERNAL_ACCESS.PYPI_RULE)
    ENABLED = TRUE
    COMMENT = 'External access for pip package installation (PyTorch Geometric)';

-- ============================================================================
-- 7. Grant Ownership and Permissions
-- ============================================================================

-- Grant ownership of database to project role
GRANT OWNERSHIP ON DATABASE IDENTIFIER($FULL_PREFIX) 
    TO ROLE IDENTIFIER($PROJECT_ROLE) COPY CURRENT GRANTS;

-- Grant ownership of schema
GRANT OWNERSHIP ON SCHEMA IDENTIFIER($FQ_SCHEMA) 
    TO ROLE IDENTIFIER($PROJECT_ROLE) COPY CURRENT GRANTS;

-- Grant ownership of warehouse
GRANT OWNERSHIP ON WAREHOUSE IDENTIFIER($PROJECT_WH) 
    TO ROLE IDENTIFIER($PROJECT_ROLE) COPY CURRENT GRANTS;

-- Grant usage on compute pool (keep ownership with ACCOUNTADMIN for now)
GRANT USAGE ON COMPUTE POOL IDENTIFIER($PROJECT_COMPUTE_POOL) 
    TO ROLE IDENTIFIER($PROJECT_ROLE);
GRANT MONITOR ON COMPUTE POOL IDENTIFIER($PROJECT_COMPUTE_POOL) 
    TO ROLE IDENTIFIER($PROJECT_ROLE);

-- Grant usage on external access integration
GRANT USAGE ON INTEGRATION IDENTIFIER($PROJECT_EXTERNAL_ACCESS) 
    TO ROLE IDENTIFIER($PROJECT_ROLE);

-- ============================================================================
-- 8. Summary
-- ============================================================================
SELECT 'Account-level setup completed successfully!' AS STATUS;
SELECT 
    $PROJECT_ROLE AS ROLE_CREATED,
    $FULL_PREFIX AS DATABASE_CREATED,
    $PROJECT_WH AS WAREHOUSE_CREATED,
    $PROJECT_COMPUTE_POOL AS COMPUTE_POOL_CREATED,
    $PROJECT_EXTERNAL_ACCESS AS EXTERNAL_ACCESS_CREATED;
