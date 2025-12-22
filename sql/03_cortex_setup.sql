-- ============================================================================
-- GridGuard - Cortex Intelligence Setup
-- ============================================================================
-- Creates Cortex Search service, uploads Semantic Model, and configures
-- Cortex AI capabilities for compliance assistance
-- Run with project role after data is loaded
--
-- IMPORTANT: This script uses placeholders that deploy.sh substitutes:
--   {{WAREHOUSE}} - Project warehouse name (e.g., GRIDGUARD_WH or DEV_GRIDGUARD_WH)
-- ============================================================================

-- ============================================================================
-- 1. Upload Semantic Model to Stage
-- ============================================================================
-- Note: The semantic model YAML file should be uploaded via deploy.sh
-- This section verifies the upload and provides the stage path

-- Verify semantic model is accessible (run after deploy.sh uploads it)
-- LIST @MODELS_STAGE/semantic_model.yaml;

-- ============================================================================
-- 2. Create Cortex Search Service for Compliance Documents
-- ============================================================================

-- The search service indexes COMPLIANCE_DOCS for RAG queries
CREATE OR REPLACE CORTEX SEARCH SERVICE COMPLIANCE_SEARCH_SERVICE
    ON CONTENT
    ATTRIBUTES REGULATION_CODE, TITLE, DOC_TYPE, KEYWORDS
    WAREHOUSE = {{WAREHOUSE}}
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOC_ID,
            REGULATION_CODE,
            TITLE,
            SECTION,
            CONTENT,
            DOC_TYPE,
            KEYWORDS
        FROM COMPLIANCE_DOCS
    );

-- Grant usage to project role (if running as ACCOUNTADMIN)
-- GRANT USAGE ON CORTEX SEARCH SERVICE COMPLIANCE_SEARCH_SERVICE TO ROLE GRIDGUARD_ROLE;

-- ============================================================================
-- 2. Test the Search Service
-- ============================================================================

-- Sample search query for testing
-- SELECT * FROM TABLE(
--     GRIDGUARD.GRIDGUARD.COMPLIANCE_SEARCH_SERVICE!SEARCH(
--         QUERY => 'voltage collapse reporting requirements',
--         COLUMNS => ['REGULATION_CODE', 'TITLE', 'CONTENT'],
--         TOP_K => 5
--     )
-- );

-- ============================================================================
-- 3. Cortex Agent Setup
-- ============================================================================
-- The GridGuard Agent combines Cortex Analyst (SQL generation) with 
-- Cortex Search (compliance document retrieval) for comprehensive responses.
--
-- Agent Definition: cortex/gridguard_agent.json
--
-- DEPLOYMENT OPTIONS:
--
-- Option A: Deploy using sf_cortex_agent_ops.py utility (RECOMMENDED)
-- -----------------------------------------------------------------------
-- # First, ensure semantic model is staged:
-- PUT file://cortex/semantic_model.yaml @MODELS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--
-- # Deploy agent using REST API:
-- python .cursor/sf_cortex_agent_ops.py import \
--     --input cortex/gridguard_agent.json \
--     --database GRIDGUARD \
--     --schema GRIDGUARD \
--     --account <your-account> \
--     --pat-token <your-pat-token>
--
-- # To update existing agent:
-- python .cursor/sf_cortex_agent_ops.py import \
--     --input cortex/gridguard_agent.json \
--     --database GRIDGUARD \
--     --schema GRIDGUARD \
--     --replace \
--     --pat-token <your-pat-token>
--
--
-- Option B: Dynamic invocation from Streamlit (current implementation)
-- -----------------------------------------------------------------------
-- The Streamlit app uses SNOWFLAKE.CORTEX.COMPLETE() and Cortex Search
-- directly, which doesn't require a persistent Agent object.
--
-- Example direct invocation:
-- SELECT SNOWFLAKE.CORTEX.COMPLETE(
--     'claude-3-5-sonnet',
--     'Answer this question about grid simulations: <user_question>'
-- );
--
-- For Cortex Search:
-- SELECT * FROM TABLE(
--     COMPLIANCE_SEARCH_SERVICE!SEARCH(
--         QUERY => 'cascade failure reporting',
--         COLUMNS => ['REGULATION_CODE', 'TITLE', 'CONTENT'],
--         TOP_K => 5
--     )
-- );


-- ============================================================================
-- 4. Semantic View Deployment (Optional)
-- ============================================================================
-- If using Semantic Views instead of the YAML-based semantic model:
--
-- Deploy using sf_cortex_agent_ops.py:
-- python .cursor/sf_cortex_agent_ops.py deploy-semantic-view \
--     --input cortex/semantic_model.yaml \
--     --database GRIDGUARD \
--     --schema GRIDGUARD \
--     --account <your-account> \
--     --user <your-user> \
--     --private-key-path ~/.ssh/snowflake_key.p8


-- ============================================================================
-- 5. Summary
-- ============================================================================
SELECT 'Cortex Search service created successfully!' AS STATUS;

-- Show Cortex services
SHOW CORTEX SEARCH SERVICES;

