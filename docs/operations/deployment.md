# Deployment Guide

This document covers deployment options and procedures for ThinkBank.

## Deployment Modes

### Mode A: Hybrid Deployment (Recommended for Development)

Infrastructure services in Docker, application services on host.

```
┌─────────────────────────────────────────────┐
│                 Docker                       │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐  │
│  │ PostgreSQL│ │  MinIO   │ │   Redis   │  │
│  │   :5432   │ │  :9000   │ │   :6379   │  │
│  └───────────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───┴───┐      ┌────┴────┐     ┌────┴────┐
│   Go  │      │ Python  │     │  vLLM   │
│ :8080 │      │ :50051  │     │ :8000   │
└───────┘      └─────────┘     └─────────┘
```

**When to use:**
- Development environment
- Machines with GPU (vLLM needs direct GPU access)
- Frequent code changes (no rebuild needed)

### Mode B: Full Docker Deployment

All services in Docker Compose.

```
┌───────────────────────────────────────────────────────┐
│                    Docker Compose                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ │
│  │PostgreSQL│ │  MinIO  │ │  Redis  │ │ Go Backend  │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │
│  │ Python AI   │ │    vLLM     │ │     Web UI      │ │
│  └─────────────┘ └─────────────┘ └─────────────────┘ │
└───────────────────────────────────────────────────────┘
```

**When to use:**
- Production deployment
- Machines without direct GPU access (using nvidia-docker)
- Consistent environments across team

---

## Mode A: Hybrid Deployment

### Prerequisites

- Docker & Docker Compose
- Go 1.25+
- Python 3.11+
- Node.js 20+
- NVIDIA GPU with CUDA (for vLLM)

### Step 1: Start Infrastructure

```bash
# Start PostgreSQL, MinIO, Redis
docker compose up -d postgres minio redis

# Verify services are running
docker compose ps
```

### Step 2: Start vLLM Server

```bash
# Set environment
source .env

# Start vLLM (requires GPU)
python -m vllm.entrypoints.openai.api_server \
  --model $LLM_MODEL \
  --host 0.0.0.0 \
  --port $LLM_PORT \
  --gpu-memory-utilization $VLLM_GPU_MEMORY_UTILIZATION \
  --max-model-len $VLLM_MAX_MODEL_LEN \
  --dtype $VLLM_DTYPE
```

### Step 3: Start Python AI Service

```bash
cd python-ai

# Install dependencies
pip install -r requirements.txt

# Start gRPC server
python server.py
```

### Step 4: Start Go Backend

```bash
cd go-backend

# Download dependencies
go mod download

# Run server
go run main.go
```

### Step 5: Start Web UI

```bash
cd web-ui

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Mode B: Full Docker Deployment

### Prerequisites

- Docker 24.x+
- Docker Compose 2.x+
- NVIDIA Container Toolkit (for GPU)
- NVIDIA GPU with CUDA

### Step 1: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

### Step 2: Build and Start

```bash
# Build all images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps
```

### Step 3: Verify Deployment

```bash
# Check Go backend
curl http://localhost:8080/ping

# Check AI service
curl http://localhost:8080/api/v1/ai/health

# Check MinIO console
open http://localhost:9001
```

---

## GPU Configuration

### NVIDIA Container Toolkit

Required for GPU access in Docker:

```bash
# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Verify GPU Access

```bash
# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### vLLM GPU Settings

In `.env`:

```bash
# Adjust based on your GPU
VLLM_GPU_MEMORY_UTILIZATION=0.95  # Use 95% of VRAM
VLLM_MAX_MODEL_LEN=8192           # Context length
VLLM_DTYPE=float16                # Data type
```

---

## Production Considerations

### Security

1. **Change default passwords** in `.env`
2. **Enable TLS** for all services
3. **Configure firewall** to restrict port access
4. **Use secrets management** (not `.env` files)

### Backups

```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U thinkbank thinkbank > backup_$(date +%Y%m%d).sql

# MinIO backup
mc mirror local/thinkbank /backup/minio/
```

### High Availability

For production HA:

1. Use managed PostgreSQL (RDS, Cloud SQL)
2. Use managed object storage (S3, GCS)
3. Deploy multiple Go backend instances behind load balancer
4. Use managed Redis (ElastiCache, Memorystore)

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  go-backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Rollback Procedure

### Application Rollback

```bash
# Pull previous image
docker compose pull go-backend:previous-version

# Update docker-compose.yml to use previous version
# Restart service
docker compose up -d go-backend
```

### Database Rollback

```bash
# Stop application
docker compose stop go-backend python-ai

# Restore database
docker compose exec -T postgres psql -U thinkbank < backup_YYYYMMDD.sql

# Restart application
docker compose start go-backend python-ai
```

---

## Health Checks

All services include health checks:

| Service | Health Endpoint | Expected Response |
|---------|-----------------|-------------------|
| Go Backend | `GET /ping` | `{"message": "pong"}` |
| AI Service | `GET /api/v1/ai/health` | `{"status": "healthy"}` |
| vLLM | `GET /v1/models` | Model list |
| PostgreSQL | `pg_isready` | Accepting connections |
| MinIO | `GET /minio/health/live` | 200 OK |
| Redis | `PING` | `PONG` |
