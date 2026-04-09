import os
import re
import subprocess
import time

def run_benchmark(name, start_cmd, port, path="/"):
    os.system(f"kill -9 $(lsof -t -i:{port}) 2>/dev/null || true")

    print(f"Starting {name} server...")
    server_proc = subprocess.Popen(start_cmd, shell=True)
    time.sleep(5) # Wait for server to start

    print(f"Running benchmark for {name} on path {path}...")
    try:
        result = subprocess.run(
            f"wrk -t4 -c100 -d10s http://127.0.0.1:{port}{path}",
            shell=True,
            capture_output=True,
            text=True
        )
        output = result.stdout

        req_sec_match = re.search(r"Requests/sec:\s+([\d.]+)", output)
        latency_match = re.search(r"Latency\s+([\d.]+[a-zA-Z]+)", output)

        req_sec = float(req_sec_match.group(1)) if req_sec_match else 0
        latency = latency_match.group(1) if latency_match else "N/A"

        print(f"{name} ({path}) -> Requests/sec: {req_sec}, Latency: {latency}")
        return {"name": name, "path": path, "req_sec": req_sec, "latency": latency}
    finally:
        server_proc.terminate()
        os.system("pkill -f 'pypy.*app_'")
        os.system(f"kill -9 $(lsof -t -i:{port}) 2>/dev/null || true")
        time.sleep(2)

json_benchmarks = []
text_benchmarks = []
html_benchmarks = []

json_benchmarks.append(run_benchmark("Socketify", "uv run --python pypy3 app_socketify.py", 3000, "/"))
json_benchmarks.append(run_benchmark("Xyra", "uv run --python pypy3 app_xyra.py", 8000, "/"))

text_benchmarks.append(run_benchmark("Socketify", "uv run --python pypy3 app_socketify.py", 3000, "/text"))
text_benchmarks.append(run_benchmark("Xyra", "uv run --python pypy3 app_xyra.py", 8000, "/text"))

html_benchmarks.append(run_benchmark("Socketify", "uv run --python pypy3 app_socketify.py", 3000, "/html"))
html_benchmarks.append(run_benchmark("Xyra", "uv run --python pypy3 app_xyra.py", 8000, "/html"))

with open("benchmark_report_pypy.md", "w") as f:
    f.write("# Framework Benchmark Report (PyPy3)\n\n")
    f.write("A performance comparison between Socketify and Xyra using PyPy3.\n\n")
    f.write("## Setup\n")
    f.write("- **Tool**: wrk\n")
    f.write("- **Threads**: 4\n")
    f.write("- **Connections**: 100\n")
    f.write("- **Duration**: 10s\n\n")

    f.write("## Results (JSON)\n\n")
    f.write("| Framework | Requests/sec | Avg Latency |\n")
    f.write("|-----------|--------------|-------------|\n")
    for b in json_benchmarks:
        f.write(f"| {b['name']} | {b['req_sec']:,.2f} | {b['latency']} |\n")
    f.write("\n")

    f.write("## Results (Plain Text)\n\n")
    f.write("| Framework | Requests/sec | Avg Latency |\n")
    f.write("|-----------|--------------|-------------|\n")
    for b in text_benchmarks:
        f.write(f"| {b['name']} | {b['req_sec']:,.2f} | {b['latency']} |\n")
    f.write("\n")

    f.write("## Results (HTML)\n\n")
    f.write("| Framework | Requests/sec | Avg Latency |\n")
    f.write("|-----------|--------------|-------------|\n")
    for b in html_benchmarks:
        f.write(f"| {b['name']} | {b['req_sec']:,.2f} | {b['latency']} |\n")

print("Done benchmarking!")
