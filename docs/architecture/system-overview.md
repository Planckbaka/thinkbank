# System Overview

This document provides a high-level overview of the ThinkBank system architecture using the C4 model.

## C4 Context Diagram

The Context diagram shows ThinkBank in relation to users and external systems.

```mermaid
graph TB
    User[User] -->|Uploads files, Queries| TB[ThinkBank System]

    subgraph External
        LLM[External LLM API<br/>vLLM/OpenAI-compatible]
    end

    TB -->|Generates responses| User
    TB -->|API calls| LLM
    LLM -->|AI responses| TB

    style TB fill:#4A90D9,color:#fff
    style User fill:#7CB342,color:#fff
    style LLM fill:#FF7043,color:#fff
```

### System Description

**ThinkBank** is a self-hosted, privacy-first intelligent personal data asset management system that serves as:

- **Smart Gallery**: Automatically organizes and tags images
- **Second Brain**: Manages documents with semantic search
- **RAG Chat**: Conversational interface to query your knowledge base

### Key Characteristics

| Attribute | Description |
|-----------|-------------|
| **Data Sovereignty** | All data stays local - nothing sent to external clouds |
| **AI-Powered** | Local AI models for tagging, OCR, and search |
| **Hybrid Deployment** | Infrastructure in Docker, AI services on host (optional) |

---

## C4 Container Diagram

The Container diagram shows the high-level technical building blocks.

```mermaid
graph TB
    subgraph Client
        Browser[Web Browser<br/>React SPA]
    end

    subgraph ThinkBank System
        GoBackend[Go Backend<br/>Hertz HTTP Server<br/>:8080]
        PythonAI[Python AI Service<br/>gRPC Server<br/>:50051]
        vLLM[vLLM Server<br/>OpenAI-Compatible<br/>:8000]
    end

    subgraph Data Stores
        PostgreSQL[(PostgreSQL 16<br/>+ pgvector)]
        MinIO[(MinIO<br/>Object Storage)]
        Redis[(Redis 7<br/>Task Queue)]
    end

    Browser -->|REST API| GoBackend
    GoBackend -->|gRPC| PythonAI
    PythonAI -->|HTTP API| vLLM

    GoBackend -->|SQL| PostgreSQL
    GoBackend -->|S3 API| MinIO
    GoBackend -->|Push tasks| Redis

    PythonAI -->|SQL + Vector| PostgreSQL
    PythonAI -->|S3 API| MinIO
    PythonAI -->|Pop tasks| Redis

    style GoBackend fill:#00ADD8,color:#fff
    style PythonAI fill:#3776AB,color:#fff
    style vLLM fill:#FF6F00,color:#fff
    style PostgreSQL fill:#336791,color:#fff
    style MinIO fill:#C72C48,color:#fff
    style Redis fill:#DC382D,color:#fff
```

### Container Descriptions

| Container | Technology | Purpose |
|-----------|------------|---------|
| **Go Backend** | Go 1.25+, CloudWeGo Hertz | REST API server, asset management, authentication |
| **Python AI Service** | Python 3.11+, gRPC | AI processing pipeline, embeddings, RAG |
| **vLLM Server** | vLLM, Qwen2.5-7B | LLM inference for chat and summarization |
| **Web UI** | React 19, Vite | Single-page application frontend |
| **PostgreSQL** | PostgreSQL 16 + pgvector | Relational + vector storage |
| **MinIO** | MinIO | S3-compatible object storage |
| **Redis** | Redis 7 | Task queue for async processing |

---

## Component Diagram - Go Backend

```mermaid
graph LR
    subgraph HTTP Handlers
        Ping[Ping Handler]
        Asset[Asset Handler]
        AI[AI Handler]
    end

    subgraph Data Access Layer
        PG[Postgres DAL]
        Minio[MinIO DAL]
        RedisDAL[Redis DAL]
    end

    subgraph Models
        AssetModel[Asset]
        EmbedModel[AssetEmbedding]
        TaskModel[ProcessingTask]
    end

    Ping --> PG
    Asset --> PG
    Asset --> Minio
    Asset --> RedisDAL
    AI --> gRPCClient[gRPC Client]

    PG --> AssetModel
    PG --> EmbedModel
    PG --> TaskModel
```

---

## Component Diagram - Python AI Service

```mermaid
graph TB
    subgraph gRPC Service
        ProcessAsset[ProcessAsset RPC]
        ChatStream[ChatStream RPC]
        GetEmbedding[GetEmbedding RPC]
        VectorSearch[VectorSearch RPC]
    end

    subgraph Core Modules
        LLM[LLM Client<br/>vLLM/OpenAI]
        Embeddings[Embeddings<br/>BGE-M3 / SigLIP]
        Vision[Vision<br/>SmolVLM]
    end

    subgraph Workers
        AssetProcessor[Asset Processor<br/>Redis Consumer]
    end

    ProcessAsset --> AssetProcessor
    ChatStream --> LLM
    ChatStream --> VectorSearch
    GetEmbedding --> Embeddings
    GetEmbedding --> Vision
    VectorSearch --> VectorDB[(pgvector)]

    AssetProcessor --> LLM
    AssetProcessor --> Embeddings
    AssetProcessor --> Vision
```

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Network                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │PostgreSQL│  │  MinIO  │  │  Redis  │  │ (Optional) App  │ │
│  │  :5432  │  │  :9000  │  │  :6379  │  │   Containers    │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
└───────┼────────────┼────────────┼─────────────────┼─────────┘
        │            │            │                 │
        └────────────┴────────────┴─────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐       ┌─────┴─────┐      ┌────┴────┐
   │   Go    │       │  Python   │      │  vLLM   │
   │ Backend │       │    AI     │      │ :8000   │
   │  :8080  │       │  :50051   │      └─────────┘
   └─────────┘       └───────────┘
        │                  │
        └────────┬─────────┘
                 │
           ┌─────┴─────┐
           │  Web UI   │
           │   :5173   │
           └───────────┘
```

### Port Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Web UI | 5173 | HTTP | Frontend development server |
| Go Backend | 8080 | HTTP | REST API |
| Python AI | 50051 | gRPC | AI processing |
| vLLM | 8000 | HTTP | LLM inference |
| PostgreSQL | 5432 | TCP | Database |
| MinIO API | 9000 | HTTP | Object storage |
| MinIO Console | 9001 | HTTP | Admin UI |
| Redis | 6379 | TCP | Cache/Queue |
