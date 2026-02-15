# ThinkBank

[简体中文](./README.zh-CN.md)

> Intelligent personal data asset management system - self-hosted, privacy-first smart gallery and second brain.

ThinkBank is a local-first personal data management system. It uses local AI models to organize, analyze, and retrieve personal digital assets (images and documents).

## Core Features

- Data sovereignty: all data stays local.
- Smart ingestion: auto tagging, OCR, and vectorization after upload.
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
└── web-ui/
```

## Prerequisites

- Docker Engine + Docker Compose Plugin
- Go 1.25+
- Node.js 20+
- Python 3.11+
- Optional: NVIDIA GPU + NVIDIA Container Toolkit (for AI container mode)

## Quick Start (Recommended: Local Dev Mode)

### 1. Clone and prepare env file

```bash
git clone <your-repo-url> thinkbank
cd thinkbank
cp .env.example .env
```

### 2. Start infrastructure (Postgres / Redis / MinIO)

```bash
docker compose up -d postgres redis minio
docker compose ps
```

If your Docker setup requires sudo, add `sudo` before those commands.

Health check:

```bash
curl -i http://localhost:9000/minio/health/live
```

Expected: `HTTP/1.1 200 OK`.

### 3. Start Go backend

```bash
cd go-backend
env -u GOROOT go mod tidy
env -u GOROOT go run .
```

Backend URL: `http://localhost:8080`

Health check:

```bash
curl -i http://localhost:8080/ping
```

Expected: `{"message":"pong"}`.

### 4. Start frontend

Open a new terminal:

```bash
cd web-ui
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend URL: `http://localhost:5173`

### 5. Optional: Start AI service (local Python mode)

Open a new terminal:

```bash
cd python-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

For worker mode, open another terminal:

```bash
cd python-ai
source .venv/bin/activate
python worker.py
```

## Container Start (Layered, Recommended)

Start only infrastructure first:

```bash
docker compose up -d postgres redis minio
```

Then start backend and frontend containers:

```bash
docker compose --profile app up -d go-backend web-ui
```

Start AI container only when needed:

```bash
docker compose --profile app up -d ai-service
```

Notes:

- `ai-service` is heavy and first build can take a long time.
- Without GPU or NVIDIA Container Toolkit, `ai-service` may fail to run.
- Validate backend/frontend first, then enable AI.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/ping` | Health check |
| `POST` | `/api/v1/assets/upload` | Upload asset |
| `GET` | `/api/v1/assets` | List assets |
| `GET` | `/api/v1/assets/:id` | Get asset by ID |
| `DELETE` | `/api/v1/assets/:id` | Delete asset |

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

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DB_AUTO_MIGRATE=true
```

Local backend runtime variables (with defaults if missing):

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
MINIO_BUCKET=thinkbank-assets

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

### 5. AI container is slow or model not loaded

- First build is very large, wait for completion.
- Check GPU:

```bash
nvidia-smi
```

- Check AI logs:

```bash
docker compose --profile app logs ai-service --tail=100
```

## Stop Services

```bash
# Stop compose services
docker compose down

# Stop and remove volumes (this deletes DB/object data)
docker compose down -v
```

If you started local dev with `go run` or `npm run dev`, stop them with `Ctrl+C` in their terminals.

## License

MIT License
