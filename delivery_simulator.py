"""
FastBox - Delivery System Simulator
Author: [Anuradha Gethe]
Date: May 2026

What this does:
- Read warehouse, agent, package data from a JSON file
- Find nearest agent for each package (by straight line distance)
- Simulate agent picking up package and delivering it
- Save final report to report.json
"""

import json
import math
import csv
import os
import random
import sys


# --------------------------------------------------
# Step 1: Calculate straight line distance
# Using basic formula: sqrt((x2-x1)^2 + (y2-y1)^2)
# --------------------------------------------------

def get_distance(point_a, point_b):
    x_diff = point_b[0] - point_a[0]
    y_diff = point_b[1] - point_a[1]
    return math.sqrt(x_diff**2 + y_diff**2)


# --------------------------------------------------
# Step 2: Read and clean up the JSON input
# Handles both dict-style and list-style JSON formats
# --------------------------------------------------

def load_data(filepath):
    with open(filepath, "r") as f:
        raw = json.load(f)

    # warehouses can be {"W1": [x,y]} or [{"id":"W1","location":[x,y]}]
    raw_wh = raw.get("warehouses", {})
    if isinstance(raw_wh, list):
        warehouses = {w["id"]: w["location"] for w in raw_wh}
    else:
        warehouses = raw_wh

    # agents same thing
    raw_ag = raw.get("agents", {})
    if isinstance(raw_ag, list):
        agents = {a["id"]: list(a["location"]) for a in raw_ag}
    else:
        agents = {k: list(v) for k, v in raw_ag.items()}

    # packages - some use "warehouse", some use "warehouse_id"
    packages = []
    for p in raw.get("packages", []):
        packages.append({
            "id": p["id"],
            "warehouse": p.get("warehouse") or p.get("warehouse_id"),
            "destination": p["destination"]
        })

    return warehouses, agents, packages


# --------------------------------------------------
# Step 3: Assign each package to the closest agent
# Closest = nearest to that package's warehouse
# Tie rule: fewer packages assigned wins, then alphabetical
# --------------------------------------------------

def assign_packages(warehouses, agents, packages):
    # Start with empty list for each agent
    agent_packages = {aid: [] for aid in agents}

    for pkg in packages:
        wh_location = warehouses[pkg["warehouse"]]
        
        best_agent = None
        best_dist = float("inf")

        for aid, aloc in agents.items():
            d = get_distance(aloc, wh_location)

            # Pick this agent if closer, or if tied but has fewer packages
            is_closer = d < best_dist
            is_tied_fewer = (d == best_dist and 
                             len(agent_packages[aid]) < len(agent_packages[best_agent]))
            is_tied_alpha = (d == best_dist and
                             len(agent_packages[aid]) == len(agent_packages[best_agent]) and
                             aid < best_agent)

            if is_closer or is_tied_fewer or is_tied_alpha:
                best_dist = d
                best_agent = aid

        agent_packages[best_agent].append(pkg)

    return agent_packages


# --------------------------------------------------
# Step 4: Simulate deliveries
# Agent goes: current position -> warehouse -> destination
# After each delivery, position updates to destination
# --------------------------------------------------

def run_deliveries(warehouses, agents, agent_packages, random_delays=False):
    # Track where each agent currently is
    current_pos = {aid: list(loc) for aid, loc in agents.items()}
    results = {}

    for aid, pkg_list in agent_packages.items():
        total_dist = 0.0
        delivered = []
        total_delay = 0

        pos = current_pos[aid]

        for pkg in pkg_list:
            wh_loc = warehouses[pkg["warehouse"]]
            dest = pkg["destination"]

            # Distance: current position to warehouse
            leg1 = get_distance(pos, wh_loc)
            # Distance: warehouse to destination
            leg2 = get_distance(wh_loc, dest)

            trip = leg1 + leg2
            total_dist += trip

            # Bonus: random delay between 0-30 mins
            delay = random.randint(0, 30) if random_delays else 0
            total_delay += delay

            delivered.append({
                "package_id": pkg["id"],
                "warehouse": pkg["warehouse"],
                "destination": pkg["destination"],
                "trip_distance": round(trip, 2),
                "delay_minutes": delay
            })

            # Agent is now at destination
            pos = list(dest)

        count = len(delivered)
        efficiency = round(total_dist / count, 2) if count > 0 else 0.0

        results[aid] = {
            "packages_delivered": count,
            "total_distance": round(total_dist, 2),
            "efficiency": efficiency,
            "delivered_packages": delivered,
            "total_delay_minutes": total_delay
        }

    return results


# --------------------------------------------------
# Step 5: Build final report + find best agent
# Best agent = lowest efficiency (less distance per package)
# --------------------------------------------------

def make_report(results):
    report = {}

    # Only compare agents who actually delivered something
    active = {aid: r for aid, r in results.items() if r["packages_delivered"] > 0}
    best = min(active, key=lambda a: active[a]["efficiency"]) if active else None

    for aid, r in results.items():
        report[aid] = {
            "packages_delivered": r["packages_delivered"],
            "total_distance": r["total_distance"],
            "efficiency": r["efficiency"]
        }

    report["best_agent"] = best
    return report


# --------------------------------------------------
# Bonus: Show a simple ASCII map of the routes
# W = warehouse, A = agent start, D = destination
# --------------------------------------------------

def show_ascii_map(warehouses, agents, agent_packages, size=20):
    all_pts = (list(warehouses.values()) +
               list(agents.values()) +
               [p["destination"] for pkgs in agent_packages.values() for p in pkgs])

    if not all_pts:
        return

    max_x = max(p[0] for p in all_pts) or 1
    max_y = max(p[1] for p in all_pts) or 1

    def to_grid(pt):
        gx = int((pt[0] / max_x) * (size - 1))
        gy = int((pt[1] / max_y) * (size - 1))
        return gx, gy

    grid = [['.' for _ in range(size)] for _ in range(size)]

    for wid, loc in warehouses.items():
        x, y = to_grid(loc)
        grid[size - 1 - y][x] = 'W'

    for aid, loc in agents.items():
        x, y = to_grid(loc)
        grid[size - 1 - y][x] = 'A'

    for pkgs in agent_packages.values():
        for pkg in pkgs:
            x, y = to_grid(pkg["destination"])
            if grid[size - 1 - y][x] == '.':
                grid[size - 1 - y][x] = 'D'

    print("\n--- Route Map (W=Warehouse, A=Agent, D=Destination) ---")
    for row in grid:
        print("  " + "".join(row))
    print("-------------------------------------------------------")


# --------------------------------------------------
# Bonus: Save top agent's deliveries to CSV
# --------------------------------------------------

def save_top_agent_csv(report, results, out_path="top_agent.csv"):
    best = report.get("best_agent")
    if not best:
        return

    deliveries = results[best].get("delivered_packages", [])
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "agent", "package_id", "warehouse",
            "dest_x", "dest_y", "distance", "delay_minutes"
        ])
        writer.writeheader()
        for d in deliveries:
            writer.writerow({
                "agent": best,
                "package_id": d["package_id"],
                "warehouse": d["warehouse"],
                "dest_x": d["destination"][0],
                "dest_y": d["destination"][1],
                "distance": d["trip_distance"],
                "delay_minutes": d.get("delay_minutes", 0)
            })
    print(f"  CSV saved -> {out_path}")


# --------------------------------------------------
# Main function - ties everything together
# --------------------------------------------------

def main(input_file, output_file="report.json"):
    print(f"\nRunning FastBox Simulator...")
    print(f"Input: {input_file}")

    # Load data
    warehouses, agents, packages = load_data(input_file)
    print(f"  Warehouses: {len(warehouses)}, Agents: {len(agents)}, Packages: {len(packages)}")

    # Assign packages
    agent_packages = assign_packages(warehouses, agents, packages)
    print("\nAssignments:")
    for aid, pkgs in agent_packages.items():
        ids = [p["id"] for p in pkgs]
        print(f"  {aid} -> {ids if ids else 'none'}")

    # Run simulation
    results = run_deliveries(warehouses, agents, agent_packages, random_delays=True)

    # Generate report
    report = make_report(results)

    # Save to file
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\nReport:")
    for key, val in report.items():
        if key != "best_agent":
            print(f"  {key}: delivered={val['packages_delivered']}, "
                  f"distance={val['total_distance']}, efficiency={val['efficiency']}")
    print(f"  Best Agent: {report['best_agent']}")

    # Bonus features
    show_ascii_map(warehouses, agents, agent_packages)
    save_top_agent_csv(report, results, output_file.replace(".json", "_top.csv"))

    return report


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "base_case.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "report.json"

    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)

    main(input_file, output_file)
