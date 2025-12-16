

Demo Requirements Document (DRD): Project GridGuard – Scenario Simulator (Simplified)

1. Strategic Overview
**Problem Statement:** Energy grid operators struggle to analyze post-incident data or simulate "what-if" scenarios because their topological data is locked in complex formats. They lack the ability to easily run advanced graph algorithms to understand how past failures propagated, preventing them from updating safety protocols effectively.
**Target Business Goals (KPIs):**
* **Simulation Efficiency:** Reduce the time to model a disaster scenario from weeks to minutes.
* **Protocol Compliance:** Increase adherence to safety standards by verifying past incident responses against SOPs.
**The "Wow" Moment:** The user selects a historical "Storm Event" from a dropdown. The system instantly reconstructs the grid topology for that timeframe, runs the PyTorch Geometric model (on-demand via SPCS) to identify the "Patient Zero" node that caused the cascade, and Cortex Analyst generates a SQL-backed report on the financial impact.

2. User Personas & Stories

| Persona Level | Role Title | Key User Story (Demo Flow) |
| :--- | :--- | :--- |
| **Strategic** | **Director of Grid Planning** | "As a Director, I want to simulate how our current infrastructure would handle a repeat of the '2021 Winter Storm' to prioritize upgrades." |
| **Operational** | **Compliance Officer** | "As an Officer, I want to review the specific maintenance logs and voltage readings from a failed substation to audit our response." |
| **Technical** | **Data Scientist** | "As a Data Scientist, I want to run complex graph algorithms on static snapshots of data without managing complex data pipelines." |

3. Data Architecture & Snowpark ML (Backend)
**Structured Data (Inferred Schema):**
* **Simplified Schema (Star/Snowflake):**
    * `GRID_NODES` (Dim): Static list of substations/assets. Columns: `NODE_ID`, `LAT`, `LON`, `TYPE`.
    * `GRID_EDGES` (Dim): Standard connectivity. Columns: `EDGE_ID`, `SRC_NODE`, `DST_NODE`.
    * `HISTORICAL_TELEMETRY` (Fact): Hourly/Minute-level snapshots. Columns: `TIMESTAMP`, `NODE_ID`, `VOLTAGE`, `LOAD_MW`, `STATUS` (Active/Down).
* **Mechanism:** Standard Tables (No Dynamic Tables/Streaming). Data is pre-loaded via `COPY INTO`.

**Unstructured Data (Tribal Knowledge):**
* **Source Material:** Post-Incident Review PDF reports, Maintenance Manuals, Regulatory Findings.
* **Purpose:** To allow the Compliance Officer to "chat with the documents" regarding specific failure codes found in the structured data.

**ML Notebook Specification (Snowpark Container Services):**
* **Objective:** Root Cause & Propagation Analysis (Batch/Interactive).
* **Execution Pattern:** **On-Demand**. The model runs only when the user clicks "Run Simulation" in Streamlit.
* **Algorithm Choice:** **PyTorch Geometric (GCN)** running in a custom SPCS container.
    * *Differentiation:* Demonstrates running specialized, non-standard Python libraries (PyG) securely next to the data.
* **Inference Output:** Results written to a temporary results table `SIMULATION_RESULTS` for visualization.

4. Cortex Intelligence Specifications
**Cortex Analyst (Structured Data / SQL)**
* **Semantic Model Scope:**
    * **Measures:** `Total_Load_Shed_MW`, `Customers_Impacted`, `Repair_Cost`.
    * **Dimensions:** `Event_Name`, `Substation_Model`, `Region`.
* **Golden Query (Verification):**
    * **User Prompt:** "What was the total repair cost for all substations that failed during the simulation?"
    * **Expected SQL Operation:** `SELECT SUM(REPAIR_COST) FROM SIMULATION_RESULTS JOIN ASSETS ... WHERE STATUS = 'FAILED'`

**Cortex Search (Unstructured Data / RAG)**
* **Service Name:** `COMPLIANCE_SEARCH_SERVICE`
* **Indexing Strategy:**
    * **Document Attribute:** Index by `Regulation_Code` (e.g., NERC-CIP standards).
* **Sample RAG Prompt:** "Summarize the NERC reporting requirements for a voltage collapse event exceeding 500MW."

**Cortex Agents (Orchestrator)**
* **Role:** The Agent ties the simulation to the documentation. After the model runs, the user can ask: "Based on this simulation failure, what reporting forms do I need to file?" The Agent uses the simulation context (Analyst) to find the magnitude, and Search to find the correct form.



5. Streamlit Application UX/UI
**Layout Strategy:**
* **Sidebar:** "Scenario Selector" (e.g., Base Case, High Load, Storm Mode). A "Run Simulation" button.
* **Main Panel:**
    * **Top:** Static Graph Plot (PyVis) showing the grid state *after* the simulation runs. Failed nodes highlighted in Red.
    * **Bottom:** Cortex Chat interface.
**Component Logic:**
* **Visualizations:** The graph is static. It does not update live. It renders once the "Run" button completes the SPCS job.
* **Chat Integration:** Toggles between "Analyst" (querying the simulation results) and "Search" (querying the manuals).

6. Success Criteria
* **Technical Validator:** The SPCS container spins up (or is warm), executes the PyG inference on the selected snapshot, and returns results to Streamlit in < 15 seconds.
* **Business Validator:** The demo clearly shows the link between **Data** (Telemetry), **Insight** (Graph Model identifying the weak point), and **Action** (Cortex retrieving the correct fix/protocol).