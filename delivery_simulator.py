"""
FastBox Delivery System Simulator
===================================
Author: [Your Name]
Assignment: Python Developer Round - Nexgensis Technologies Pvt. Ltd.

ASSUMPTIONS (as instructed):
1. Each package is assigned to the nearest agent based on Euclidean distance
   from agent's CURRENT position to the package's warehouse.
2. Agents deliver packages one by one (sequential delivery per agent).
3. After each delivery, agent's position updates to the destination.
4. If two agents are equidistant from a warehouse, the agent with fewer
   assigned packages (alphabetically first on tie) gets the package.
5. "Efficiency" = total_distance / packages_delivered (lower is better).
6. "best_agent" = agent with lowest efficiency score (most efficient).
7. Input JSON supports two formats:
   - dict format: {"warehouses": {"W1": [x, y]}, "agents": {"A1": [x, y]}}
   - list format: {"warehouses": [{"id": "W1", "location": [x, y]}], ...}
   Both are handled automatically.
8. Packages with "warehouse" key and "warehouse_id" key are both supported.
9. Random delay (bonus) is between 0-30 minutes per delivery.
"""

import json
import math
import csv
import os
import random
import sys
from typing import Union


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def euclidean_distance(point1: list, point2: list) -> float:
    """
    Calculate Euclidean distance between two 2D points.
    Formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    """
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def parse_input(data: dict) -> tuple:
    """
    Parse JSON input supporting both dict and list formats.
    Returns: (warehouses_dict, agents_dict, packages_list)
    
    Supported formats:
      Format A (dict): {"W1": [x, y]}
      Format B (list): [{"id": "W1", "location": [x, y]}]
    """
    raw_warehouses = data.get("warehouses", {})
    raw_agents = data.get("agents", {})
    raw_packages = data.get("packages", [])

    # Normalize warehouses
    if isinstance(raw_warehouses, list):
        warehouses = {w["id"]: w["location"] for w in raw_warehouses}
    else:
        warehouses = raw_warehouses  # already dict

    # Normalize agents
    if isinstance(raw_agents, list):
        agents = {a["id"]: list(a["location"]) for a in raw_agents}
    else:
        agents = {k: list(v) for k, v in raw_agents.items()}

    # Normalize packages (support both "warehouse" and "warehouse_id")
    packages = []
    for p in raw_packages:
        pkg = {
            "id": p["id"],
            "warehouse": p.get("warehouse") or p.get("warehouse_id"),
            "destination": p["destination"]
        }
        packages.append(pkg)

    return warehouses, agents, packages


# ─────────────────────────────────────────────
#  CORE ASSIGNMENT LOGIC
# ─────────────────────────────────────────────

def assign_packages_to_agents(warehouses: dict, agents: dict, packages: list) -> dict:
    """
    Assign each package to the nearest available agent.
    
    Logic:
    - For each package, find the agent nearest to that package's warehouse.
    - Tie-breaking: agent with fewer assigned packages wins;
      if still tied, alphabetically first agent wins.
    
    Returns: dict mapping agent_id -> list of package dicts
    """
    assignments = {agent_id: [] for agent_id in agents}

    for package in packages:
        warehouse_id = package["warehouse"]
        warehouse_loc = warehouses[warehouse_id]

        best_agent = None
        best_dist = float("inf")

        for agent_id, agent_loc in agents.items():
            dist = euclidean_distance(agent_loc, warehouse_loc)

            # Tie-breaking: fewer packages assigned first, then alphabetical
            if (dist < best_dist or
                (dist == best_dist and (
                    len(assignments[agent_id]) < len(assignments[best_agent]) or
                    (len(assignments[agent_id]) == len(assignments[best_agent]) and
                     agent_id < best_agent)
                ))):
                best_dist = dist
                best_agent = agent_id

        assignments[best_agent].append(package)

    return assignments


# ─────────────────────────────────────────────
#  SIMULATION
# ─────────────────────────────────────────────

def simulate_deliveries(warehouses: dict, agents: dict,
                        assignments: dict, add_random_delays: bool = False) -> dict:
    """
    Simulate each agent traveling from current position → warehouse → destination
    for every assigned package (sequentially).
    
    Distance per package = dist(agent_pos → warehouse) + dist(warehouse → destination)
    After delivery, agent_pos is updated to destination.
    
    Returns: simulation results dict per agent.
    """
    agent_positions = {k: list(v) for k, v in agents.items()}  # mutable copy
    results = {}

    for agent_id, packages in assignments.items():
        total_distance = 0.0
        delivered = []
        total_delay_minutes = 0

        current_pos = agent_positions[agent_id]

        for package in packages:
            warehouse_loc = warehouses[package["warehouse"]]
            destination = package["destination"]

            # Leg 1: agent travels to warehouse
            dist_to_warehouse = euclidean_distance(current_pos, warehouse_loc)

            # Leg 2: warehouse to destination
            dist_to_dest = euclidean_distance(warehouse_loc, destination)

            trip_distance = dist_to_warehouse + dist_to_dest
            total_distance += trip_distance

            # Optional: random delivery delay (bonus feature)
            delay = 0
            if add_random_delays:
                delay = random.randint(0, 30)
                total_delay_minutes += delay

            delivered.append({
                "package_id": package["id"],
                "warehouse": package["warehouse"],
                "destination": package["destination"],
                "distance": round(trip_distance, 2),
                "delay_minutes": delay
            })

            # Agent is now at destination
            current_pos = list(destination)

        packages_count = len(delivered)
        efficiency = round(total_distance / packages_count, 2) if packages_count > 0 else 0.0

        results[agent_id] = {
            "packages_delivered": packages_count,
            "total_distance": round(total_distance, 2),
            "efficiency": efficiency,
            "delivered_packages": delivered
        }
        if add_random_delays:
            results[agent_id]["total_delay_minutes"] = total_delay_minutes

    return results


# ─────────────────────────────────────────────
#  REPORT GENERATION
# ─────────────────────────────────────────────

def generate_report(simulation_results: dict) -> dict:
    """
    Build final report.
    best_agent = agent with lowest efficiency (least distance per package).
    If all agents have 0 packages, best_agent is None.
    """
    # Only consider agents who delivered at least one package
    active_agents = {
        aid: res for aid, res in simulation_results.items()
        if res["packages_delivered"] > 0
    }

    if active_agents:
        best_agent = min(active_agents, key=lambda a: active_agents[a]["efficiency"])
    else:
        best_agent = None

    report = {}
    for agent_id, res in simulation_results.items():
        report[agent_id] = {
            "packages_delivered": res["packages_delivered"],
            "total_distance": res["total_distance"],
            "efficiency": res["efficiency"]
        }

    report["best_agent"] = best_agent
    return report


# ─────────────────────────────────────────────
#  BONUS: ASCII ROUTE VISUALIZATION
# ─────────────────────────────────────────────

def visualize_routes_ascii(warehouses: dict, agents: dict,
                           assignments: dict, grid_size: int = 20) -> str:
    """
    Display agent routes, warehouses, and destinations on an ASCII grid.
    Scales all coordinates to fit within grid_size x grid_size.
    """
    all_points = (
        list(warehouses.values()) +
        list(agents.values()) +
        [p["destination"] for pkgs in assignments.values() for p in pkgs]
    )

    if not all_points:
        return "No points to visualize."

    max_x = max(p[0] for p in all_points) or 1
    max_y = max(p[1] for p in all_points) or 1

    def scale(point):
        """Scale a coordinate to grid space."""
        x = int((point[0] / max_x) * (grid_size - 1))
        y = int((point[1] / max_y) * (grid_size - 1))
        return x, y

    grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

    # Mark warehouses
    for wid, loc in warehouses.items():
        x, y = scale(loc)
        grid[grid_size - 1 - y][x] = 'W'

    # Mark agents
    for aid, loc in agents.items():
        x, y = scale(loc)
        grid[grid_size - 1 - y][x] = 'A'

    # Mark destinations
    for pkgs in assignments.values():
        for pkg in pkgs:
            x, y = scale(pkg["destination"])
            if grid[grid_size - 1 - y][x] == '.':
                grid[grid_size - 1 - y][x] = 'D'

    lines = ["", "=== ASCII Route Map ===",
             f"  W=Warehouse  A=Agent  D=Destination  (grid {grid_size}x{grid_size})",
             "  " + "─" * grid_size]
    for row in grid:
        lines.append("  " + "".join(row))
    lines.append("  " + "─" * grid_size)
    return "\n".join(lines)


# ─────────────────────────────────────────────
#  BONUS: EXPORT TOP PERFORMER TO CSV
# ─────────────────────────────────────────────

def export_top_performer_csv(report: dict, simulation_results: dict,
                              output_path: str = "top_performer.csv"):
    """
    Export the best agent's delivery details to a CSV file.
    """
    best_agent = report.get("best_agent")
    if not best_agent:
        print("  No best agent to export.")
        return

    deliveries = simulation_results[best_agent].get("delivered_packages", [])

    with open(output_path, "w", newline="") as csvfile:
        fieldnames = ["agent_id", "package_id", "warehouse",
                      "destination_x", "destination_y", "distance_km", "delay_minutes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for d in deliveries:
            writer.writerow({
                "agent_id": best_agent,
                "package_id": d["package_id"],
                "warehouse": d["warehouse"],
                "destination_x": d["destination"][0],
                "destination_y": d["destination"][1],
                "distance_km": d["distance"],
                "delay_minutes": d.get("delay_minutes", 0)
            })

    print(f"  ✅ Top performer CSV saved → {output_path}")


# ─────────────────────────────────────────────
#  BONUS: NEW AGENT JOINING MID-DAY
# ─────────────────────────────────────────────

def add_new_agent(agents: dict, new_agent_id: str, location: list) -> dict:
    """
    Simulate a new agent joining mid-day.
    Returns updated agents dict.
    ASSUMPTION: New agent only picks up unassigned packages. Since assignment
    already happened, this is modeled as a post-assignment addition noted in output.
    """
    if new_agent_id in agents:
        print(f"  ⚠️  Agent {new_agent_id} already exists. Skipping.")
        return agents

    agents[new_agent_id] = location
    print(f"  ✅ New agent {new_agent_id} joined at {location}")
    return agents


# ─────────────────────────────────────────────
#  MAIN RUNNER
# ─────────────────────────────────────────────

def run_simulation(input_path: str, output_path: str = "report.json",
                   add_random_delays: bool = False,
                   export_csv: bool = True,
                   show_ascii: bool = True) -> dict:
    """
    Full pipeline:
      1. Read JSON input
      2. Parse (handle both formats)
      3. Assign packages to nearest agents
      4. Simulate deliveries
      5. Generate report
      6. Save report.json
      7. Bonus: ASCII map, CSV export
    """
    print(f"\n{'='*50}")
    print(f"  FastBox Delivery Simulator")
    print(f"  Input: {input_path}")
    print(f"{'='*50}")

    # Step 1: Read JSON
    with open(input_path, "r") as f:
        data = json.load(f)

    # Step 2: Parse input (handles both dict & list formats)
    warehouses, agents, packages = parse_input(data)

    print(f"\n  📦 Warehouses : {len(warehouses)}")
    print(f"  🚴 Agents     : {len(agents)}")
    print(f"  📫 Packages   : {len(packages)}")

    # Step 3: Assign packages to nearest agents
    assignments = assign_packages_to_agents(warehouses, agents, packages)
    print("\n  📋 Package Assignments:")
    for agent_id, pkgs in assignments.items():
        pkg_ids = [p["id"] for p in pkgs]
        print(f"     {agent_id} → {pkg_ids if pkg_ids else 'No packages'}")

    # Step 4: Simulate deliveries
    simulation_results = simulate_deliveries(
        warehouses, agents, assignments, add_random_delays=add_random_delays
    )

    # Step 5: Generate report
    report = generate_report(simulation_results)

    # Step 6: Save report to JSON
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  ✅ Report saved → {output_path}")
    print(f"\n  📊 Report Summary:")
    for key, val in report.items():
        if key != "best_agent":
            print(f"     {key}: delivered={val['packages_delivered']}, "
                  f"distance={val['total_distance']}, "
                  f"efficiency={val['efficiency']}")
    print(f"     🏆 Best Agent: {report['best_agent']}")

    # Step 7a: Bonus – ASCII visualization
    if show_ascii:
        ascii_map = visualize_routes_ascii(warehouses, agents, assignments)
        print(ascii_map)

    # Step 7b: Bonus – Export CSV
    if export_csv and report.get("best_agent"):
        csv_path = output_path.replace(".json", "_top_performer.csv")
        export_top_performer_csv(report, simulation_results, csv_path)

    # Step 7c: Bonus – Random delays summary
    if add_random_delays:
        print("\n  ⏰ Delay Summary:")
        for aid, res in simulation_results.items():
            if res["packages_delivered"] > 0:
                print(f"     {aid}: {res.get('total_delay_minutes', 0)} min total delay")

    return report


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Accept input file as command-line argument, default to base_case.json
    input_file = sys.argv[1] if len(sys.argv) > 1 else "base_case.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "report.json"

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    run_simulation(
        input_path=input_file,
        output_path=output_file,
        add_random_delays=True,   # Bonus: random delays enabled
        export_csv=True,           # Bonus: export CSV
        show_ascii=True            # Bonus: ASCII map
    )
