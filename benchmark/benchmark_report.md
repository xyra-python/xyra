# Framework Benchmark Report

A performance comparison between FastAPI, Flask, Robyn, Socketify, and Xyra.

## Setup
- **Tool**: wrk
- **Threads**: 4
- **Connections**: 100
- **Duration**: 10s

## Results (JSON)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,105.49 | 66.49ms |
| Flask | 1,901.48 | 52.26ms |
| Robyn | 11,841.03 | 8.42ms |
| Socketify | 16,900.51 | 5.89ms |
| Xyra | 27,726.51 | 3.60ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,257.12 | 72.97ms |
| Flask | 2,030.31 | 48.97ms |
| Robyn | 11,067.55 | 9.00ms |
| Socketify | 21,920.40 | 4.55ms |
| Xyra | 33,231.35 | 2.99ms |

## Results (HTML)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,202.33 | 74.70ms |
| Flask | 2,003.17 | 49.60ms |
| Robyn | 12,415.40 | 8.01ms |
| Socketify | 20,150.98 | 4.95ms |
| Xyra | 14,466.98 | 6.92ms |
