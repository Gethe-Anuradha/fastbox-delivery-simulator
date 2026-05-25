"""
Test Suite for FastBox Delivery Simulator
==========================================
Tests all 10 provided test cases + base_case.
Also unit tests for distance calculation, parsing, and assignment.
"""

import json
import os
import sys
import math
import unittest
import tempfile

# Add parent folder to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from delivery_simulator import (
    euclidean_distance, parse_input,
    assign_packages_to_agents, simulate_deliveries,
    generate_report, run_simulation
)


class TestEuclideanDistance(unittest.TestCase):
    def test_same_point(self):
        self.assertAlmostEqual(euclidean_distance([0, 0], [0, 0]), 0.0)

    def test_horizontal(self):
        self.assertAlmostEqual(euclidean_distance([0, 0], [3, 0]), 3.0)

    def test_vertical(self):
        self.assertAlmostEqual(euclidean_distance([0, 0], [0, 4]), 4.0)

    def test_diagonal(self):
        # 3-4-5 triangle
        self.assertAlmostEqual(euclidean_distance([0, 0], [3, 4]), 5.0)

    def test_negative_coords(self):
        self.assertAlmostEqual(euclidean_distance([-1, -1], [2, 3]), 5.0)


class TestParsing(unittest.TestCase):
    def test_dict_format(self):
        data = {
            "warehouses": {"W1": [0, 0], "W2": [10, 10]},
            "agents": {"A1": [5, 5]},
            "packages": [{"id": "P1", "warehouse": "W1", "destination": [3, 3]}]
        }
        wh, ag, pk = parse_input(data)
        self.assertEqual(wh["W1"], [0, 0])
        self.assertEqual(ag["A1"], [5, 5])
        self.assertEqual(pk[0]["warehouse"], "W1")

    def test_list_format(self):
        data = {
            "warehouses": [{"id": "W1", "location": [0, 0]}],
            "agents": [{"id": "A1", "location": [5, 5]}],
            "packages": [{"id": "P1", "warehouse_id": "W1", "destination": [3, 3]}]
        }
        wh, ag, pk = parse_input(data)
        self.assertEqual(wh["W1"], [0, 0])
        self.assertEqual(pk[0]["warehouse"], "W1")


class TestAssignment(unittest.TestCase):
    def test_nearest_agent_assigned(self):
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [1, 1], "A2": [100, 100]}
        packages = [{"id": "P1", "warehouse": "W1", "destination": [5, 5]}]
        result = assign_packages_to_agents(warehouses, agents, packages)
        # A1 is closer to W1
        self.assertIn({"id": "P1", "warehouse": "W1", "destination": [5, 5]},
                      result["A1"])
        self.assertEqual(result["A2"], [])

    def test_all_packages_assigned(self):
        warehouses = {"W1": [0, 0], "W2": [50, 50]}
        agents = {"A1": [5, 5], "A2": [45, 45]}
        packages = [
            {"id": "P1", "warehouse": "W1", "destination": [10, 10]},
            {"id": "P2", "warehouse": "W2", "destination": [40, 40]},
            {"id": "P3", "warehouse": "W1", "destination": [2, 2]},
        ]
        result = assign_packages_to_agents(warehouses, agents, packages)
        total = sum(len(v) for v in result.values())
        self.assertEqual(total, 3)


class TestSimulation(unittest.TestCase):
    def test_distance_correctness(self):
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [3, 4]}  # dist to W1 = 5
        packages = [{"id": "P1", "warehouse": "W1", "destination": [3, 4]}]  # back to start = 5
        assignments = {"A1": packages}
        results = simulate_deliveries(warehouses, agents, assignments)
        # 5 (to warehouse) + 5 (to destination) = 10
        self.assertAlmostEqual(results["A1"]["total_distance"], 10.0)
        self.assertEqual(results["A1"]["packages_delivered"], 1)

    def test_empty_agent(self):
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [0, 0], "A2": [5, 5]}
        assignments = {"A1": [], "A2": []}
        results = simulate_deliveries(warehouses, agents, assignments)
        self.assertEqual(results["A1"]["packages_delivered"], 0)
        self.assertEqual(results["A1"]["total_distance"], 0.0)


class TestReport(unittest.TestCase):
    def test_best_agent_is_most_efficient(self):
        sim_results = {
            "A1": {"packages_delivered": 2, "total_distance": 10.0, "efficiency": 5.0,
                   "delivered_packages": []},
            "A2": {"packages_delivered": 2, "total_distance": 20.0, "efficiency": 10.0,
                   "delivered_packages": []},
        }
        report = generate_report(sim_results)
        self.assertEqual(report["best_agent"], "A1")

    def test_no_packages(self):
        sim_results = {
            "A1": {"packages_delivered": 0, "total_distance": 0.0, "efficiency": 0.0,
                   "delivered_packages": []},
        }
        report = generate_report(sim_results)
        self.assertIsNone(report["best_agent"])


class TestAllTestCases(unittest.TestCase):
    """Run all provided test case JSON files."""

    TEST_CASE_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_cases"
    )

    def _run_case(self, filepath):
        """Helper to run a single test case and validate output."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            report = run_simulation(
                input_path=filepath,
                output_path=tmp_path,
                add_random_delays=False,
                export_csv=False,
                show_ascii=False
            )
            # Validate report structure
            with open(tmp_path) as f:
                saved = json.load(f)

            # Check basic structure
            self.assertIn("best_agent", saved)

            # Check all packages are accounted for
            with open(filepath) as f:
                input_data = json.load(f)
            _, _, packages = parse_input(input_data)
            total_delivered = sum(
                v["packages_delivered"]
                for k, v in saved.items()
                if k != "best_agent"
            )
            self.assertEqual(total_delivered, len(packages),
                             f"Package count mismatch in {filepath}")
        finally:
            os.unlink(tmp_path)

    def test_base_case(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_case.json")
        if os.path.exists(path):
            self._run_case(path)

    def test_all_test_cases(self):
        if not os.path.exists(self.TEST_CASE_DIR):
            self.skipTest("test_cases/ directory not found")
        for i in range(1, 11):
            fname = f"test_case_{i}.json"
            fpath = os.path.join(self.TEST_CASE_DIR, fname)
            if os.path.exists(fpath):
                with self.subTest(file=fname):
                    self._run_case(fpath)


if __name__ == "__main__":
    unittest.main(verbosity=2)
