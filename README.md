# FastBox Delivery Simulator

A Python project that simulates one day of delivery operations for a fictional company called **FastBox**.

## What it does

- Reads warehouse, agent, and package data from a JSON file
- Assigns each package to the nearest available agent
- Simulates pickup and delivery, tracking total distance per agent
- Outputs a report showing deliveries, distances, and the best agent

---

## How to run

```bash
# Default (uses base_case.json)
python delivery_simulator.py

# With custom input
python delivery_simulator.py base_case.json report.json
python delivery_simulator.py test_cases/test_case_1.json output.json
```

## How to run tests

```bash
python test_simulator.py
```

---

## Input format

Two formats are supported:

**Dict style:**
```json
{
  "warehouses": { "W1": [0, 0] },
  "agents": { "A1": [5, 5] },
  "packages": [{ "id": "P1", "warehouse": "W1", "destination": [10, 10] }]
}
```

**List style:**
```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents": [{ "id": "A1", "location": [5, 5] }],
  "packages": [{ "id": "P1", "warehouse_id": "W1", "destination": [10, 10] }]
}
```

---

## Output (report.json)

```json
{
  "A1": { "packages_delivered": 2, "total_distance": 85.32, "efficiency": 42.66 },
  "A2": { "packages_delivered": 2, "total_distance": 120.12, "efficiency": 60.06 },
  "A3": { "packages_delivered": 1, "total_distance": 50.0, "efficiency": 50.0 },
  "best_agent": "A1"
}
```

`efficiency` = total_distance / packages_delivered. Lower is better.

---

## Bonus features

- Random delivery delays (0–30 mins per package)
- ASCII grid map showing warehouses, agents, destinations
- CSV export of best agent's deliveries

---

## Assumptions

- Nearest agent = closest to the package's warehouse (Euclidean distance)
- Agents deliver one package at a time; position updates after each delivery
- Tie-breaking: agent with fewer assigned packages wins; alphabetical if still tied
- Both `"warehouse"` and `"warehouse_id"` keys are handled in package data
- No external libraries needed — only Python standard library

---

## Requirements

Python 3.8+, no third-party packages needed.
