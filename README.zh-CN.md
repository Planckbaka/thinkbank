# ThinkBank

[English](./README.md)

> 智能个人数据资产管理系统 - 自托管、隐私优先的“智能图库”与“第二大脑”

ThinkBank 是一个本地优先的个人数据管理系统，利用本地 AI 模型对个人数字资产（图片、文档）进行组织、分析和检索。

## 核心特性

- 数据主权：所有数据保留在本地，完全掌控
- 智能摄入：上传后自动打标签、OCR 和向量化
- 实时反馈：可视化追踪处理队列与状态
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
├── web-ui/
├── start-infra.sh
├── run-backend-host.sh
├── run-ai-host.sh
├── run-ai-worker-host.sh
├── run-ai-embed-host.sh
├── run-vllm-host.sh
└── run-web-host.sh
```

## 环境要求

- Docker Engine + Docker Compose Plugin
- Go 1.25+
- Node.js 20+
- Python 3.11+
- 可选：NVIDIA GPU + NVIDIA Container Toolkit（AI 容器模式）

## 部署方案

ThinkBank 提供两套部署方案。

### 方案 A：混合部署（基础设施在 Docker，应用在主机）

这套方案对应你的目标：
- Docker：PostgreSQL + Redis + MinIO
- 主机：Go 后端 + Python AI gRPC + Python AI Worker + vLLM + web-ui

1. 准备环境变量：

```bash
cp .env.example .env
```

2. 启动 Docker 基础设施：

```bash
./start-infra.sh
```

3. 在主机启动 vLLM：

```bash
python3 -m venv .venv-vllm
source .venv-vllm/bin/activate
pip install vllm
./run-vllm-host.sh
```

4. 在主机启动 Python AI Embed 服务（新终端）：

```bash
./run-ai-embed-host.sh
```

5. 在主机启动 Python AI gRPC 服务（新终端）：

```bash
./run-ai-host.sh
```

6. 在主机启动 Python AI Worker（新终端）：

```bash
./run-ai-worker-host.sh
```

7. 在主机启动 Go 后端（新终端）：

```bash
./run-backend-host.sh
```

8. 在主机启动前端（新终端）：

```bash
cd web-ui
npm ci
cd ..
./run-web-host.sh
```

9. 验证：

```bash
curl -i http://localhost:8080/ping
curl -i http://localhost:8080/api/v1/ai/health
curl -i http://localhost:8000/v1/models -H "Authorization: Bearer sk-local"
```

### 方案 B：全容器部署（Compose 启动全部服务）

```bash
cp .env.example .env
docker compose --profile app up -d
docker compose --profile app ps
```

说明：
- `llm-engine` 需要 NVIDIA runtime（`nvidia` container runtime / NVIDIA Container Toolkit）。
- `ai-service` 首次构建依赖大，耗时较长。

## API 端点

| Method | Path | 描述 |
| --- | --- | --- |
| `GET` | `/ping` | 健康检查 |
| `POST` | `/api/v1/assets/upload` | 上传文件 |
| `GET` | `/api/v1/assets` | 获取资产列表 |
| `GET` | `/api/v1/assets/:id` | 获取单个资产 |
| `DELETE` | `/api/v1/assets/:id` | 删除资产 |
| `GET` | `/api/v1/ai/health` | 检查 AI 与 LLM 可用性 |
| `GET` | `/api/v1/search?q=&limit=&threshold=` | 混合（矢量 + 字符）检索 |
| `POST` | `/api/v1/chat` | RAG 问答（返回 `answer` 和 `sources`） |

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

主机模式下，`run-backend-host.sh` 会按 `.env` 自动映射这些变量：

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

### 5) `llm-engine` 报 NVIDIA runtime 错误

报错示例：`could not select device driver "nvidia" with capabilities: [[gpu]]`

检查 runtime：

```bash
docker info | rg -i nvidia
```

若没有 `nvidia` runtime：
- 安装 NVIDIA Container Toolkit 并重启 Docker，或
- 切到方案 A，直接在主机运行 `./run-vllm-host.sh`。

### 6) vLLM 报显存不足 (OOM)

如果在 8GB 显卡初始化或生成时崩溃：
- 降低 `.env` 中的 `VLLM_GPU_MEMORY_UTILIZATION`（默认 0.7 或 0.8）：
  ```env
  VLLM_GPU_MEMORY_UTILIZATION=0.6
  ```
- 降低 Context 长度：
  ```env
  VLLM_MAX_MODEL_LEN=2048
  ```

### 7) 服务无法重启 / 端口持续占用

如果停止服务后，`./run-backend-host.sh` 仍报 "address already in use"：
- 说明可能有僵尸进程未被杀死。
- 运行强力清理脚本：
  ```bash
  ./stop-host-app.sh
  ```
- 或手动杀死相关进程：
  ```bash
  pkill -f "thinkbank/backend"
  pkill -f "workers.asset_processor"
  ```

## 停止服务

```bash
# 停止 compose 服务
docker compose down

# 停止并删除卷（会清空数据库/对象存储数据）
docker compose down -v
```

若你是本地 `go run` / `npm run dev` 启动，请在对应终端中 `Ctrl+C` 停止。

若你通过 `./start-host-app.sh` 后台启动主机模式服务，可用：

```bash
./stop-host-app.sh
```

## 许可证

MIT License
