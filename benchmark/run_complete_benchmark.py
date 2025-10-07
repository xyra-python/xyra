#!/usr/bin/env python3
"""
Complete benchmark runner that includes chart generation and baseline comparison.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any


def run_command(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    print(f"🔄 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        return result
    print("✅ Command completed successfully")
    return result


def run_benchmarks():
    """Run comprehensive benchmarks."""
    print("🚀 Starting Complete Xyra Framework Benchmark Suite")
    print("=" * 60)

    benchmark_dir = os.path.dirname(os.path.abspath(__file__))

    # Run different benchmark configurations
    configs = [
        {
            "name": "Simple Server",
            "cmd": [
                "python",
                "run_benchmark.py",
                "--mode=single",
                "--requests=2000",
                "--concurrency=20",
                "--server-type=simple",
            ],
        },
        {
            "name": "Middleware Server",
            "cmd": [
                "python",
                "run_benchmark.py",
                "--mode=single",
                "--requests=1500",
                "--concurrency=15",
                "--server-type=middleware",
            ],
        },
        {
            "name": "Template Server",
            "cmd": [
                "python",
                "run_benchmark.py",
                "--mode=single",
                "--requests=1000",
                "--concurrency=10",
                "--server-type=template",
            ],
        },
    ]

    all_results = []

    for config in configs:
        print(f"\n📋 Running {config['name']} Benchmark")
        print("-" * 40)

        result = run_command(config["cmd"], benchmark_dir)
        if result.returncode == 0:
            # Try to extract results from output
            results = parse_benchmark_output(result.stdout)
            if results:
                all_results.extend(results)
        else:
            print(f"❌ {config['name']} benchmark failed")

    # Save combined results
    if all_results:
        output_file = os.path.join(benchmark_dir, "complete_benchmark_results.json")
        with open(output_file, "w") as f:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "results": all_results},
                f,
                indent=2,
            )
        print(f"💾 Results saved to {output_file}")

        # Generate charts
        print("\n📊 Generating Performance Charts")
        print("-" * 40)
        chart_cmd = [
            "python",
            "chart_generator.py",
            "--benchmark-file=complete_benchmark_results.json",
        ]
        run_command(chart_cmd, benchmark_dir)

        # Update baseline
        print("\n📈 Updating Performance Baseline")
        print("-" * 40)
        baseline_cmd = [
            "python",
            "baseline.py",
            "set",
            "--test-name=complete_benchmark",
        ]
        run_command(baseline_cmd, benchmark_dir)

        # Generate baseline report
        report_cmd = ["python", "baseline.py", "report"]
        result = run_command(report_cmd, benchmark_dir)
        if result.returncode == 0:
            report_file = os.path.join(benchmark_dir, "baseline_report.md")
            with open(report_file, "w") as f:
                f.write(result.stdout)
            print(f"📄 Baseline report saved to {report_file}")

    print("\n🎉 Complete Benchmark Suite Finished!")
    print("=" * 60)
    print("Generated files:")
    print("- complete_benchmark_results.json")
    print("- rps_comparison.png")
    print("- latency_comparison.png")
    print("- performance_trend.png (if baseline exists)")
    print("- baseline_report.md")


def parse_benchmark_output(output: str) -> list[dict[str, Any]]:
    """Parse benchmark output to extract results."""
    results = []

    # This is a simple parser - in production you'd want more robust parsing
    lines = output.split("\n")

    for line in lines:
        line = line.strip()
        if "|" in line and "RPS" in line:
            # This is a results table line
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 4:
                try:
                    endpoint = parts[0]
                    rps = float(parts[1].split()[0])
                    avg_latency = float(parts[2].split()[0])
                    p95_latency = float(parts[3].split()[0])

                    results.append(
                        {
                            "endpoint": endpoint,
                            "requests_per_second": rps,
                            "avg_response_time_ms": avg_latency,
                            "p95_response_time_ms": p95_latency,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except (ValueError, IndexError):
                    continue

    return results


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Xyra Complete Benchmark Runner")
            print("Usage: python run_complete_benchmark.py")
            print("Runs comprehensive benchmarks and generates charts/reports")
            return

    run_benchmarks()


if __name__ == "__main__":
    main()
