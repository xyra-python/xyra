# Framework Benchmark Report

A performance comparison between FastAPI, Robyn, Socketify, and Xyra.

## Setup
- **Tool**: wrk
- **Threads**: 4
- **Connections**: 100
- **Duration**: 10s

## Results (JSON)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,032.15 | 56.03ms |
| Robyn | 10,457.35 | 9.55ms |
| Socketify | 18,206.07 | 5.46ms |
| Xyra | 8,903.92 | 11.14ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,076.97 | 76.19ms |
| Robyn | 10,998.73 | 9.05ms |
| Socketify | 25,681.85 | 3.88ms |
| Xyra | 7,773.28 | 13.27ms |
