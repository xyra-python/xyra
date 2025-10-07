#!/usr/bin/env python3
"""
Performance baseline management for Xyra framework benchmarks.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any


class PerformanceBaseline:
    """Manage performance baseline data."""

    def __init__(self, baseline_file: str = "performance_baseline.json"):
        self.baseline_file = baseline_file
        self.baseline_data = self._load_baseline()

    def _load_baseline(self) -> dict[str, Any]:
        """Load baseline data from file."""
        if os.path.exists(self.baseline_file):
            try:
                with open(self.baseline_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load baseline file: {e}")
                return self._create_empty_baseline()
        else:
            return self._create_empty_baseline()

    def _create_empty_baseline(self) -> dict[str, Any]:
        """Create empty baseline structure."""
        return {
            "metadata": {
                "framework": "Xyra",
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "description": "Performance baseline for Xyra framework",
            },
            "baselines": {},
            "history": [],
        }

    def set_baseline(
        self,
        test_name: str,
        metrics: dict[str, Any],
        python_version: str | None = None,
        environment: str = "ci",
    ) -> None:
        """Set performance baseline for a test."""
        if python_version is None:
            python_version = f"python_{sys.version_info.major}.{sys.version_info.minor}"

        key = f"{test_name}_{python_version}_{environment}"

        self.baseline_data["baselines"][key] = {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "python_version": python_version,
            "environment": environment,
        }

        self._save_baseline()

    def get_baseline(
        self, test_name: str, python_version: str | None = None, environment: str = "ci"
    ) -> dict[str, Any]:
        """Get baseline for a test."""
        if python_version is None:
            python_version = f"python_{sys.version_info.major}.{sys.version_info.minor}"

        key = f"{test_name}_{python_version}_{environment}"
        return self.baseline_data["baselines"].get(key, {})

    def compare_with_baseline(
        self,
        test_name: str,
        current_metrics: dict[str, Any],
        python_version: str | None = None,
        environment: str = "ci",
    ) -> dict[str, Any]:
        """Compare current metrics with baseline."""
        baseline = self.get_baseline(test_name, python_version, environment)

        if not baseline:
            return {
                "status": "no_baseline",
                "message": "No baseline found for comparison",
            }

        baseline_metrics = baseline.get("metrics", {})
        comparison = {}

        # Compare key metrics
        for metric_name in [
            "requests_per_second",
            "avg_response_time_ms",
            "p95_response_time_ms",
        ]:
            if metric_name in current_metrics and metric_name in baseline_metrics:
                current_value = current_metrics[metric_name]
                baseline_value = baseline_metrics[metric_name]

                if metric_name == "requests_per_second":
                    # Higher RPS is better
                    change = ((current_value - baseline_value) / baseline_value) * 100
                    status = "improved" if change > 0 else "regressed"
                else:
                    # Lower latency is better
                    change = ((baseline_value - current_value) / baseline_value) * 100
                    status = "improved" if change > 0 else "regressed"

                comparison[metric_name] = {
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": round(change, 2),
                    "status": status,
                }

        # Determine overall status
        regressions = [m for m in comparison.values() if m["status"] == "regressed"]
        improvements = [m for m in comparison.values() if m["status"] == "improved"]

        if regressions:
            overall_status = "regressed"
            message = (
                f"Performance regression detected: {len(regressions)} metrics worsened"
            )
        elif improvements:
            overall_status = "improved"
            message = f"Performance improved: {len(improvements)} metrics better"
        else:
            overall_status = "stable"
            message = "Performance stable, no significant changes"

        return {
            "status": overall_status,
            "message": message,
            "comparison": comparison,
            "baseline_timestamp": baseline.get("timestamp"),
        }

    def _save_baseline(self) -> None:
        """Save baseline data to file."""
        try:
            with open(self.baseline_file, "w") as f:
                json.dump(self.baseline_data, f, indent=2)
        except OSError as e:
            print(f"Error saving baseline: {e}")

    def update_history(self, test_results: dict[str, Any]) -> None:
        """Update performance history."""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "results": test_results,
        }

        self.baseline_data["history"].append(history_entry)

        # Keep only last 50 entries
        if len(self.baseline_data["history"]) > 50:
            self.baseline_data["history"] = self.baseline_data["history"][-50:]

        self._save_baseline()

    def generate_report(self) -> str:
        """Generate performance report."""
        report = []
        report.append("# Xyra Framework Performance Baseline Report")
        report.append("")

        metadata = self.baseline_data.get("metadata", {})
        report.append("## Metadata")
        report.append(f"- **Framework**: {metadata.get('framework', 'Unknown')}")
        report.append(f"- **Version**: {metadata.get('version', 'Unknown')}")
        report.append(f"- **Created**: {metadata.get('created', 'Unknown')}")
        report.append("")

        report.append("## Current Baselines")
        baselines = self.baseline_data.get("baselines", {})
        if baselines:
            for key, data in baselines.items():
                report.append(f"### {key}")
                metrics = data.get("metrics", {})
                report.append(f"- **RPS**: {metrics.get('requests_per_second', 'N/A')}")
                report.append(
                    f"- **Avg Latency**: {metrics.get('avg_response_time_ms', 'N/A')}ms"
                )
                report.append(
                    f"- **P95 Latency**: {metrics.get('p95_response_time_ms', 'N/A')}ms"
                )
                report.append(f"- **Timestamp**: {data.get('timestamp', 'Unknown')}")
                report.append("")
        else:
            report.append("No baselines set yet.")
            report.append("")

        report.append("## Recent History")
        history = self.baseline_data.get("history", [])
        if history:
            recent = history[-5:]  # Last 5 entries
            for entry in recent:
                timestamp = entry.get("timestamp", "Unknown")
                report.append(f"- {timestamp}: Test completed")
        else:
            report.append("No history available.")

        return "\n".join(report)


def main():
    """Command line interface for baseline management."""
    import argparse

    parser = argparse.ArgumentParser(description="Xyra Performance Baseline Manager")
    parser.add_argument(
        "action", choices=["set", "get", "compare", "report"], help="Action to perform"
    )
    parser.add_argument("--test-name", help="Test name for baseline operations")
    parser.add_argument(
        "--baseline-file",
        default="performance_baseline.json",
        help="Baseline file path",
    )
    parser.add_argument(
        "--python-version", help="Python version (auto-detected if not specified)"
    )
    parser.add_argument(
        "--environment", default="ci", help="Environment (ci, local, etc.)"
    )

    args = parser.parse_args()

    baseline = PerformanceBaseline(args.baseline_file)

    if args.action == "set":
        if not args.test_name:
            print("Error: --test-name required for set action")
            return

        # Read metrics from stdin or generate sample
        print("Enter metrics as JSON (or press Enter for sample data):")
        try:
            import sys

            input_line = sys.stdin.readline().strip()
            if input_line:
                metrics = json.loads(input_line)
            else:
                # Sample metrics
                metrics = {
                    "requests_per_second": 4500.0,
                    "avg_response_time_ms": 220.0,
                    "p95_response_time_ms": 280.0,
                }
        except (json.JSONDecodeError, KeyboardInterrupt):
            print("Using sample metrics...")
            metrics = {
                "requests_per_second": 4500.0,
                "avg_response_time_ms": 220.0,
                "p95_response_time_ms": 280.0,
            }

        baseline.set_baseline(
            args.test_name, metrics, args.python_version, args.environment
        )
        print(f"✅ Baseline set for {args.test_name}")

    elif args.action == "get":
        if not args.test_name:
            print("Error: --test-name required for get action")
            return

        data = baseline.get_baseline(
            args.test_name, args.python_version, args.environment
        )
        if data:
            print(json.dumps(data, indent=2))
        else:
            print("No baseline found")

    elif args.action == "compare":
        if not args.test_name:
            print("Error: --test-name required for compare action")
            return

        # Read current metrics
        print("Enter current metrics as JSON:")
        try:
            input_line = input().strip()
            current_metrics = json.loads(input_line)
        except (json.JSONDecodeError, EOFError):
            print("Invalid JSON input")
            return

        result = baseline.compare_with_baseline(
            args.test_name, current_metrics, args.python_version, args.environment
        )
        print(json.dumps(result, indent=2))

    elif args.action == "report":
        report = baseline.generate_report()
        print(report)


if __name__ == "__main__":
    main()
