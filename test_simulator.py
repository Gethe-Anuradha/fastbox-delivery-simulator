"""
Tests for FastBox Delivery Simulator
"""

import json
import os
import sys
import math
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from delivery_simulator import (
    get_distance, load_data, assign_packages,
    run_deliveries, make_report, main
)


class TestDistance(unittest.TestCase):

    def test_zero_distance(self):
        self.assertEqual(get_distance([0, 0], [0, 0]), 0)

    def test_horizontal_line(self):
        self.assertAlmostEqual(get_distance([0, 0], [5, 0]), 5.0)

    def test_vertical_line(self):
        self.assertAlmostEqual(get_distance([0, 0], [0, 5]), 5.0)

    def test_345_triangle(self):
        # classic 3-4-5 right triangle
        self.assertAlmostEqual(get_distance([0, 0], [3, 4]), 5.0)

    def test_reverse_direction(self):
        # distance should be same either way
        self.assertAlmostEqual(
            get_distance([10, 20], [5, 5]),
            get_distance([5, 5], [10, 20])
        )


class TestAssignment(unittest.TestCase):

    def test_closer_agent_gets_package(self):
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [1, 0], "A2": [50, 50]}
        packages = [{"id": "P1", "warehouse": "W1", "destination": [2, 2]}]

        result = assign_packages(warehouses, agents, packages)
        # A1 is closer to W1
        self.assertEqual(len(result["A1"]), 1)
        self.assertEqual(len(result["A2"]), 0)

    def test_all_packages_assigned(self):
        warehouses = {"W1": [0, 0], "W2": [100, 100]}
        agents = {"A1": [5, 5], "A2": [90, 90]}
        packages = [
            {"id": "P1", "warehouse": "W1", "destination": [10, 10]},
            {"id": "P2", "warehouse": "W2", "destination": [80, 80]},
            {"id": "P3", "warehouse": "W1", "destination": [3, 3]},
        ]
        result = assign_packages(warehouses, agents, packages)
        total = sum(len(v) for v in result.values())
        self.assertEqual(total, 3)


class TestDeliveries(unittest.TestCase):

    def test_distance_is_correct(self):
        # Agent at (3,4), warehouse at (0,0), destination at (3,4)
        # leg1 = 5, leg2 = 5, total = 10
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [3, 4]}
        packages = [{"id": "P1", "warehouse": "W1", "destination": [3, 4]}]
        assigned = {"A1": packages}

        results = run_deliveries(warehouses, agents, assigned)
        self.assertAlmostEqual(results["A1"]["total_distance"], 10.0)

    def test_agent_with_no_packages(self):
        warehouses = {"W1": [0, 0]}
        agents = {"A1": [0, 0]}
        assigned = {"A1": []}

        results = run_deliveries(warehouses, agents, assigned)
        self.assertEqual(results["A1"]["packages_delivered"], 0)
        self.assertEqual(results["A1"]["total_distance"], 0.0)


class TestReport(unittest.TestCase):

    def test_best_agent_has_lowest_efficiency(self):
        results = {
            "A1": {"packages_delivered": 2, "total_distance": 20.0,
                   "efficiency": 10.0, "delivered_packages": [], "total_delay_minutes": 0},
            "A2": {"packages_delivered": 2, "total_distance": 40.0,
                   "efficiency": 20.0, "delivered_packages": [], "total_delay_minutes": 0},
        }
        report = make_report(results)
        self.assertEqual(report["best_agent"], "A1")

    def test_no_deliveries_returns_none(self):
        results = {
            "A1": {"packages_delivered": 0, "total_distance": 0,
                   "efficiency": 0, "delivered_packages": [], "total_delay_minutes": 0},
        }
        report = make_report(results)
        self.assertIsNone(report["best_agent"])


class TestAllTestCases(unittest.TestCase):
    """Run all 10 provided test case files"""

    TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases")

    def _check_case(self, filepath):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        try:
            report = main(filepath, tmp.name)
            with open(tmp.name) as f:
                saved = json.load(f)

            self.assertIn("best_agent", saved)

            # Check total packages match
            with open(filepath) as f:
                raw = json.load(f)
            from delivery_simulator import load_data
            _, _, pkgs = load_data(filepath)
            total = sum(v["packages_delivered"] for k, v in saved.items() if k != "best_agent")
            self.assertEqual(total, len(pkgs))
        finally:
            os.unlink(tmp.name)

    def test_base_case(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_case.json")
        if os.path.exists(path):
            self._check_case(path)

    def test_cases_1_to_10(self):
        if not os.path.exists(self.TEST_DIR):
            self.skipTest("test_cases/ folder not found")
        for i in range(1, 11):
            fname = f"test_case_{i}.json"
            fpath = os.path.join(self.TEST_DIR, fname)
            if os.path.exists(fpath):
                with self.subTest(file=fname):
                    self._check_case(fpath)


if __name__ == "__main__":
    unittest.main(verbosity=2)
