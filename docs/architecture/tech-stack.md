# Technology Stack

This document provides a comprehensive reference of all technologies used in ThinkBank.

## Overview

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | React + Vite | 19.x / 6.x | UI framework & build tool |
| Backend API | Go + Hertz | 1.25+ | HTTP server |
| AI Service | Python + gRPC | 3.11+ | AI processing |
| LLM Engine | vLLM | Latest | Model inference |
| Database | PostgreSQL | 16 | Relational + vector storage |
| Object Storage | MinIO | Latest | File storage |
| Cache/Queue | Redis | 7.x | Task queue |

---

## Frontend Stack

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 19.x | UI library |
| `react-dom` | 19.x | DOM rendering |
| `react-router-dom` | 7.x | Client-side routing |
| `vite` | 6.x | Build tool & dev server |

### UI Components

| Package | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/*` | Latest | Headless UI primitives |
| `tailwindcss` | 4.x | Utility-first CSS |
| `class-variance-authority` | Latest | Component variants |
| `lucide-react` | Latest | Icon library |

### Data Fetching

| Package | Version | Purpose |
|---------|---------|---------|
| `@tanstack/react-query` | 5.x | Server state management |
| `axios` | Latest | HTTP client |

---

## Backend Stack (Go)

### Core Dependencies

```go
// HTTP Framework
github.com/cloudwego/hertz v0.9.x

// Database
gorm.io/gorm v1.25.x
gorm.io/driver/postgres v1.5.x

// Object Storage
github.com/minio/minio-go/v7 v7.0.x

// Cache
github.com/redis/go-redis/v9 v9.5.x

// Utilities
github.com/google/uuid v1.6.x
```

### Project Structure

```
go-backend/
├── main.go              # Entry point
├── router.go            # Route registration
├── biz/
│   ├── handler/         # HTTP handlers
│   ├── model/           # Data models (GORM)
│   ├── dal/             # Data Access Layer
│   │   ├── postgres/    # PostgreSQL connection
│   │   ├── redis/       # Redis connection
│   │   └── minio/       # MinIO connection
│   └── pkg/errno/       # Error definitions
└── idl/
    └── ai_service.proto # gRPC definitions
```

---

## AI Service Stack (Python)

### Core Dependencies

```txt
# gRPC
grpcio>=1.60.0
grpcio-tools>=1.60.0

# LLM & Embeddings
langchain>=0.1.0
langchain-openai>=0.1.0
sentence-transformers>=2.2.0
transformers>=4.36.0

# Document Processing
docling>=1.0.0

# Database
psycopg2-binary>=2.9.0
pgvector>=0.2.0

# Storage
minio>=7.2.0
redis>=5.0.0

# Utilities
pydantic-settings>=2.0.0
loguru>=0.7.0
python-multipart>=0.0.6
```

### Project Structure

```
python-ai/
├── server.py            # gRPC server entry
├── worker.py            # Standalone worker
├── core/
│   ├── config.py        # Pydantic settings
│   ├── llm.py           # vLLM client
│   ├── embeddings.py    # BGE-M3 & SigLIP
│   └── vision.py        # SmolVLM captioning
└── workers/
    └── asset_processor.py  # Queue consumer
```

---

## AI Models

### Model Inventory

| Model | Purpose | Hardware | Dimensions |
|-------|---------|----------|------------|
| Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4 | Chat & summarization | GPU (8GB VRAM) | - |
| BAAI/bge-m3 | Text embeddings | CPU | 1024 |
| google/siglip-so400m-patch14-384 | Image embeddings | CPU | 1152 |
| HuggingFaceTB/SmolVLM-Instruct | Image captioning | CPU/GPU | - |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | RTX 3060 (12GB) | RTX 4070 (8GB+) |
| **CPU** | 8 cores | 16+ cores |
| **RAM** | 16GB | 32GB+ |
| **Storage** | 50GB SSD | 100GB+ NVMe |

### Model Allocation Strategy

```
┌─────────────────────────────────────────┐
│              GPU (8GB VRAM)              │
│  ┌─────────────────────────────────────┐│
│  │     Qwen2.5-7B-Instruct-GPTQ-Int4   ││
│  │         (~4GB model + KV cache)      ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│                 CPU                      │
│  ┌─────────┐ ┌─────────┐ ┌────────────┐│
│  │ BGE-M3  │ │ SigLIP  │ │  SmolVLM   ││
│  │ (text)  │ │ (image) │ │ (caption)  ││
│  └─────────┘ └─────────┘ └────────────┘│
└─────────────────────────────────────────┘
```

---

## Infrastructure

### Docker Services

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    volumes: ["minio_data:/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: ["redis_data:/data"]
```

### Database Extensions

| Extension | Purpose |
|-----------|---------|
| `pgvector` | Vector similarity search |
| `uuid-ossp` | UUID generation |

---

## Development Tools

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Go | 1.25+ | Backend development |
| Python | 3.11+ | AI service development |
| Node.js | 20.x+ | Frontend development |
| Docker | 24.x+ | Container runtime |
| Docker Compose | 2.x+ | Multi-container orchestration |

### Optional Tools

| Tool | Purpose |
|------|---------|
| `protoc` | Protobuf compilation |
| `swagger-cli` | OpenAPI validation |
| `pgvector` CLI | Vector operations |

---

## External APIs

### vLLM OpenAI-Compatible API

```bash
# Chat completion
POST http://localhost:8000/v1/chat/completions
Content-Type: application/json

{
  "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
  "messages": [...],
  "stream": true,
  "max_tokens": 2048
}
```

---

## Version Compatibility Matrix

| Go | Python | Node.js | PostgreSQL |
|----|--------|---------|------------|
| 1.25+ | 3.11+ | 20.x+ | 16 |
| 1.24 | 3.10 | 18.x | 15 |
| 1.23 | 3.9 | 16.x | 14 |

**Recommended**: Use the latest stable versions for all components.
