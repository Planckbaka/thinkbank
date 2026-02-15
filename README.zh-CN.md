# ThinkBank

[English](./README.md)

> 智能个人数据资产管理系统 - 自托管、隐私优先的“智能图库”与“第二大脑”

ThinkBank 是一个本地优先的个人数据管理系统，利用本地 AI 模型对个人数字资产（图片、文档）进行组织、分析和检索。

## 核心特性

- 数据主权：所有数据保留在本地，完全掌控
- 智能摄入：上传后自动打标签、OCR 和向量化
- 自然交互：使用 RAG 与数据进行对话

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Go / Hertz |
| AI 服务 | Python / LangChain / vLLM |
| 数据库 | PostgreSQL 16 + pgvector |
| 对象存储 | MinIO (S3 兼容) |
| 缓存/队列 | Redis 7 |
| 前端 | React + Vite + Tailwind + shadcn/ui |

## 项目结构

```text
thinkbank/
├── docker-compose.yml
├── init-db/
├── go-backend/
├── python-ai/
└── web-ui/
```

## 环境要求

- Docker Engine + Docker Compose Plugin
- Go 1.25+
- Node.js 20+
- Python 3.11+
- 可选：NVIDIA GPU + NVIDIA Container Toolkit（AI 容器模式）

## 快速开始（推荐：本地开发模式）

### 1) 克隆并准备环境变量

```bash
git clone <your-repo-url> thinkbank
cd thinkbank
cp .env.example .env
```

### 2) 启动基础设施（Postgres / Redis / MinIO）

```bash
docker compose up -d postgres redis minio
docker compose ps
```

如果你的 Docker 需要 sudo，请在命令前加 `sudo`。

健康检查：

```bash
curl -i http://localhost:9000/minio/health/live
```

预期：返回 `HTTP/1.1 200 OK`。

### 3) 启动 Go 后端

```bash
cd go-backend
env -u GOROOT go mod tidy
env -u GOROOT go run .
```

后端默认地址：`http://localhost:8080`

健康检查：

```bash
curl -i http://localhost:8080/ping
```

预期：`{"message":"pong"}`。

### 4) 启动前端

新开一个终端：

```bash
cd web-ui
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

前端地址：`http://localhost:5173`

### 5) 可选：启动 AI 服务（本地 Python 模式）

新开一个终端：

```bash
cd python-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

如需后台 worker，再开一个终端：

```bash
cd python-ai
source .venv/bin/activate
python worker.py
```

## 容器化启动（推荐分层）

先只启动基础设施：

```bash
docker compose up -d postgres redis minio
```

再启动后端与前端容器：

```bash
docker compose --profile app up -d go-backend web-ui
```

按需启动 AI 容器：

```bash
docker compose --profile app up -d ai-service
```

说明：

- `ai-service` 依赖较重，首次构建会很久（下载 vLLM/torch/docling）。
- 没有 GPU 或未安装 NVIDIA Container Toolkit 时，`ai-service` 可能无法正常运行。
- 建议先确认前后端主链路可用，再单独引入 AI 服务。

## API 端点

| Method | Path | 描述 |
| --- | --- | --- |
| `GET` | `/ping` | 健康检查 |
| `POST` | `/api/v1/assets/upload` | 上传文件 |
| `GET` | `/api/v1/assets` | 获取资产列表 |
| `GET` | `/api/v1/assets/:id` | 获取单个资产 |
| `DELETE` | `/api/v1/assets/:id` | 删除资产 |

## 关键环境变量

`.env` 主要用于 `docker-compose`：

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

后端本地运行读取以下变量（未设置时有默认值）：

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

## 常见问题排查

### 1) `docker compose up` 报端口占用

报错示例：`bind: address already in use`。

检查占用：

```bash
ss -ltn '( sport = :5432 or sport = :6379 or sport = :9000 or sport = :9001 or sport = :8080 or sport = :5173 )'
```

处理方式：

- 停掉占用进程/服务，或
- 修改 `.env` 中端口映射（例如把 `POSTGRES_PORT` 改为 `15432`）

### 2) Go 编译报 `compile: version "go1.xx" does not match go tool version`

通常是本机 `GOROOT` 指向了旧版本。

临时修复：

```bash
env -u GOROOT go test ./...
env -u GOROOT go run .
```

长期修复（推荐）：

- 检查并删除 shell 配置里的旧 `GOROOT`，例如 `~/.bashrc` / `~/.zshrc`
- 重新加载配置：`source ~/.bashrc`
- 验证：

```bash
go env GOROOT && go version
```

### 3) 前端页面出现 `Failed to fetch`

先确认后端是否在 `:8080`：

```bash
curl -i http://localhost:8080/ping
```

再确认前端 API 地址（`web-ui/src/lib/api.ts` 默认 `http://localhost:8080`）。

### 4) `docker compose ps` 显示 `Created` 而不是 `Up`

说明容器未成功启动（通常是端口冲突或依赖条件未满足）。

查看日志：

```bash
docker compose logs postgres --tail=50
docker compose logs redis --tail=50
docker compose logs minio --tail=50
```

### 5) AI 容器启动慢或模型未加载

- 首次构建下载非常大，耐心等待
- 先检查 GPU：

```bash
nvidia-smi
```

- 再看 AI 日志：

```bash
docker compose --profile app logs ai-service --tail=100
```

## 停止服务

```bash
# 停止 compose 服务
docker compose down

# 停止并删除卷（会清空数据库/对象存储数据）
docker compose down -v
```

若你是本地 `go run` / `npm run dev` 启动，请在对应终端中 `Ctrl+C` 停止。

## 许可证

MIT License
