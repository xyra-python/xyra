# Framework Benchmark Report

A performance comparison between FastAPI, Flask, Go Gin, Go Native, Robyn, Socketify, and Xyra.

## Setup
- **Tool**: wrk
- **Threads**: 4
- **Connections**: 100
- **Duration**: 10s

## Results (JSON)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,047.53 | 66.82ms |
| Flask | 1,833.10 | 54.09ms |
| Go Gin | 68,959.80 | 1.85ms |
| Go Native | 71,985.62 | 1.80ms |
| Robyn | 10,636.50 | 9.36ms |
| Socketify | 16,635.86 | 5.99ms |
| Xyra | 34,330.92 | 2.90ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 1,810.58 | 78.29ms |
| Flask | 1,967.97 | 50.41ms |
| Go Gin | 76,091.05 | 1.60ms |
| Go Native | 75,554.80 | 1.67ms |
| Robyn | 10,493.90 | 9.51ms |
| Socketify | 20,717.55 | 4.83ms |
| Xyra | 28,994.62 | 3.43ms |

## Results (HTML)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 1,736.36 | 85.44ms |
| Flask | 1,975.55 | 50.29ms |
| Go Gin | 75,051.54 | 1.63ms |
| Go Native | 76,886.24 | 1.63ms |
| Robyn | 11,180.00 | 8.91ms |
| Socketify | 19,893.58 | 5.02ms |
| Xyra | 19,908.08 | 5.01ms |
