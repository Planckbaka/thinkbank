# Getting Started

This guide will help you set up ThinkBank for local development.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.x+ | Container runtime |
| Docker Compose | 2.x+ | Multi-container orchestration |
| Go | 1.25+ | Backend development |
| Python | 3.11+ | AI service development |
| Node.js | 20.x+ | Frontend development |
| npm/pnpm | 10.x+/9.x+ | Package management |
| Git | 2.x+ | Version control |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16+ cores |
| RAM | 16GB | 32GB+ |
| GPU | RTX 3060 (12GB) | RTX 4070 (8GB+) |
| Storage | 50GB SSD | 100GB+ NVMe |

### Verify Prerequisites

```bash
# Check versions
docker --version          # Docker version 24.x+
docker compose version    # Docker Compose version 2.x+
go version                # go1.25+
python --version          # Python 3.11+
node --version            # v20.x+
npm --version             # 10.x+

# Check GPU
nvidia-smi                # Should show GPU info
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/thinkbank.git
cd thinkbank
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional for development)
nano .env
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL, MinIO, Redis
docker compose up -d postgres minio redis

# Wait for services to be healthy
docker compose ps
```

### 4. Start vLLM (GPU Required)

```bash
# In a separate terminal
source .env

python -m vllm.entrypoints.openai.api_server \
  --model $LLM_MODEL \
  --host 0.0.0.0 \
  --port $LLM_PORT \
  --gpu-memory-utilization $VLLM_GPU_MEMORY_UTILIZATION
```

First run will download the model (~5GB).

### 5. Start Python AI Service

```bash
cd python-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start gRPC server
python server.py
```

### 6. Start Go Backend

```bash
cd go-backend

# Download dependencies
go mod download

# Run server
go run main.go
```

### 7. Start Frontend

```bash
cd web-ui

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 8. Access Application

Open http://localhost:5173 in your browser.

---

## Development Setup Details

### Database Setup

The database is automatically initialized when PostgreSQL starts.

**Schema location**: `init-db/01-init.sql`

**Manual connection**:
```bash
docker compose exec postgres psql -U thinkbank -d thinkbank
```

### MinIO Setup

Access MinIO console at http://localhost:9001

**Default credentials**:
- Username: `minioadmin`
- Password: `minioadmin123`

**Create bucket** (if not auto-created):
```bash
# Using MinIO client
mc alias set local http://localhost:9000 minioadmin minioadmin123
mc mb local/thinkbank
```

### IDE Setup

#### VSCode

Recommended extensions:

```json
{
  "recommendations": [
    "golang.go",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "bierner.markdown-mermaid"
  ]
}
```

#### Go Configuration

```json
// .vscode/settings.json
{
  "go.useLanguageServer": true,
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "package"
}
```

#### Python Configuration

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/python-ai/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

---

## Project Structure

```
thinkbank/
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment template
├── init-db/
│   └── 01-init.sql         # Database schema
├── go-backend/             # Go HTTP backend
│   ├── main.go
│   ├── router.go
│   ├── biz/
│   │   ├── handler/        # HTTP handlers
│   │   ├── model/          # Data models
│   │   └── dal/            # Data access
│   └── idl/
│       └── ai_service.proto
├── python-ai/              # Python AI service
│   ├── server.py
│   ├── worker.py
│   ├── core/               # Core modules
│   └── workers/            # Queue consumers
├── web-ui/                 # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
└── docs/                   # Documentation
```

---

## Common Tasks

### Run All Tests

```bash
# Go tests
cd go-backend && go test ./...

# Python tests
cd python-ai && pytest

# Frontend tests
cd web-ui && npm test
```

### Generate gRPC Code

```bash
# Go
cd go-backend
protoc --go_out=. --go-grpc_out=. idl/ai_service.proto

# Python
cd python-ai
python -m grpc_tools.protoc -I../go-backend/idl --python_out=. --grpc_python_out=. ai_service.proto
```

### Database Migrations

```bash
# Connect to database
docker compose exec postgres psql -U thinkbank -d thinkbank

# Run migration manually
\i /path/to/migration.sql
```

### Clear All Data

```bash
# Stop and remove volumes
docker compose down -v

# Start fresh
docker compose up -d postgres minio redis
```

---

## Troubleshooting Setup

### Port Conflicts

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Docker Issues

```bash
# Reset Docker
docker compose down -v
docker system prune -f

# Rebuild
docker compose build --no-cache
```

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## Next Steps

1. Read [Architecture Overview](../architecture/system-overview.md)
2. Review [API Documentation](../api/openapi.yaml)
3. Check [Contributing Guidelines](./contributing.md)
