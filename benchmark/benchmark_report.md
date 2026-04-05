# Framework Benchmark Report

A performance comparison between FastAPI, Robyn, Socketify, and Xyra.

## Setup
- **Tool**: wrk
- **Threads**: 4
- **Connections**: 100
- **Duration**: 10s

## Results

| Framework | Requests/sec | Avg Latency |
|-----------|--------------|-------------|
| FastAPI | 1,905.40 | 79.61ms |
| Robyn | 12,038.47 | 8.28ms |
| Socketify | 16,466.22 | 6.06ms |
| Xyra | 4,993.12 | 19.96ms |
