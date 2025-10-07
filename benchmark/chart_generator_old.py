#!/usr/bin/env python3
"""
Generate performance reports from benchmark results.
"""

import json
import os
from datetime import datetime
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAS_MATPLOTLIB = True
    print("✅ Matplotlib available for chart generation")
except ImportError as e:
    HAS_MATPLOTLIB = False
    plt = None
    sns = None
    print(f"❌ Matplotlib not available: {e}")


class PerformanceReportGenerator:
    """Generate performance reports from benchmark data."""

    def load_benchmark_data(self, file_path: str) -> dict[str, Any]:
        """Load benchmark data from JSON file."""
        try:
            with open(file_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading benchmark data: {e}")
            return {}

    def create_rps_comparison_chart(
        self, data: dict[str, Any], output_file: str = "rps_comparison.png"
    ):
        """Create RPS comparison chart."""
        if not HAS_MATPLOTLIB:
            print("❌ Chart generation disabled - matplotlib not available")
            return

        fig, ax = plt.subplots(figsize=(12, 8))

        endpoints = []
        rps_values = []

        # Extract data from benchmark results
        if isinstance(data, list):
            for result in data:
                if isinstance(result, dict):
                    if "endpoint" in result and "requests_per_second" in result:
                        # Direct result format from parse_benchmark_output
                        endpoints.append(result["endpoint"])
                        rps_values.append(result["requests_per_second"])
                    elif "result" in result:
                        # This is from run_benchmark.py format
                        continue
                    else:
                        for key, value in result.items():
                            if (
                                isinstance(value, dict)
                                and "requests_per_second" in value
                            ):
                                endpoints.append(key.replace("_", " ").title())
                                rps_values.append(value["requests_per_second"])

        if endpoints and rps_values:
            bars = ax.bar(
                endpoints, rps_values, color=sns.color_palette("husl", len(endpoints))
            )
            ax.set_title(
                "Requests Per Second (RPS) by Endpoint", fontsize=16, fontweight="bold"
            )
            ax.set_xlabel("Endpoint", fontsize=12)
            ax.set_ylabel("Requests Per Second", fontsize=12)
            ax.tick_params(axis="x", rotation=45)

            # Add value labels on bars
            for bar, value in zip(bars, rps_values, strict=False):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 50,
                    f"{value:.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"✅ RPS comparison chart saved to {output_file}")
        else:
            print("❌ No RPS data found for chart generation")

    def create_latency_comparison_chart(
        self, data: dict[str, Any], output_file: str = "latency_comparison.png"
    ):
        """Create latency comparison chart."""
        if not HAS_MATPLOTLIB:
            print("❌ Chart generation disabled - matplotlib not available")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

        endpoints = []
        avg_latencies = []
        p95_latencies = []

        # Extract latency data
        if isinstance(data, list):
            for result in data:
                if isinstance(result, dict):
                    if "endpoint" in result and "avg_response_time_ms" in result:
                        # Direct result format from parse_benchmark_output
                        endpoints.append(result["endpoint"])
                        avg_latencies.append(result["avg_response_time_ms"])
                        p95_latencies.append(result.get("p95_response_time_ms", 0))
                    else:
                        for key, value in result.items():
                            if (
                                isinstance(value, dict)
                                and "avg_response_time_ms" in value
                            ):
                                endpoints.append(key.replace("_", " ").title())
                                avg_latencies.append(value["avg_response_time_ms"])
                                p95_latencies.append(
                                    value.get("p95_response_time_ms", 0)
                                )

        if endpoints and avg_latencies:
            x = range(len(endpoints))

            # Average latency
            ax1.bar(x, avg_latencies, color="skyblue", alpha=0.7, label="Average")
            ax1.set_title("Average Response Time", fontsize=14, fontweight="bold")
            ax1.set_xlabel("Endpoint")
            ax1.set_ylabel("Response Time (ms)")
            ax1.set_xticks(x)
            ax1.set_xticklabels(endpoints, rotation=45)

            # P95 latency
            if any(p95_latencies):
                ax2.bar(x, p95_latencies, color="salmon", alpha=0.7, label="P95")
                ax2.set_title("P95 Response Time", fontsize=14, fontweight="bold")
                ax2.set_xlabel("Endpoint")
                ax2.set_ylabel("Response Time (ms)")
                ax2.set_xticks(x)
                ax2.set_xticklabels(endpoints, rotation=45)

            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"✅ Latency comparison chart saved to {output_file}")
        else:
            print("❌ No latency data found for chart generation")

    def create_performance_trend_chart(
        self, baseline_file: str, output_file: str = "performance_trend.png"
    ):
        """Create performance trend chart from baseline history."""
        if not HAS_MATPLOTLIB:
            print("❌ Chart generation disabled - matplotlib not available")
            return

        baseline_data = self.load_benchmark_data(baseline_file)

        if not baseline_data or "history" not in baseline_data:
            print("❌ No baseline history found")
            return

        history = baseline_data["history"]
        if len(history) < 2:
            print("❌ Need at least 2 data points for trend analysis")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        timestamps = []
        rps_values = []
        avg_latencies = []
        p95_latencies = []

        for entry in history[-20:]:  # Last 20 entries
            results = entry.get("results", {})
            if results:
                # Extract metrics from first result
                first_result = next(iter(results.values()), {})
                if isinstance(first_result, dict):
                    timestamps.append(datetime.fromisoformat(entry["timestamp"]))
                    rps_values.append(first_result.get("requests_per_second", 0))
                    avg_latencies.append(first_result.get("avg_response_time_ms", 0))
                    p95_latencies.append(first_result.get("p95_response_time_ms", 0))

        if timestamps and rps_values:
            # RPS Trend
            ax1.plot(timestamps, rps_values, marker="o", linewidth=2, markersize=4)
            ax1.set_title("RPS Trend Over Time", fontweight="bold")
            ax1.set_ylabel("Requests Per Second")
            ax1.tick_params(axis="x", rotation=45)

            # Average Latency Trend
            ax2.plot(
                timestamps,
                avg_latencies,
                marker="s",
                color="orange",
                linewidth=2,
                markersize=4,
            )
            ax2.set_title("Average Latency Trend", fontweight="bold")
            ax2.set_ylabel("Response Time (ms)")
            ax2.tick_params(axis="x", rotation=45)

            # P95 Latency Trend
            ax3.plot(
                timestamps,
                p95_latencies,
                marker="^",
                color="red",
                linewidth=2,
                markersize=4,
            )
            ax3.set_title("P95 Latency Trend", fontweight="bold")
            ax3.set_ylabel("Response Time (ms)")
            ax3.tick_params(axis="x", rotation=45)

            # Summary stats
            ax4.axis("off")
            stats_text = (
                ".1f"
                ".1f"
                ".1f"
                f"""
Performance Summary:
• RPS Range: {min(rps_values):.0f} - {max(rps_values):.0f}
• Avg Latency Range: {min(avg_latencies):.1f}ms - {max(avg_latencies):.1f}ms
• P95 Latency Range: {min(p95_latencies):.1f}ms - {max(p95_latencies):.1f}ms
• Total Data Points: {len(timestamps)}
"""
            )
            ax4.text(
                0.1,
                0.8,
                stats_text,
                transform=ax4.transAxes,
                fontsize=10,
                verticalalignment="top",
                fontfamily="monospace",
            )

            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"✅ Performance trend chart saved to {output_file}")
        else:
            print("❌ Insufficient data for trend analysis")

    def generate_all_charts(
        self,
        benchmark_file: str = "benchmark_results.json",
        baseline_file: str = "performance_baseline.json",
    ):
        """Generate all performance charts."""
        print("📊 Generating Performance Charts...")

        # Load benchmark data
        benchmark_data = self.load_benchmark_data(benchmark_file)

        if benchmark_data:
            # Extract results list from data
            results = benchmark_data.get("results", [])
            if results:
                # Create comparison charts
                self.create_rps_comparison_chart(results, "rps_comparison.png")
                self.create_latency_comparison_chart(results, "latency_comparison.png")

        # Create trend chart if baseline exists
        if os.path.exists(baseline_file):
            self.create_performance_trend_chart(baseline_file, "performance_trend.png")

        print("✅ Chart generation completed!")


def main():
    """Command line interface for chart generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Xyra Performance Chart Generator")
    parser.add_argument(
        "--benchmark-file",
        default="benchmark_results.json",
        help="Benchmark results JSON file",
    )
    parser.add_argument(
        "--baseline-file",
        default="performance_baseline.json",
        help="Performance baseline JSON file",
    )
    parser.add_argument("--output-dir", default=".", help="Output directory for charts")
    parser.add_argument(
        "--chart-type",
        choices=["rps", "latency", "trend", "all"],
        default="all",
        help="Type of chart to generate",
    )

    args = parser.parse_args()

    # Change to output directory
    os.chdir(args.output_dir)

    generator = PerformanceReportGenerator()

    if args.chart_type == "all":
        generator.generate_all_charts(args.benchmark_file, args.baseline_file)
    elif args.chart_type == "rps":
        data = generator.load_benchmark_data(args.benchmark_file)
        results = data.get("results", []) if isinstance(data, dict) else data
        generator.create_rps_comparison_chart(results)
    elif args.chart_type == "latency":
        data = generator.load_benchmark_data(args.benchmark_file)
        results = data.get("results", []) if isinstance(data, dict) else data
        generator.create_latency_comparison_chart(results)
    elif args.chart_type == "trend":
        generator.create_performance_trend_chart(args.baseline_file)


if __name__ == "__main__":
    main()
