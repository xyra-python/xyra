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
| FastAPI | 2,128.26 | 61.75ms |
| Flask | 1,867.83 | 53.18ms |
| Go Gin | 75,263.97 | 1.69ms |
| Go Native | 59,385.06 | 2.13ms |
| Robyn | 11,823.58 | 8.43ms |
| Socketify | 18,193.66 | 5.48ms |
| Xyra | 29,750.15 | 3.86ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,244.37 | 73.94ms |
| Flask | 1,970.56 | 50.38ms |
| Go Gin | 83,312.40 | 1.50ms |
| Go Native | 76,070.76 | 1.67ms |
| Robyn | 11,881.48 | 8.39ms |
| Socketify | 20,513.22 | 4.85ms |
| Xyra | 39,052.35 | 2.55ms |

## Results (HTML)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,234.49 | 73.70ms |
| Flask | 1,990.40 | 49.84ms |
| Go Gin | 80,137.23 | 1.55ms |
| Go Native | 83,011.69 | 1.52ms |
| Robyn | 12,743.48 | 7.83ms |
| Socketify | 25,205.91 | 3.95ms |
| Xyra | 22,990.01 | 4.33ms |
