#!/usr/bin/env python3
"""
Run comprehensive benchmarks for Xyra framework and compare results.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any


def run_server(server_type: str = "simple", port: int = 8000) -> subprocess.Popen:
    """Start the benchmark server."""
    cmd = [sys.executable, "server.py", "--type", server_type, "--port", str(port)]
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))


def run_client(
    base_url: str, requests: int = 1000, concurrency: int = 10
) -> dict[str, Any]:
    """Run the benchmark client."""
    cmd = [
        sys.executable,
        "client.py",
        "--url",
        base_url,
        "--requests",
        str(requests),
        "--concurrency",
        str(concurrency),
    ]

    result = subprocess.run(
        cmd, cwd=os.path.dirname(__file__), capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"❌ Client failed: {result.stderr}")
        return {}

    # Parse output to extract results
    # This is a simple implementation - in production you'd want better parsing
    return {"raw_output": result.stdout, "returncode": result.returncode}


def benchmark_version(
    version_name: str,
    server_type: str = "simple",
    requests: int = 1000,
    concurrency: int = 10,
) -> dict[str, Any]:
    """Run benchmark for a specific version."""
    print(f"🧪 Benchmarking {version_name} ({server_type})")

    port = 8000
    base_url = f"http://127.0.0.1:{port}"

    # Start server
    print("🚀 Starting server...")
    server_process = run_server(server_type, port)

    # Wait for server to start
    time.sleep(2)

    try:
        # Run client benchmark
        print("📊 Running client benchmark...")
        result = run_client(base_url, requests, concurrency)

        return {
            "version": version_name,
            "server_type": server_type,
            "requests": requests,
            "concurrency": concurrency,
            "result": result,
            "timestamp": time.time(),
        }

    finally:
        # Stop server
        print("🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        time.sleep(1)


def run_comparison_benchmarks():
    """Run benchmarks before and after optimization."""
    print("🔬 Xyra Framework Performance Benchmark")
    print("=" * 60)

    results = []

    # Benchmark configurations
    configs = [
        {"server_type": "simple", "requests": 5000, "concurrency": 50},
        {"server_type": "middleware", "requests": 3000, "concurrency": 30},
    ]

    for config in configs:
        print(f"\n📋 Testing configuration: {config['server_type']}")
        print(
            f"   Requests: {config['requests']}, Concurrency: {config['concurrency']}"
        )

        # Benchmark current version
        result = benchmark_version(
            "Current Version",
            config["server_type"],
            config["requests"],
            config["concurrency"],
        )
        results.append(result)

        print("✅ Benchmark completed\n")

    return results


def save_results(results: list[dict[str, Any]], filename: str):
    """Save benchmark results to file."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved to {filename}")


def load_results(filename: str) -> list[dict[str, Any]]:
    """Load benchmark results from file."""
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)
    return []


def compare_results(
    before_results: list[dict[str, Any]], after_results: list[dict[str, Any]]
):
    """Compare benchmark results and show improvements."""
    print("\n📊 PERFORMANCE COMPARISON")
    print("=" * 80)

    if not before_results or not after_results:
        print("❌ Insufficient data for comparison")
        return

    # Group results by configuration
    before_by_config = {
        f"{r['server_type']}_{r['requests']}_{r['concurrency']}": r
        for r in before_results
    }
    after_by_config = {
        f"{r['server_type']}_{r['requests']}_{r['concurrency']}": r
        for r in after_results
    }

    for config_key in before_by_config:
        if config_key in after_by_config:
            before = before_by_config[config_key]
            after = after_by_config[config_key]

            print(
                f"Configuration: {before['server_type']} "
                f"({before['requests']} req, {before['concurrency']} conc)"
            )

            # Extract RPS from raw output (simplified parsing)
            before_rps = extract_rps_from_output(before["result"].get("raw_output", ""))
            after_rps = extract_rps_from_output(after["result"].get("raw_output", ""))

            if before_rps and after_rps:
                improvement = ((after_rps - before_rps) / before_rps) * 100
                print(f"   Before: {before_rps:.1f} RPS")
                print(f"   After:  {after_rps:.1f} RPS")
                print(f"   Improvement: {improvement:.1f}%")
            print()


def extract_rps_from_output(output: str) -> float:
    """Extract RPS value from client output (simplified)."""
    lines = output.split("\n")
    for line in lines:
        if "RPS" in line and "|" in line:
            parts = line.split("|")
            if len(parts) >= 2:
                try:
                    return float(parts[1].strip().split()[0])
                except (ValueError, IndexError):
                    continue
    return 0.0


def main():
    """Main benchmark runner."""
    parser = argparse.ArgumentParser(description="Xyra Framework Benchmark Runner")
    parser.add_argument(
        "--mode",
        choices=["single", "compare", "before", "after"],
        default="single",
        help="Benchmark mode",
    )
    parser.add_argument(
        "--server-type",
        default="simple",
        choices=["simple", "middleware", "template"],
        help="Type of server to benchmark",
    )
    parser.add_argument(
        "--requests", type=int, default=1000, help="Number of requests per endpoint"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Number of concurrent requests"
    )
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    if args.mode == "single":
        # Run single benchmark
        result = benchmark_version(
            "Single Run", args.server_type, args.requests, args.concurrency
        )

        if args.output:
            save_results([result], args.output)

    elif args.mode == "before":
        # Run benchmark before optimization
        results = run_comparison_benchmarks()
        save_results(results, "benchmark_before.json")
        print("📋 Before optimization results saved")

    elif args.mode == "after":
        # Run benchmark after optimization
        results = run_comparison_benchmarks()
        save_results(results, "benchmark_after.json")
        print("📋 After optimization results saved")

    elif args.mode == "compare":
        # Compare before and after results
        before_results = load_results("benchmark_before.json")
        after_results = load_results("benchmark_after.json")
        compare_results(before_results, after_results)


if __name__ == "__main__":
    main()
