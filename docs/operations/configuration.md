# Configuration Reference

This document provides a complete reference for all ThinkBank configuration options.

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (main config) |
| `docker-compose.yml` | Docker service configuration |
| `python-ai/core/config.py` | Python service settings |
| `web-ui/.env` | Frontend environment (optional) |

---

## Environment Variables

### PostgreSQL Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `thinkbank` | Database username |
| `POSTGRES_PASSWORD` | `thinkbank123` | Database password |
| `POSTGRES_DB` | `thinkbank` | Database name |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_HOST` | `postgres` | Database host (Docker) or `localhost` |

**Security Note**: Change `POSTGRES_PASSWORD` in production!

### MinIO Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_USER` | `minioadmin` | MinIO admin username |
| `MINIO_PASSWORD` | `minioadmin123` | MinIO admin password |
| `MINIO_API_PORT` | `9000` | S3 API port |
| `MINIO_CONSOLE_PORT` | `9001` | Web console port |
| `MINIO_BUCKET` | `thinkbank` | Default bucket name |

**Security Note**: Change `MINIO_PASSWORD` in production!

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PASSWORD` | (empty) | Redis password (optional) |

### Application Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | `8080` | Go HTTP server port |
| `AI_GRPC_PORT` | `50051` | Python gRPC port |
| `WEB_PORT` | `5173` | Frontend dev server port |
| `LLM_PORT` | `8000` | vLLM API port |

### Backend Runtime

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `DB_AUTO_MIGRATE` | `true` | Auto-run database migrations |
| `GIN_MODE` | `debug` | Gin mode: `debug` or `release` |

### LLM / vLLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4` | HuggingFace model ID |
| `LLM_API_KEY` | `sk-local` | API key (any value for local) |
| `LLM_API_BASE` | `http://localhost:8000/v1` | API base URL |
| `VLLM_GPU_MEMORY_UTILIZATION` | `0.95` | GPU memory fraction to use |
| `VLLM_MAX_MODEL_LEN` | `8192` | Maximum context length |
| `VLLM_DTYPE` | `float16` | Model data type |

---

## Complete .env Example

```bash
# ThinkBank Environment Configuration
# Copy this file to .env and modify as needed

# ===========================================
# PostgreSQL Configuration
# ===========================================
POSTGRES_USER=thinkbank
POSTGRES_PASSWORD=thinkbank123  # CHANGE IN PRODUCTION
POSTGRES_DB=thinkbank
POSTGRES_PORT=5432
# POSTGRES_HOST=postgres  # For Docker
# POSTGRES_HOST=localhost # For local development

# ===========================================
# MinIO Configuration
# ===========================================
MINIO_USER=minioadmin
MINIO_PASSWORD=minioadmin123  # CHANGE IN PRODUCTION
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# ===========================================
# Redis Configuration
# ===========================================
REDIS_PORT=6379
# REDIS_HOST=redis     # For Docker
# REDIS_HOST=localhost # For local development
# REDIS_PASSWORD=      # Optional

# ===========================================
# Application Ports
# ===========================================
BACKEND_PORT=8080
AI_GRPC_PORT=50051
WEB_PORT=5173
LLM_PORT=8000

# ===========================================
# Backend Runtime
# ===========================================
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DB_AUTO_MIGRATE=true

# ===========================================
# vLLM Configuration
# ===========================================
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4
LLM_API_KEY=sk-local
VLLM_GPU_MEMORY_UTILIZATION=0.95
VLLM_MAX_MODEL_LEN=8192
VLLM_DTYPE=float16
```

---

## Python Service Configuration

The Python AI service uses Pydantic Settings for configuration. Settings can be overridden via environment variables.

### File: `python-ai/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "thinkbank"
    postgres_password: str = "thinkbank123"
    postgres_db: str = "thinkbank"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "thinkbank"
    minio_secure: bool = False

    # LLM
    llm_api_base: str = "http://localhost:8000/v1"
    llm_api_key: str = "sk-local"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"

    # gRPC
    grpc_port: int = 50051

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## Docker Compose Configuration

### Service Dependencies

```yaml
services:
  go-backend:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_started

  python-ai:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
```

### Volume Paths

| Service | Container Path | Purpose |
|---------|---------------|---------|
| PostgreSQL | `/var/lib/postgresql/data` | Database files |
| MinIO | `/data` | Object storage |
| Redis | `/data` | Persistence |

---

## Secrets Management

### Development (Not Recommended for Production)

Store secrets in `.env`:

```bash
# .env - DO NOT COMMIT
POSTGRES_PASSWORD=supersecret
MINIO_PASSWORD=supersecret
LLM_API_KEY=sk-xxxxx
```

### Production Recommendations

1. **Docker Secrets**

```yaml
services:
  postgres:
    secrets:
      - postgres_password

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

2. **Environment Variables** (via orchestration platform)

```bash
# Kubernetes
kubectl create secret generic thinkbank-secrets \
  --from-literal=POSTGRES_PASSWORD=xxx
```

3. **HashiCorp Vault** for enterprise deployments

---

## Configuration Validation

### Check Environment

```bash
# Verify .env is loaded
docker compose config

# Check Python config
cd python-ai && python -c "from core.config import settings; print(settings)"
```

### Common Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `connection refused` | Wrong host/port | Check `POSTGRES_HOST`, `REDIS_HOST` |
| `authentication failed` | Wrong credentials | Verify passwords in `.env` |
| `CORS error` | Missing origin | Add frontend URL to `CORS_ALLOWED_ORIGINS` |
| `GPU OOM` | Model too large | Reduce `VLLM_GPU_MEMORY_UTILIZATION` |

---

## Environment-Specific Configs

### Development

```bash
# .env.development
CORS_ALLOWED_ORIGINS=*
DB_AUTO_MIGRATE=true
```

### Production

```bash
# .env.production
CORS_ALLOWED_ORIGINS=https://thinkbank.example.com
DB_AUTO_MIGRATE=false
GIN_MODE=release
```

### Load Specific Config

```bash
# Development
cp .env.development .env

# Production
cp .env.production .env
```
