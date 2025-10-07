#!/usr/bin/env python3
"""
Benchmark client for load testing Xyra framework.
"""

import argparse
import asyncio
import statistics
import time
from typing import Any

import aiohttp


async def make_request(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict | None = None,
) -> float:
    """Make a single HTTP request and return response time in milliseconds."""
    start_time = time.time()

    try:
        async with session.request(
            method, url, headers=headers, json=json_data
        ) as response:
            await response.text()  # Consume response
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
    except Exception as e:
        print(f"Request failed: {e}")
        return float("inf")


async def benchmark_endpoint(
    url: str,
    num_requests: int,
    concurrency: int,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict | None = None,
) -> dict[str, Any]:
    """Benchmark a single endpoint."""

    async def worker(session: aiohttp.ClientSession, request_id: int) -> float:
        return await make_request(session, url, method, headers, json_data)

    connector = aiohttp.TCPConnector(limit=concurrency * 2)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []

        # Create tasks
        for i in range(num_requests):
            task = asyncio.create_task(worker(session, i))
            tasks.append(task)

        # Execute tasks with concurrency control
        semaphore = asyncio.Semaphore(concurrency)

        async def limited_worker(task):
            async with semaphore:
                return await task

        start_time = time.time()
        results = await asyncio.gather(*[limited_worker(task) for task in tasks])
        total_time = time.time() - start_time

        # Filter out failed requests
        successful_results = [r for r in results if r != float("inf")]
        failed_count = len(results) - len(successful_results)

        if not successful_results:
            return {
                "error": "All requests failed",
                "total_requests": num_requests,
                "failed_requests": failed_count,
            }

        # Calculate statistics
        avg_time = statistics.mean(successful_results)
        median_time = statistics.median(successful_results)
        min_time = min(successful_results)
        max_time = max(successful_results)
        p95_time = statistics.quantiles(successful_results, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(successful_results, n=100)[
            98
        ]  # 99th percentile

        rps = len(successful_results) / total_time

        return {
            "endpoint": url,
            "method": method,
            "total_requests": num_requests,
            "successful_requests": len(successful_results),
            "failed_requests": failed_count,
            "total_time_seconds": round(total_time, 2),
            "requests_per_second": round(rps, 2),
            "avg_response_time_ms": round(avg_time, 2),
            "median_response_time_ms": round(median_time, 2),
            "min_response_time_ms": round(min_time, 2),
            "max_response_time_ms": round(max_time, 2),
            "p95_response_time_ms": round(p95_time, 2),
            "p99_response_time_ms": round(p99_time, 2),
        }


async def run_benchmarks(
    base_url: str, num_requests: int = 1000, concurrency: int = 10
):
    """Run comprehensive benchmarks."""

    print("🚀 Starting Xyra Framework Benchmark")
    print(f"📍 Target: {base_url}")
    print(f"📊 Requests: {num_requests}, Concurrency: {concurrency}")
    print("-" * 60)

    benchmarks = [
        {"name": "Simple Hello World", "url": f"{base_url}/", "method": "GET"},
        {"name": "JSON Response", "url": f"{base_url}/json", "method": "GET"},
        {
            "name": "JSON POST",
            "url": f"{base_url}/json",
            "method": "POST",
            "json_data": {"test": "data", "numbers": [1, 2, 3]},
        },
        {
            "name": "Headers Access",
            "url": f"{base_url}/headers",
            "method": "GET",
            "headers": {
                "User-Agent": "BenchmarkClient/1.0",
                "Accept": "application/json",
            },
        },
        {
            "name": "Query Parameters",
            "url": f"{base_url}/query?page=1&limit=10&search=test",
            "method": "GET",
        },
        {"name": "Route Parameters", "url": f"{base_url}/user/123", "method": "GET"},
    ]

    results = []

    for benchmark in benchmarks:
        print(f"🔄 Testing: {benchmark['name']}")

        result = await benchmark_endpoint(
            benchmark["url"],
            num_requests,
            concurrency,
            benchmark.get("method", "GET"),
            benchmark.get("headers"),
            benchmark.get("json_data"),
        )

        results.append({"name": benchmark["name"], **result})

        if "error" in result:
            print(f"❌ {benchmark['name']}: {result['error']}")
        else:
            print(
                f"✅ {benchmark['name']}: {result['requests_per_second']} RPS, "
                f"{result['avg_response_time_ms']}ms avg"
            )

        print()

    return results


def print_summary(results: list[dict[str, Any]]):
    """Print benchmark summary."""
    print("📊 BENCHMARK SUMMARY")
    print("=" * 80)

    total_rps = 0
    total_requests = 0

    for result in results:
        if "error" not in result:
            print(
                f"{result['name']:<20} | {result['requests_per_second']:>8.1f} RPS | "
                f"{result['avg_response_time_ms']:>6.1f}ms | "
                f"{result['p95_response_time_ms']:>6.1f}ms P95"
            )
            total_rps += result["requests_per_second"]
            total_requests += result["successful_requests"]

    print("-" * 80)
    avg_rps = total_rps / len([r for r in results if "error" not in r])
    print(f"{'AVERAGE':<20} | {avg_rps:>8.1f} RPS")
    print("=" * 80)


def main():
    """Main benchmark client."""
    parser = argparse.ArgumentParser(description="Xyra Framework Benchmark Client")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of the server to benchmark",
    )
    parser.add_argument(
        "--requests", type=int, default=1000, help="Number of requests per endpoint"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Number of concurrent requests"
    )
    parser.add_argument("--output", help="Output results to JSON file")

    args = parser.parse_args()

    # Run benchmarks
    results = asyncio.run(run_benchmarks(args.url, args.requests, args.concurrency))

    # Print summary
    print_summary(results)

    # Save to file if requested
    if args.output:
        import json

        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to {args.output}")


if __name__ == "__main__":
    main()
