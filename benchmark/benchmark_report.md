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
| FastAPI | 2,045.97 | 67.09ms |
| Robyn | 11,672.08 | 8.53ms |
| Socketify | 17,219.43 | 5.78ms |
| Xyra | 5,117.77 | 19.51ms |

## Results (Plain Text)

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 2,147.04 | 59.05ms |
| Robyn | 10,022.85 | 9.96ms |
| Socketify | 19,846.66 | 5.02ms |
| Xyra | 5,268.99 | 18.91ms |
