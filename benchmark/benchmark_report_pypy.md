# Framework Benchmark Report (PyPy3)

A performance comparison between Socketify and Xyra using PyPy3.

## Setup
- **Tool**: wrk
- **Threads**: 4
- **Connections**: 100
- **Duration**: 10s

## Results (JSON)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| Socketify | 31,523.98 | 8.89ms |
| Xyra | 25,469.74 | 4.26ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| Socketify | 48,101.47 | 24.30ms |
| Xyra | 58,802.48 | 1.70ms |

## Results (HTML)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| Socketify | 51,613.50 | 11.75ms |
| Xyra | 43,455.65 | 2.47ms |
