# ThinkBank - Intelligent Personal Data Asset Management System
## Product Requirement Document (PRD)

### 1. Project Overview
**ThinkBank** is a self-hosted, privacy-first personal data management system. It serves as a "Smart Gallery" and "Second Brain," utilizing local AI models to organize, analyze, and retrieve personal digital assets (photos, documents).

**Core Philosophy:**
* **Data Sovereignty:** All data stays local.
* **Smart Ingestion:** Automated tagging, OCR, and vectorization upon upload.
* **Natural Interaction:** Chat with your data using RAG (Retrieval-Augmented Generation).

### 2. Technology Stack & Constraints

#### 2.1 Backend (Core Service)
* **Language:** Golang (1.23+)
* **Framework:** Hertz (High-performance HTTP framework)
* **Communication:**
    * External: RESTful API (HTTP/2)
    * Internal (to AI Service): gRPC (Protobuf)

#### 2.2 AI Service (Intelligence Layer)
* **Language:** Python 3.11+
* **Orchestration:** LangChain
* **Inference Engine:** vLLM (with `gpu_memory_utilization` limits)
* **Models (Optimized for RTX 4070 8GB VRAM):**
    * **LLM:** `Qwen/Qwen3-VL-8B-Instruct-GPTQ-Int4` (GPU Dedicated)
    * **Vision Captioning:** `HuggingFaceTB/SmolVLM-Instruct` (CPU/Offload)
    * **Image Embedding:** `google/siglip-so400m-patch14-384` (CPU)
    * **Text Embedding:** `BAAI/bge-m3` (CPU)
* **Document Parsing:** `Docling` or `Marker` (PDF to Markdown)

#### 2.3 Database & Storage
* **Relational & Vector DB:** PostgreSQL 16 + `pgvector` extension.
* **Object Storage:** MinIO (S3 Compatible) for raw files and thumbnails.
* **Cache & Queue:** Redis 7 (for async task queues).

#### 2.4 Frontend
* **Framework:** React 19 + Vite
* **UI Library:** shadcn/ui + Tailwind CSS
* **State Management:** Zustand / TanStack Query

#### 2.5 Infrastructure
* **Deployment:** Docker Compose (Full stack)

---

### 3. System Architecture & Workflows

#### 3.1 Architecture Diagram
```mermaid
graph TD
    User[Web Client] -->|HTTP/REST| GoAPI[Go Backend (Hertz)]
    
    subgraph "Data Layer"
        GoAPI -->|Metadata| PG[(PostgreSQL + pgvector)]
        GoAPI -->|File Stream| MinIO[MinIO Storage]
        GoAPI -->|Async Task| Redis[Redis Queue]
    end
    
    subgraph "AI Service (Python)"
        PyWorker[Task Consumer] -->|Pop Task| Redis
        PyWorker -->|Read File| MinIO
        PyWorker -->|Write Vector| PG
        
        GoAPI -.->|gRPC (Real-time Chat)| PyService[Inference Service]
        PyService -->|Load| vLLM[vLLM Engine]
    end

```

#### 3.2 Key Workflows

1. **Ingestion Pipeline (Async):**
* Upload -> Save to MinIO -> Create DB Record (Pending) -> Push ID to Redis.
* Python Worker -> Pop ID -> Download File -> (If Image: Caption + Embedding) / (If Doc: Parse + Embedding) -> Update DB.


2. **RAG Search (Sync):**
* User Query -> Go API -> Python gRPC -> Embed Query -> Vector Search (PG) -> LLM Synthesis -> Return Response.



---

### 4. Database Schema (PostgreSQL)

#### 4.1 Table: `assets`

Core metadata storage.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_name VARCHAR(64) NOT NULL,
    object_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(127) NOT NULL,
    size_bytes BIGINT NOT NULL,
    caption TEXT,          -- AI description or Doc summary
    content_text TEXT,     -- Full OCR/Doc text
    metadata JSONB DEFAULT '{}', -- EXIF, dimensions
    processing_status VARCHAR(32) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

```

#### 4.2 Table: `asset_embeddings`

Separated for performance.

```sql
CREATE TABLE asset_embeddings (
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    semantic_vector vector(1024), -- BGE-M3
    visual_vector vector(1152),   -- SigLIP
    PRIMARY KEY (asset_id)
);
CREATE INDEX ON asset_embeddings USING ivfflat (semantic_vector vector_cosine_ops);

```

---

### 5. API Specification (Internal & External)

#### 5.1 gRPC Definition (`proto/ai_service.proto`)

```protobuf
syntax = "proto3";
package ai_service;

service AiWorker {
  // Trigger analysis manually or check status
  rpc ProcessAsset (AssetRequest) returns (ProcessStatus);
  // RAG Chat Stream
  rpc ChatStream (ChatRequest) returns (stream ChatResponse);
}

message AssetRequest { string asset_id = 1; string file_path = 2; string mime_type = 3; }
message ChatRequest { string query = 1; repeated string history = 2; }
message ChatResponse { string chunk = 1; }
message ProcessStatus { bool success = 1; string error = 2; }

```

#### 5.2 Go REST API

* `POST /api/v1/assets/upload` - Multipart upload.
* `GET /api/v1/assets` - List with pagination.
* `GET /api/v1/search?q={text}&type={semantic|visual}` - Vector search.
* `POST /api/v1/chat` - Interactive chat endpoint.

---

### 6. Project Directory Structure

```
thinkbank/
├── go-backend/         # Hertz App
│   ├── biz/            # Business Logic
│   ├── cmd/            # Main entry
│   ├── conf/           # Config files
│   └── idl/            # Protobuf definitions
├── python-ai/          # AI Service
│   ├── core/           # Model loaders (vLLM, Embeddings)
│   ├── workers/        # Redis consumers
│   └── server.py       # gRPC Server
├── web-ui/             # React App
├── docker-compose.yml
└── PRD.md

