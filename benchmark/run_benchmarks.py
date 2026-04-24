import os
import re
import subprocess
import time
import signal
import shlex


def kill_process_on_port(port):
    try:
        output = subprocess.check_output(['lsof', '-t', f'-i:{port}']).decode('utf-8').strip()
        if output:
            for pid in output.split():
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except OSError:
                    pass
    except subprocess.CalledProcessError:
        pass


def run_benchmark(name, start_cmd, port, path="/"):
    # Kill any process listening on the target port
    kill_process_on_port(port)

    print(f"Starting {name} server...")
    server_proc = subprocess.Popen(shlex.split(start_cmd), shell=False)
    time.sleep(5) # Wait for server to start

    print(f"Running benchmark for {name} on path {path}...")
    try:
        result = subprocess.run(
            ["wrk", "-t4", "-c100", "-d10s", f"http://127.0.0.1:{port}{path}"],
            shell=False,
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
        for pkill_arg in ['python.*app_', 'uvicorn', 'gunicorn', 'app_go_native', 'app_go_gin']:
            subprocess.run(['pkill', '-f', pkill_arg], shell=False)
        kill_process_on_port(port)
        time.sleep(2)

if __name__ == '__main__':
    print("Building Go applications...")
    subprocess.run(["go", "build", "-o", "app_go_native", "app_go_native.go"], shell=False)
    subprocess.run(["go", "build", "-o", "app_go_gin", "app_go_gin.go"], shell=False)

    json_benchmarks = []
    text_benchmarks = []
    html_benchmarks = []

    json_benchmarks.append(run_benchmark("FastAPI", "uvicorn app_fastapi:app --port 8001 --workers 1", 8001, "/"))
    json_benchmarks.append(run_benchmark("Flask", "gunicorn app_flask:app -b 127.0.0.1:8003 -w 1", 8003, "/"))
    json_benchmarks.append(run_benchmark("Go Gin", "./app_go_gin", 8005, "/"))
    json_benchmarks.append(run_benchmark("Go Native", "./app_go_native", 8004, "/"))
    json_benchmarks.append(run_benchmark("Robyn", "python app_robyn.py", 8002, "/"))
    json_benchmarks.append(run_benchmark("Socketify", "python app_socketify.py", 3000, "/"))
    json_benchmarks.append(run_benchmark("Xyra", "python app_xyra.py", 8000, "/"))

    text_benchmarks.append(run_benchmark("FastAPI", "uvicorn app_fastapi:app --port 8001 --workers 1", 8001, "/text"))
    text_benchmarks.append(run_benchmark("Flask", "gunicorn app_flask:app -b 127.0.0.1:8003 -w 1", 8003, "/text"))
    text_benchmarks.append(run_benchmark("Go Gin", "./app_go_gin", 8005, "/text"))
    text_benchmarks.append(run_benchmark("Go Native", "./app_go_native", 8004, "/text"))
    text_benchmarks.append(run_benchmark("Robyn", "python app_robyn.py", 8002, "/text"))
    text_benchmarks.append(run_benchmark("Socketify", "python app_socketify.py", 3000, "/text"))
    text_benchmarks.append(run_benchmark("Xyra", "python app_xyra.py", 8000, "/text"))

    html_benchmarks.append(run_benchmark("FastAPI", "uvicorn app_fastapi:app --port 8001 --workers 1", 8001, "/html"))
    html_benchmarks.append(run_benchmark("Flask", "gunicorn app_flask:app -b 127.0.0.1:8003 -w 1", 8003, "/html"))
    html_benchmarks.append(run_benchmark("Go Gin", "./app_go_gin", 8005, "/html"))
    html_benchmarks.append(run_benchmark("Go Native", "./app_go_native", 8004, "/html"))
    html_benchmarks.append(run_benchmark("Robyn", "python app_robyn.py", 8002, "/html"))
    html_benchmarks.append(run_benchmark("Socketify", "python app_socketify.py", 3000, "/html"))
    html_benchmarks.append(run_benchmark("Xyra", "python app_xyra.py", 8000, "/html"))

    # Write to markdown
    with open("benchmark_report.md", "w") as f:
        f.write("# Framework Benchmark Report\n\n")
        f.write("A performance comparison between FastAPI, Flask, Go Gin, Go Native, Robyn, Socketify, and Xyra.\n\n")
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
