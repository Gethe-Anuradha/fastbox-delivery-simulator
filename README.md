# FastBox Delivery System Simulator

A Python simulation of a logistics delivery system for **FastBox** — a fictional delivery company.

## Problem Summary

Simulate one day of delivery operations:
- Multiple warehouses, agents, and packages
- Assign packages to nearest agents (Euclidean distance)
- Simulate pickup and delivery routes
- Output a report with distance totals and best agent

---

## Project Structure

```
fastbox_delivery/
├── delivery_simulator.py   # Main simulation code
├── test_simulator.py       # Unit tests + integration tests
├── base_case.json          # Sample input (from assignment)
├── test_cases/             # 10 provided test case JSONs
│   ├── test_case_1.json
│   ├── ...
│   └── test_case_10.json
└── README.md               # This file
```

---

## How to Run

### Basic (uses base_case.json):
```bash
python delivery_simulator.py
```

### With custom input:
```bash
python delivery_simulator.py base_case.json report.json
python delivery_simulator.py test_cases/test_case_1.json output_1.json
```

### Run tests:
```bash
python -m pytest test_simulator.py -v
# or
python test_simulator.py
```

---

## Input Format

Two formats are supported automatically:

**Format A (dict-style):**
```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75] },
  "agents": { "A1": [5, 5], "A2": [60, 60] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

**Format B (list-style):**
```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents": [{ "id": "A1", "location": [5, 5] }],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
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

---

## Bonus Features Implemented

| Feature | Description |
|---|---|
| ✅ Random Delays | 0–30 min random delay per delivery, shown in summary |
| ✅ ASCII Route Map | Visual grid showing warehouses (W), agents (A), destinations (D) |
| ✅ New Agent Mid-Day | `add_new_agent()` utility function |
| ✅ CSV Export | Top performer's deliveries exported to `*_top_performer.csv` |

---

## Assumptions (as instructed)

1. Each package is assigned to the **nearest agent** by Euclidean distance from agent to warehouse.
2. Agents deliver packages **sequentially** — after each delivery, position updates to destination.
3. **Tie-breaking**: agent with fewer assigned packages wins; alphabetically first on equal count.
4. `efficiency = total_distance / packages_delivered` — lower is better.
5. `best_agent` = agent with lowest efficiency score.
6. Both `"warehouse"` and `"warehouse_id"` keys in packages are handled.
7. Both dict and list input formats are handled automatically.
8. Random delays are **0–30 minutes** per delivery (uniform distribution).
9. A new agent joining mid-day does not receive already-assigned packages.

---

## Requirements

- Python 3.8+
- No third-party libraries required (stdlib only: `json`, `math`, `csv`, `random`, `sys`, `os`)

For tests: `pytest` (optional, `unittest` works standalone too)

---

## Author

Assignment: Python Developer Round — Nexgensis Technologies Pvt. Ltd.
