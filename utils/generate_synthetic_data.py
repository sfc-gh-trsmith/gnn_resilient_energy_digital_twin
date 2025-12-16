#!/usr/bin/env python3
"""
generate_synthetic_data.py - Generate Synthetic Data for GridGuard Demo

This script generates deterministic synthetic data for the GridGuard
energy grid resilience demo. All data is pre-generated and version-controlled.

Usage:
    python3 utils/generate_synthetic_data.py
    python3 utils/generate_synthetic_data.py --output-dir data/synthetic

The generated data includes:
    - grid_nodes.csv: 50 substations/assets in the Texas grid
    - grid_edges.csv: 120+ transmission lines
    - historical_telemetry.csv: Time-series data for 3 scenarios
    - compliance_docs.csv: NERC regulation excerpts for RAG

Hidden Demo Story:
    - "2021 Winter Storm" scenario contains a cascade failure
    - "Permian Basin Substation #7" is the Patient Zero
    - The GNN should identify this node as the cascade origin
"""

import csv
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Deterministic random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "synthetic"

# Texas grid region coordinates (approximate)
TEXAS_REGIONS = {
    "PERMIAN_BASIN": {"lat": 31.8, "lon": -102.4, "name": "Permian Basin"},
    "GULF_COAST": {"lat": 29.5, "lon": -95.0, "name": "Gulf Coast"},
    "PANHANDLE": {"lat": 35.2, "lon": -101.8, "name": "Panhandle"},
    "NORTH_CENTRAL": {"lat": 32.8, "lon": -97.0, "name": "North Central"},
    "SOUTH_CENTRAL": {"lat": 29.4, "lon": -98.5, "name": "South Central"},
    "EAST_TEXAS": {"lat": 31.5, "lon": -94.5, "name": "East Texas"},
    "WEST_TEXAS": {"lat": 31.0, "lon": -104.0, "name": "West Texas"},
}

# Node types
NODE_TYPES = ["SUBSTATION", "GENERATOR", "LOAD_CENTER", "TRANSMISSION_HUB"]

# Edge types
EDGE_TYPES = ["TRANSMISSION", "DISTRIBUTION", "TIE_LINE"]

# Scenarios
SCENARIOS = ["BASE_CASE", "HIGH_LOAD", "WINTER_STORM_2021"]

# Patient Zero node (hidden story)
PATIENT_ZERO_NODE_ID = "SUB_PERMIAN_07"
PATIENT_ZERO_NAME = "Permian Basin Substation #7"


def generate_grid_nodes(output_dir: Path):
    """Generate grid nodes (substations and assets)."""
    nodes = []
    node_id = 1
    
    for region_key, region_info in TEXAS_REGIONS.items():
        # Generate 6-8 nodes per region
        num_nodes = random.randint(6, 8)
        
        for i in range(num_nodes):
            # Add some jitter to coordinates
            lat = region_info["lat"] + random.uniform(-0.5, 0.5)
            lon = region_info["lon"] + random.uniform(-0.5, 0.5)
            
            # Determine node type
            if i == 0:
                node_type = "TRANSMISSION_HUB"
            elif i == 1:
                node_type = "GENERATOR"
            elif i < 4:
                node_type = "SUBSTATION"
            else:
                node_type = "LOAD_CENTER"
            
            # Special handling for Patient Zero
            if region_key == "PERMIAN_BASIN" and i == 6:
                node_id_str = PATIENT_ZERO_NODE_ID
                node_name = PATIENT_ZERO_NAME
                criticality_score = 0.95  # High criticality (hidden bottleneck)
            else:
                node_id_str = f"SUB_{region_key[:3]}_{node_id:02d}"
                node_name = f"{region_info['name']} {node_type.replace('_', ' ').title()} #{i+1}"
                criticality_score = round(random.uniform(0.3, 0.9), 2)
            
            nodes.append({
                "NODE_ID": node_id_str,
                "NODE_NAME": node_name,
                "NODE_TYPE": node_type,
                "LAT": round(lat, 4),
                "LON": round(lon, 4),
                "REGION": region_info["name"],
                "CAPACITY_MW": random.randint(100, 2000),
                "VOLTAGE_KV": random.choice([69, 138, 230, 345, 500]),
                "INSTALL_YEAR": random.randint(1970, 2020),
                "CRITICALITY_SCORE": criticality_score,
                "COMMENT": f"{node_type} in {region_info['name']} region"
            })
            node_id += 1
    
    # Write to CSV
    output_file = output_dir / "grid_nodes.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=nodes[0].keys())
        writer.writeheader()
        writer.writerows(nodes)
    
    print(f"Generated {len(nodes)} grid nodes -> {output_file}")
    return nodes


def generate_grid_edges(nodes: list, output_dir: Path):
    """Generate transmission lines connecting nodes."""
    edges = []
    edge_id = 1
    
    # Group nodes by region
    regions = {}
    for node in nodes:
        region = node["REGION"]
        if region not in regions:
            regions[region] = []
        regions[region].append(node)
    
    # Connect nodes within each region
    for region, region_nodes in regions.items():
        for i, src_node in enumerate(region_nodes):
            # Connect to 2-4 other nodes in the same region
            num_connections = min(random.randint(2, 4), len(region_nodes) - 1)
            targets = random.sample([n for n in region_nodes if n != src_node], num_connections)
            
            for dst_node in targets:
                # Avoid duplicate edges
                existing = any(
                    (e["SRC_NODE"] == src_node["NODE_ID"] and e["DST_NODE"] == dst_node["NODE_ID"]) or
                    (e["SRC_NODE"] == dst_node["NODE_ID"] and e["DST_NODE"] == src_node["NODE_ID"])
                    for e in edges
                )
                if existing:
                    continue
                
                # Calculate distance
                dist = math.sqrt(
                    (src_node["LAT"] - dst_node["LAT"])**2 + 
                    (src_node["LON"] - dst_node["LON"])**2
                ) * 69  # Approximate miles per degree
                
                edges.append({
                    "EDGE_ID": f"LINE_{edge_id:03d}",
                    "SRC_NODE": src_node["NODE_ID"],
                    "DST_NODE": dst_node["NODE_ID"],
                    "EDGE_TYPE": random.choice(EDGE_TYPES),
                    "CAPACITY_MW": random.randint(200, 1500),
                    "LENGTH_MILES": round(dist, 1),
                    "VOLTAGE_KV": random.choice([138, 230, 345, 500]),
                    "REDUNDANCY_LEVEL": random.randint(1, 3),
                    "COMMENT": f"Line from {src_node['NODE_NAME']} to {dst_node['NODE_NAME']}"
                })
                edge_id += 1
    
    # Add inter-region tie lines
    region_list = list(regions.keys())
    for i, r1 in enumerate(region_list):
        for r2 in region_list[i+1:]:
            # 1-2 tie lines between adjacent regions
            if random.random() < 0.6:
                src = random.choice(regions[r1])
                dst = random.choice(regions[r2])
                
                dist = math.sqrt(
                    (src["LAT"] - dst["LAT"])**2 + 
                    (src["LON"] - dst["LON"])**2
                ) * 69
                
                edges.append({
                    "EDGE_ID": f"LINE_{edge_id:03d}",
                    "SRC_NODE": src["NODE_ID"],
                    "DST_NODE": dst["NODE_ID"],
                    "EDGE_TYPE": "TIE_LINE",
                    "CAPACITY_MW": random.randint(500, 2000),
                    "LENGTH_MILES": round(dist, 1),
                    "VOLTAGE_KV": random.choice([345, 500]),
                    "REDUNDANCY_LEVEL": 1,  # Tie lines often single path
                    "COMMENT": f"Inter-region tie line"
                })
                edge_id += 1
    
    # Write to CSV
    output_file = output_dir / "grid_edges.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=edges[0].keys())
        writer.writeheader()
        writer.writerows(edges)
    
    print(f"Generated {len(edges)} grid edges -> {output_file}")
    return edges


def generate_historical_telemetry(nodes: list, output_dir: Path):
    """Generate historical telemetry data for multiple scenarios."""
    telemetry = []
    telemetry_id = 1
    
    # Base timestamp
    base_time = datetime(2021, 2, 14, 0, 0, 0)  # Valentine's Day 2021 (Winter Storm Uri)
    
    # Cascade sequence for Winter Storm scenario (Patient Zero + affected nodes)
    cascade_sequence = [PATIENT_ZERO_NODE_ID]  # Start with Patient Zero
    
    # Find nodes connected to Patient Zero for cascade
    for node in nodes:
        if node["NODE_ID"] != PATIENT_ZERO_NODE_ID:
            # Permian Basin nodes are more likely to cascade
            if "Permian" in node.get("REGION", ""):
                cascade_sequence.append(node["NODE_ID"])
            elif random.random() < 0.3:  # 30% chance for other nodes
                cascade_sequence.append(node["NODE_ID"])
    
    cascade_sequence = cascade_sequence[:15]  # Limit cascade to ~15 nodes
    
    for scenario in SCENARIOS:
        # Generate 24 hours of data at 15-minute intervals
        for hour in range(24):
            for minute in [0, 15, 30, 45]:
                timestamp = base_time + timedelta(hours=hour, minutes=minute)
                
                for node in nodes:
                    # Base values
                    base_voltage = node.get("VOLTAGE_KV", 138)
                    base_load = random.uniform(50, 300)
                    
                    # Scenario-specific adjustments
                    if scenario == "BASE_CASE":
                        voltage = base_voltage * random.uniform(0.98, 1.02)
                        load = base_load * random.uniform(0.9, 1.1)
                        temp = random.uniform(60, 85)
                        status = "ACTIVE"
                        alert_code = None
                        
                    elif scenario == "HIGH_LOAD":
                        voltage = base_voltage * random.uniform(0.95, 1.0)
                        load = base_load * random.uniform(1.3, 1.6)
                        temp = random.uniform(90, 105)
                        status = "WARNING" if load > base_load * 1.4 else "ACTIVE"
                        alert_code = "HIGH_LOAD" if status == "WARNING" else None
                        
                    elif scenario == "WINTER_STORM_2021":
                        temp = random.uniform(-5, 20)  # Cold temps
                        
                        # Cascade failure logic
                        if node["NODE_ID"] in cascade_sequence:
                            cascade_order = cascade_sequence.index(node["NODE_ID"])
                            failure_hour = 6 + cascade_order  # Failures start at hour 6
                            
                            if hour >= failure_hour:
                                status = "FAILED"
                                voltage = 0
                                load = 0
                                alert_code = "CASCADE_FAILURE"
                            elif hour >= failure_hour - 1:
                                status = "WARNING"
                                voltage = base_voltage * random.uniform(0.7, 0.85)
                                load = base_load * random.uniform(0.5, 0.8)
                                alert_code = "VOLTAGE_DROP"
                            else:
                                status = "ACTIVE"
                                voltage = base_voltage * random.uniform(0.9, 1.0)
                                load = base_load * random.uniform(1.1, 1.3)
                                alert_code = None
                        else:
                            # Non-cascade nodes just see high load
                            voltage = base_voltage * random.uniform(0.92, 1.0)
                            load = base_load * random.uniform(1.2, 1.5)
                            status = "ACTIVE"
                            alert_code = None
                    
                    telemetry.append({
                        "TELEMETRY_ID": f"TEL_{telemetry_id:06d}",
                        "TIMESTAMP": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "NODE_ID": node["NODE_ID"],
                        "SCENARIO_NAME": scenario,
                        "VOLTAGE_KV": round(voltage, 2),
                        "LOAD_MW": round(load, 2),
                        "FREQUENCY_HZ": round(60 + random.uniform(-0.1, 0.1), 3),
                        "TEMPERATURE_F": round(temp, 1),
                        "STATUS": status,
                        "ALERT_CODE": alert_code or ""
                    })
                    telemetry_id += 1
    
    # Write to CSV
    output_file = output_dir / "historical_telemetry.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=telemetry[0].keys())
        writer.writeheader()
        writer.writerows(telemetry)
    
    print(f"Generated {len(telemetry)} telemetry records -> {output_file}")
    return telemetry


def generate_compliance_docs(output_dir: Path):
    """Generate compliance documents for Cortex Search RAG."""
    docs = [
        {
            "DOC_ID": "NERC_CIP_008_6_R1",
            "REGULATION_CODE": "NERC-CIP-008-6",
            "TITLE": "Cyber Security Incident Response - Incident Response Plan",
            "SECTION": "R1",
            "CONTENT": """Each Responsible Entity shall document one or more Cyber Security Incident response plans that collectively include: 
1.1 One or more processes to identify, classify, and respond to Cyber Security Incidents
1.2 One or more processes to determine if an identified Cyber Security Incident is a Reportable Cyber Security Incident
1.3 The roles and responsibilities of Cyber Security Incident response groups
1.4 Incident handling procedures for each type of Cyber Security Incident
1.5 The process for reporting Reportable Cyber Security Incidents to ES-ISAC and ICS-CERT""",
            "EFFECTIVE_DATE": "2019-07-01",
            "KEYWORDS": "incident response, cyber security, reporting, ES-ISAC",
            "DOC_TYPE": "REGULATION"
        },
        {
            "DOC_ID": "NERC_EOP_004_4_R1",
            "REGULATION_CODE": "NERC-EOP-004-4",
            "TITLE": "Event Reporting - Event Reporting Requirements",
            "SECTION": "R1",
            "CONTENT": """Each Responsible Entity shall report events to the applicable organizations within the specified timeframes:
- Physical threats: within 24 hours to the Electricity Sector Information Sharing and Analysis Center
- Voltage collapse events exceeding 300MW: within 1 hour to the Regional Entity
- Load shedding events exceeding 100MW: within 24 hours using DOE Form OE-417
- Transmission line trips affecting system stability: within 1 hour
For cascade failures affecting multiple substations, immediate notification to the Reliability Coordinator is required.""",
            "EFFECTIVE_DATE": "2022-01-01",
            "KEYWORDS": "event reporting, voltage collapse, load shedding, cascade failure, OE-417",
            "DOC_TYPE": "REGULATION"
        },
        {
            "DOC_ID": "NERC_EOP_004_4_FORM",
            "REGULATION_CODE": "NERC-EOP-004-4",
            "TITLE": "DOE Form OE-417 - Electric Emergency Incident and Disturbance Report",
            "SECTION": "Form",
            "CONTENT": """Form OE-417 must be filed for the following events:
- Fuel supply emergencies affecting reliability
- Load shedding of 100 MW or more
- Voltage reductions of 3 percent or more
- Public appeals to reduce electricity use
- Physical attacks on facilities
- Cyber events affecting reliability
- Major transmission line outages
Filing deadlines: Initial report within 6 hours, final report within 30 days.
Submit to: DOE Office of Electricity via the OE-417 online portal.""",
            "EFFECTIVE_DATE": "2022-01-01",
            "KEYWORDS": "OE-417, emergency report, load shedding, voltage reduction",
            "DOC_TYPE": "FORM"
        },
        {
            "DOC_ID": "NERC_TPL_001_5_R1",
            "REGULATION_CODE": "NERC-TPL-001-5",
            "TITLE": "Transmission System Planning Performance - Steady State",
            "SECTION": "R1",
            "CONTENT": """Each Planning Coordinator and Transmission Planner shall maintain System models for steady-state analysis that include:
1.1 Modeling data for generators, transmission lines, and loads
1.2 System topology representing realistic operating conditions  
1.3 Transfer limits between areas
1.4 Reactive power capabilities
For cascade failure risk assessment, models must simulate N-1-1 contingencies and identify potential cascade initiating nodes (weak points in the system topology). Historical cascade events should inform model validation.""",
            "EFFECTIVE_DATE": "2020-10-01",
            "KEYWORDS": "planning, steady state, topology, cascade, N-1-1, weak points",
            "DOC_TYPE": "REGULATION"
        },
        {
            "DOC_ID": "NERC_FAC_001_3_R1",
            "REGULATION_CODE": "NERC-FAC-001-3",
            "TITLE": "Facility Interconnection Requirements - Connection Requirements",
            "SECTION": "R1",
            "CONTENT": """Each Transmission Owner shall document facility connection requirements that include:
- Voltage regulation requirements
- Protection system requirements
- Metering requirements  
- Communication requirements
For substations identified as critical cascade points, additional redundancy requirements apply:
- Dual protection systems
- Backup power supply with minimum 8-hour capacity
- Real-time monitoring and automatic alerts
Permian Basin and other remote substations require enhanced isolation capability.""",
            "EFFECTIVE_DATE": "2018-04-01",
            "KEYWORDS": "facility, connection, protection, redundancy, Permian Basin",
            "DOC_TYPE": "REGULATION"
        },
        {
            "DOC_ID": "ERCOT_NODAL_4_4_1",
            "REGULATION_CODE": "ERCOT-NODAL-4.4.1",
            "TITLE": "ERCOT Nodal Operating Guides - Voltage Support",
            "SECTION": "4.4.1",
            "CONTENT": """During emergency conditions, ERCOT may issue directives for voltage support:
- All generators must maintain reactive power output within capability curves
- Transmission Operators shall implement voltage reduction procedures per ERCOT protocols
- Load shedding may be ordered if voltage drops below 0.92 per unit
For winter storm conditions, additional protocols apply:
- Natural gas generators must maintain fuel supply coordination
- Wind generation forecasting accuracy requirements increase
- Emergency demand response programs may be activated""",
            "EFFECTIVE_DATE": "2021-06-01",
            "KEYWORDS": "ERCOT, voltage, winter storm, load shedding, demand response",
            "DOC_TYPE": "PROCEDURE"
        },
        {
            "DOC_ID": "ERCOT_BLACKSTART_7_2",
            "REGULATION_CODE": "ERCOT-NODAL-7.2",
            "TITLE": "ERCOT System Restoration - Black Start Procedures",
            "SECTION": "7.2",
            "CONTENT": """Following a cascading blackout, system restoration shall follow these steps:
1. Assess extent of outage and identify black start resources
2. Establish cranking paths from black start units
3. Restore transmission backbone in priority order
4. Coordinate load pickup with Transmission Operators
5. Monitor frequency and voltage during restoration
Critical path substations (identified through cascade analysis) receive priority for restoration. Permian Basin facilities are designated as Tier 1 restoration priority due to natural gas infrastructure dependencies.""",
            "EFFECTIVE_DATE": "2021-06-01",
            "KEYWORDS": "black start, restoration, cascade, Permian Basin, priority",
            "DOC_TYPE": "PROCEDURE"
        },
        {
            "DOC_ID": "WINTER_STORM_URI_REPORT",
            "REGULATION_CODE": "FERC-NERC-2021",
            "TITLE": "February 2021 Cold Weather Outages - Final Report",
            "SECTION": "Executive Summary",
            "CONTENT": """The February 2021 winter storm (Uri) caused widespread outages across Texas and the central United States. Key findings:
- 4.5 million customers lost power at peak
- Generation outages totaled 52,277 MW
- Natural gas supply interruptions cascaded to generators
- Winterization failures were primary cause
- Cascade failures initiated at substations with single points of failure
Recommendations include: enhanced weatherization requirements, improved fuel supply coordination, identification of cascade-vulnerable nodes through graph-based analysis, and mandatory extreme weather planning scenarios.""",
            "EFFECTIVE_DATE": "2021-11-01",
            "KEYWORDS": "winter storm Uri, cascade, weatherization, natural gas, Texas",
            "DOC_TYPE": "GUIDANCE"
        }
    ]
    
    # Write to CSV
    output_file = output_dir / "compliance_docs.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=docs[0].keys())
        writer.writeheader()
        writer.writerows(docs)
    
    print(f"Generated {len(docs)} compliance documents -> {output_file}")
    return docs


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate synthetic data for GridGuard demo")
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})"
    )
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GridGuard - Synthetic Data Generator")
    print("=" * 60)
    print(f"Random Seed: {RANDOM_SEED}")
    print(f"Output Directory: {args.output_dir}")
    print("")
    
    # Generate data
    nodes = generate_grid_nodes(args.output_dir)
    edges = generate_grid_edges(nodes, args.output_dir)
    telemetry = generate_historical_telemetry(nodes, args.output_dir)
    docs = generate_compliance_docs(args.output_dir)
    
    print("")
    print("=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    print("")
    print("Hidden Story:")
    print(f"  - Patient Zero: {PATIENT_ZERO_NAME} ({PATIENT_ZERO_NODE_ID})")
    print("  - Scenario: WINTER_STORM_2021")
    print("  - Cascade starts at hour 6 and propagates outward")
    print("")
    print("Files generated:")
    print(f"  - grid_nodes.csv: {len(nodes)} nodes")
    print(f"  - grid_edges.csv: {len(edges)} edges")
    print(f"  - historical_telemetry.csv: {len(telemetry)} records")
    print(f"  - compliance_docs.csv: {len(docs)} documents")


if __name__ == "__main__":
    main()

