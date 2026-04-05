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
| FastAPI | 1,963.01 | 64.80ms |
| Robyn | 11,546.91 | 8.63ms |
| Socketify | 16,523.74 | 6.04ms |
| Xyra | 2,377.38 | 449.78us |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,181.59 | 61.02ms |
| Robyn | 11,264.70 | 8.84ms |
| Socketify | 20,795.48 | 4.79ms |
| Xyra | 7.08 | 12.33ms |
