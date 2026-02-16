# ThinkBank

[简体中文](./README.zh-CN.md) | [Documentation](./docs/README.md)

> Intelligent personal data asset management system - self-hosted, privacy-first smart gallery and second brain.

ThinkBank is a local-first personal data management system. It uses local AI models to organize, analyze, and retrieve personal digital assets (images and documents).

**[View Full Documentation](./docs/README.md)** - API specs, architecture diagrams, deployment guides, and more.

## Core Features

- Data sovereignty: all data stays local.
- Smart ingestion: auto tagging, OCR, and vectorization after upload.
- Real-time status: tracked processing queue with visual feedback.
- Natural interaction: chat with your data using RAG.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Go / Hertz |
| AI Service | Python / LangChain / vLLM |
| Database | PostgreSQL 16 + pgvector |
| Object Storage | MinIO (S3 compatible) |
| Cache/Queue | Redis 7 |
| Frontend | React + Vite + Tailwind + shadcn/ui |

## Project Structure

```text
thinkbank/
├── docker-compose.yml
├── init-db/
├── go-backend/
├── python-ai/
├── web-ui/
├── start-infra.sh
├── run-backend-host.sh
├── run-ai-host.sh
├── run-ai-worker-host.sh
├── run-ai-embed-host.sh
├── run-vllm-host.sh
├── run-web-host.sh
├── start-host-app.sh
└── stop-host-app.sh
```

## Prerequisites

- Docker Engine + Docker Compose Plugin
- Go 1.25+
- Node.js 20+
- Python 3.11+
- `python3`, `pip`, and `virtualenv` available on host
- Optional: NVIDIA GPU + NVIDIA Container Toolkit (for AI container mode)

## Deployment Modes

ThinkBank supports two deployment modes.

### Mode A: Hybrid (Infra in Docker, App Services on Host)

This mode matches your target workflow:
- In Docker: PostgreSQL + Redis + MinIO
- On host: Go backend + Python AI service + Python AI worker + vLLM + web-ui

1. Prepare env file:

```bash
cp .env.example .env
```

2. Start infrastructure in Docker:

```bash
./start-infra.sh
```

3. Prepare Python virtual environments on host (first time only):

```bash
python3 -m pip install --user --break-system-packages virtualenv
~/.local/bin/virtualenv .venv-ai
source .venv-ai/bin/activate && pip install -r python-ai/requirements.txt && deactivate
~/.local/bin/virtualenv .venv-vllm
source .venv-vllm/bin/activate && pip install vllm && deactivate
```

4. Start Python AI Embed service on host (new terminal):

```bash
./run-ai-embed-host.sh
```

5. Start Python AI gRPC service on host (new terminal):

```bash
./run-ai-host.sh
```

6. Start Python AI worker on host (new terminal):

```bash
./run-ai-worker-host.sh
```

7. Start Go backend on host (new terminal):

```bash
./run-backend-host.sh
```

8. Start web-ui on host (new terminal):

```bash
cd web-ui
npm ci
cd ..
./run-web-host.sh
```

9. Or start all host app services in background (including vLLM):

```bash
./start-host-app.sh
```

9. Verify:

```bash
curl -i http://localhost:8080/ping
curl -i http://localhost:8000/v1/models -H "Authorization: Bearer sk-local"
ss -ltnp | grep -E ':50051|:8080|:5173|:8000'
```

Notes:
- Host-mode scripts use project-local HF cache at `.hf-cache/` to avoid Docker-created root-owned cache conflicts.
- Stop host-mode app services with `./stop-host-app.sh`.

### Mode B: Full Docker (All Services in Compose)

```bash
cp .env.example .env
docker compose --profile app up -d
docker compose --profile app ps
```

Notes:
- `llm-engine` needs NVIDIA runtime (`nvidia` container runtime / NVIDIA Container Toolkit).
- `ai-service` first build is heavy and takes a long time.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/ping` | Health check |
| `POST` | `/api/v1/assets/upload` | Upload asset |
| `GET` | `/api/v1/assets` | List assets |
| `GET` | `/api/v1/assets/:id` | Get asset by ID |
| `DELETE` | `/api/v1/assets/:id` | Delete asset |
| `GET` | `/api/v1/ai/health` | Check AI + LLM availability |
| `GET` | `/api/v1/search?q=&limit=&threshold=` | Hybrid (vector + character) retrieval |
| `POST` | `/api/v1/chat` | RAG chat, returns `answer` + `sources` |

## Key Environment Variables

`.env` mainly for `docker-compose`:

```env
POSTGRES_USER=thinkbank
POSTGRES_PASSWORD=thinkbank123
POSTGRES_DB=thinkbank
POSTGRES_PORT=5432

REDIS_PORT=6379

MINIO_USER=minioadmin
MINIO_PASSWORD=minioadmin123
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

BACKEND_PORT=8080
WEB_PORT=5173
AI_GRPC_PORT=50051
LLM_PORT=8000

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DB_AUTO_MIGRATE=true

LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4
LLM_API_KEY=sk-local
VLLM_GPU_MEMORY_UTILIZATION=0.7
VLLM_MAX_MODEL_LEN=4096
VLLM_MAX_NUM_SEQS=32
VLLM_MAX_NUM_BATCHED_TOKENS=1024
VLLM_DTYPE=float16
```

Host-run backend defaults (`run-backend-host.sh` auto maps infra ports from `.env`):

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=thinkbank
DB_PASSWORD=thinkbank123
DB_NAME=thinkbank

REDIS_HOST=localhost
REDIS_PORT=6379

MINIO_ENDPOINT=localhost:9000
MINIO_USER=minioadmin
MINIO_PASSWORD=minioadmin123

AI_SERVICE_HOST=127.0.0.1
AI_SERVICE_PORT=50051
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DB_AUTO_MIGRATE=true
```

## Troubleshooting

### 1. `docker compose up` fails with port conflict

Example: `bind: address already in use`

Check occupied ports:

```bash
ss -ltn '( sport = :5432 or sport = :6379 or sport = :9000 or sport = :9001 or sport = :8080 or sport = :5173 )'
```

Fix options:

- Stop conflicting services/processes.
- Change host port mappings in `.env` (for example `POSTGRES_PORT=15432`).

### 2. Go version mismatch error

Error example: `compile: version "go1.xx" does not match go tool version`

Quick workaround:

```bash
env -u GOROOT go test ./...
env -u GOROOT go run .
```

Long-term fix:

- Remove stale `GOROOT` export from shell config (`~/.bashrc` or `~/.zshrc`).
- Reload shell config.
- Verify with:

```bash
go env GOROOT && go version
```

### 3. Frontend shows `Failed to fetch`

Verify backend first:

```bash
curl -i http://localhost:8080/ping
```

Then verify frontend API base URL in `web-ui/src/lib/api.ts` (default: `http://localhost:8080`).

### 4. `docker compose ps` shows `Created` instead of `Up`

Usually caused by port conflicts or failed dependencies.

Check logs:

```bash
docker compose logs postgres --tail=50
docker compose logs redis --tail=50
docker compose logs minio --tail=50
```

### 5. `llm-engine` fails with NVIDIA runtime error

Error example: `could not select device driver "nvidia" with capabilities: [[gpu]]`

Check runtime:

```bash
docker info | rg -i nvidia
```

If no `nvidia` runtime is available:
- Install NVIDIA Container Toolkit and restart Docker, or
- Use Mode A (Hybrid) and run vLLM directly on host via `./run-vllm-host.sh`.

### 6. vLLM Out Of Memory (OOM) on 8GB GPUs

If vLLM crashes during initialization or generation with 8GB VRAM:
- Lower gpu_memory_utilization in `.env` (default is 0.7 or 0.8 for 8GB cards):
  ```env
  VLLM_GPU_MEMORY_UTILIZATION=0.6
  ```
- Reduce context length:
  ```env
  VLLM_MAX_MODEL_LEN=2048
  ```

### 7. Services fail to restart / Port already in use

If `./run-backend-host.sh` fails with "address already in use" even after stopping services:
- You may have zombie processes.
- Run the aggressive cleanup script:
  ```bash
  ./stop-host-app.sh
  ```
- Or manually kill them:
  ```bash
  pkill -f "thinkbank/backend"
  pkill -f "workers.asset_processor"
  ```

## Stop Services

```bash
# Stop compose services
docker compose down

# Stop and remove volumes (this deletes DB/object data)
docker compose down -v
```

If you started local dev with `go run` or `npm run dev`, stop them with `Ctrl+C` in their terminals.

If you started host-mode services in background with `./start-host-app.sh`:

```bash
./stop-host-app.sh
```

## License

MIT License
