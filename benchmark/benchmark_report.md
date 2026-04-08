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
| FastAPI | 1,987.32 | 76.30ms |
| Robyn | 10,838.03 | 9.18ms |
| Socketify | 14,015.36 | 7.11ms |
| Xyra | 20,953.00 | 4.75ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,100.50 | 61.79ms |
| Robyn | 11,352.08 | 8.79ms |
| Socketify | 19,870.91 | 5.03ms |
| Xyra | 25,174.21 | 3.96ms |
