# Monitoring & Observability

This document covers health checks, logging, and monitoring strategies for ThinkBank.

## Health Check Endpoints

### Go Backend

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ping` | GET | Simple liveness check |
| `/api/v1/ai/health` | GET | AI service connectivity |

#### Responses

**`GET /ping`**
```json
{
  "message": "pong"
}
```

**`GET /api/v1/ai/health`**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "grpc_endpoint": "localhost:50051"
}
```

### vLLM Server

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/models` | GET | List available models |
| `/health` | GET | Server health |

### Infrastructure Services

| Service | Check Command |
|---------|--------------|
| PostgreSQL | `pg_isready -h localhost -p 5432` |
| Redis | `redis-cli ping` |
| MinIO | `curl http://localhost:9000/minio/health/live` |

---

## Logging

### Log Format

ThinkBank uses structured logging throughout:

#### Go Backend (Hertz)

```
{"level":"info","time":"2024-01-15T10:30:00Z","message":"Server started","port":8080}
```

#### Python AI (Loguru)

```
2024-01-15 10:30:00.123 | INFO     | server:main:15 - gRPC server started on :50051
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| DEBUG | Detailed debugging info |
| INFO | Normal operations |
| WARNING | Potential issues |
| ERROR | Errors that don't stop the service |
| CRITICAL | Service-stopping errors |

### Viewing Logs

```bash
# Docker logs (all services)
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps go-backend

# Filter by time
docker compose logs --since 1h python-ai

# Search logs
docker compose logs | grep -i error
```

### Log Aggregation (Future)

For production, consider:

- **Loki + Grafana**: Lightweight log aggregation
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **CloudWatch Logs**: AWS deployments

---

## Metrics

### Key Metrics to Monitor

#### Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `assets_uploaded_total` | Counter | Total assets uploaded |
| `assets_processed_total` | Counter | Successfully processed assets |
| `processing_errors_total` | Counter | Processing failures |
| `embedding_generation_seconds` | Histogram | Embedding generation time |

#### Infrastructure Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `db_connections_active` | Gauge | Active DB connections |
| `db_query_duration_seconds` | Histogram | Database query time |
| `redis_queue_length` | Gauge | Items in processing queue |
| `minio_storage_bytes` | Gauge | Total storage used |

#### GPU Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `gpu_memory_used_bytes` | Gauge | GPU memory in use |
| `gpu_memory_total_bytes` | Gauge | Total GPU memory |
| `gpu_utilization_percent` | Gauge | GPU compute utilization |
| `vllm_requests_total` | Counter | LLM inference requests |
| `vllm_tokens_generated_total` | Counter | Total tokens generated |

### Metrics Collection (Future)

Recommended setup:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'thinkbank-backend'
    static_configs:
      - targets: ['go-backend:8080']

  - job_name: 'thinkbank-ai'
    static_configs:
      - targets: ['python-ai:50051']
```

### Grafana Dashboard

Key panels to include:

1. **Request Rate**: Requests per second
2. **Latency P50/P95/P99**: Response time percentiles
3. **Error Rate**: 4xx and 5xx errors
4. **GPU Memory**: Used vs Total
5. **Queue Depth**: Redis queue length
6. **Processing Status**: Pending/Processing/Completed

---

## Alerting

### Alert Rules (Recommended)

| Alert | Condition | Severity |
|-------|-----------|----------|
| `ServiceDown` | No response for 1m | Critical |
| `HighErrorRate` | >5% 5xx errors for 5m | Warning |
| `HighLatency` | P99 > 2s for 5m | Warning |
| `GPUMemoryHigh` | >90% GPU memory | Warning |
| `QueueBacklog` | >100 items pending | Warning |
| `ProcessingFailures` | >10 failures in 1h | Warning |

### Alert Channels

- Email notifications
- Slack/Discord webhooks
- PagerDuty for critical alerts

---

## Health Check Configuration

### Docker Compose Health Checks

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U thinkbank"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /ping
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ping
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Observability Stack (Recommended)

### Development

```
┌─────────────────────────────────────────┐
│           ThinkBank Services             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Go Backend│ │Python AI│ │  vLLM   │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼───────────┼───────────┼─────────┘
        │           │           │
        └───────────┼───────────┘
                    │
              ┌─────┴─────┐
              │   Logs    │
              │ (stdout)  │
              └───────────┘
```

### Production

```
┌─────────────────────────────────────────┐
│           ThinkBank Services             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Go Backend│ │Python AI│ │  vLLM   │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼───────────┼───────────┼─────────┘
        │           │           │
        └─────┬─────┴─────┬─────┘
              │           │
        ┌─────┴─────┐ ┌───┴────┐
        │ Prometheus│ │  Loki  │
        └─────┬─────┘ └───┬────┘
              │           │
              └─────┬─────┘
                    │
              ┌─────┴─────┐
              │  Grafana  │
              └───────────┘
```

---

## Debugging Checklist

When investigating issues:

1. [ ] Check health endpoints
2. [ ] Review recent logs
3. [ ] Check GPU memory (`nvidia-smi`)
4. [ ] Verify database connectivity
5. [ ] Check Redis queue length
6. [ ] Review processing task status
7. [ ] Check disk space

### Quick Status Script

```bash
#!/bin/bash
echo "=== ThinkBank Status ==="
echo ""
echo "Services:"
docker compose ps
echo ""
echo "GPU:"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv
echo ""
echo "Redis Queue:"
docker compose exec redis redis-cli LLEN processing_queue
echo ""
echo "Processing Status:"
docker compose exec postgres psql -U thinkbank -d thinkbank -t -c \
  "SELECT processing_status, COUNT(*) FROM assets GROUP BY processing_status"
echo ""
echo "Recent Errors:"
docker compose logs --tail=20 | grep -i error
```
