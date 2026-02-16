# Troubleshooting Guide

This document covers common issues and their solutions.

## Quick Diagnostics

### Check Service Status

```bash
# Docker services
docker compose ps

# Port availability
netstat -tlnp | grep -E '5432|6379|8080|9000'

# GPU status
nvidia-smi
```

### Health Check Script

```bash
#!/bin/bash
echo "=== ThinkBank Health Check ==="

# PostgreSQL
docker compose exec postgres pg_isready && echo "✓ PostgreSQL OK" || echo "✗ PostgreSQL FAIL"

# Redis
docker compose exec redis redis-cli ping && echo "✓ Redis OK" || echo "✗ Redis FAIL"

# MinIO
curl -s http://localhost:9000/minio/health/live && echo "✓ MinIO OK" || echo "✗ MinIO FAIL"

# Go Backend
curl -s http://localhost:8080/ping && echo "✓ Backend OK" || echo "✗ Backend FAIL"

# AI Service
curl -s http://localhost:8080/api/v1/ai/health && echo "✓ AI Service OK" || echo "✗ AI Service FAIL"

# vLLM
curl -s http://localhost:8000/v1/models && echo "✓ vLLM OK" || echo "✗ vLLM FAIL"
```

---

## Common Issues

### 1. Database Connection Errors

#### Symptom
```
connection refused: localhost:5432
```

#### Causes & Solutions

| Cause | Solution |
|-------|----------|
| PostgreSQL not running | `docker compose up -d postgres` |
| Wrong host | Set `POSTGRES_HOST=postgres` in `.env` |
| Port conflict | Check if port 5432 is in use |
| Firewall blocking | Open port 5432 |

#### Debug Commands

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U thinkbank -d thinkbank -c "SELECT 1"
```

---

### 2. Redis Connection Errors

#### Symptom
```
redis: connection refused
```

#### Solutions

```bash
# Start Redis
docker compose up -d redis

# Test connection
docker compose exec redis redis-cli ping
```

---

### 3. MinIO Errors

#### Symptom
```
MinIO: The access key ID you provided does not exist
```

#### Solutions

```bash
# Verify credentials in .env
echo $MINIO_USER
echo $MINIO_PASSWORD

# Check MinIO logs
docker compose logs minio

# Recreate bucket if needed
docker compose exec minio mc alias set local http://localhost:9000 $MINIO_USER $MINIO_PASSWORD
docker compose exec minio mc mb local/thinkbank
```

---

### 4. GPU / vLLM Issues

#### Symptom: Out of Memory
```
CUDA out of memory. Tried to allocate 2.00 GiB
```

#### Solutions

1. **Reduce GPU memory utilization**
   ```bash
   # In .env
   VLLM_GPU_MEMORY_UTILIZATION=0.8
   ```

2. **Reduce context length**
   ```bash
   VLLM_MAX_MODEL_LEN=4096
   ```

3. **Use smaller model**
   ```bash
   LLM_MODEL=Qwen/Qwen2.5-3B-Instruct
   ```

#### Symptom: Model Not Found
```
Model not found: Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4
```

#### Solutions

```bash
# Pre-download model
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4

# Or use cache directory
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache
```

---

### 5. gRPC Connection Errors

#### Symptom
```
grpc connection refused: localhost:50051
```

#### Solutions

```bash
# Check Python AI service is running
ps aux | grep "python server.py"

# Check gRPC port
netstat -tlnp | grep 50051

# Start Python service
cd python-ai && python server.py
```

#### Symptom: gRPC Timeout
```
grpc timeout after 30s
```

#### Solutions

1. Check AI service logs for processing errors
2. Verify model loading completed
3. Increase timeout if processing large files

---

### 6. Processing Failures

#### Symptom: Assets stuck in PENDING

#### Debug Steps

```bash
# Check Redis queue
docker compose exec redis redis-cli LLEN processing_queue

# Check processing tasks
docker compose exec postgres psql -U thinkbank -d thinkbank \
  -c "SELECT * FROM processing_tasks ORDER BY created_at DESC LIMIT 10"

# Check worker logs
cd python-ai && python worker.py  # Watch for errors
```

#### Common Causes

| Cause | Solution |
|-------|----------|
| Worker not running | Start `python worker.py` |
| Model not loaded | Check vLLM is running |
| File corrupted | Re-upload file |
| Unsupported format | Check MIME type |

---

### 7. Upload Errors

#### Symptom: File Too Large
```json
{"code": "FILE_TOO_LARGE", "message": "File exceeds 100MB"}
```

#### Solution
- Compress file or split into smaller parts
- Max size is configurable in Go backend

#### Symptom: Invalid File Type
```json
{"code": "INVALID_FILE_TYPE", "message": "Type video/mp4 not supported"}
```

#### Solution
- Only these types are supported:
  - Images: JPEG, PNG, GIF, WebP
  - Documents: PDF, TXT, JSON, MD

---

### 8. CORS Errors

#### Symptom (Browser Console)
```
Access to XMLHttpRequest at 'http://localhost:8080' from origin 'http://localhost:5173' has been blocked by CORS policy
```

#### Solution

```bash
# In .env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Restart Go backend
```

---

### 9. Vector Search Returns No Results

#### Debug Steps

```bash
# Check embeddings exist
docker compose exec postgres psql -U thinkbank -d thinkbank \
  -c "SELECT COUNT(*) FROM asset_embeddings"

# Check vector dimensions
docker compose exec postgres psql -U thinkbank -d thinkbank \
  -c "SELECT array_length(semantic_vector, 1) FROM asset_embeddings LIMIT 1"
```

#### Solutions

1. Verify processing completed (`processing_status = 'COMPLETED'`)
2. Lower similarity threshold
3. Check embedding model loaded correctly

---

## Log Locations

| Service | Log Location |
|---------|-------------|
| Go Backend | stdout / docker logs |
| Python AI | stdout (Loguru formatted) |
| vLLM | stdout |
| PostgreSQL | `docker compose logs postgres` |
| Redis | `docker compose logs redis` |
| MinIO | `docker compose logs minio` |

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f go-backend

# Last 100 lines
docker compose logs --tail=100 python-ai
```

---

## Performance Troubleshooting

### Slow Uploads

1. Check MinIO health
2. Verify disk I/O: `iostat -x 1`
3. Check network: `iperf3`

### Slow Vector Search

1. Verify IVFFlat index exists
2. Check `lists` parameter matches dataset size
3. Monitor PostgreSQL memory

### Slow LLM Responses

1. Check GPU utilization: `nvidia-smi -l 1`
2. Reduce batch size
3. Use smaller model

---

## Recovery Procedures

### Reset Database

```bash
# WARNING: Destroys all data
docker compose down -v
docker compose up -d postgres
```

### Rebuild Embeddings

```sql
-- Clear existing embeddings
DELETE FROM asset_embeddings;

-- Reset asset status
UPDATE assets SET processing_status = 'PENDING';

-- Re-queue for processing
-- (Worker will reprocess automatically)
```

### Clear Redis Queue

```bash
docker compose exec redis redis-cli DEL processing_queue
```

---

## Getting Help

1. Check logs for error messages
2. Search this document for symptoms
3. Check GitHub Issues
4. Provide diagnostic info when asking for help:
   - Docker version
   - GPU model and driver version
   - Error messages (full stack trace)
   - Steps to reproduce
