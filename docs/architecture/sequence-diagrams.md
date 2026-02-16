# Sequence Diagrams

This document illustrates the key workflows in ThinkBank using sequence diagrams.

## 1. Asset Upload Pipeline

The complete flow when a user uploads a file.

```mermaid
sequenceDiagram
    actor User
    participant Browser as Web UI
    participant Go as Go Backend
    participant Minio as MinIO
    participant DB as PostgreSQL
    participant Redis as Redis Queue
    participant Worker as Python Worker
    participant AI as AI Models

    User->>Browser: Select file to upload
    Browser->>Go: POST /api/v1/assets/upload
    Note over Go: Validate file type & size

    alt Invalid file
        Go-->>Browser: 400 Error (InvalidFileType)
        Browser-->>User: Show error message
    else Valid file
        Go->>Go: Generate UUID
        Go->>Minio: Store file (bucket/object)
        Minio-->>Go: Object path
        Go->>DB: INSERT asset (status: PENDING)
        Go->>DB: INSERT processing_task
        Go->>Redis: LPUSH asset_id
        Go-->>Browser: 200 { asset_id, message }
        Browser-->>User: Show upload success

        Note over Redis,Worker: Async Processing
        Worker->>Redis: BRPOP (blocking)
        Redis-->>Worker: asset_id
        Worker->>DB: UPDATE task (PROCESSING)
        Worker->>Minio: Download file

        alt Image file
            Worker->>AI: Generate caption (SmolVLM)
            AI-->>Worker: Caption text
            Worker->>AI: Generate visual embedding (SigLIP)
            AI-->>Worker: 1152-dim vector
        else Document file
            Worker->>AI: Extract text (Docling)
            AI-->>Worker: Text content
            Worker->>AI: Generate semantic embedding (BGE-M3)
            AI-->>Worker: 1024-dim vector
        end

        Worker->>DB: UPDATE asset (caption, content, status: COMPLETED)
        Worker->>DB: INSERT/UPDATE embedding
        Worker->>DB: UPDATE task (COMPLETED)
    end
```

---

## 2. RAG Chat Flow

The flow when a user queries their knowledge base.

```mermaid
sequenceDiagram
    actor User
    participant Browser as Web UI
    participant Go as Go Backend
    participant AI as Python AI (gRPC)
    participant DB as PostgreSQL
    participant LLM as vLLM Server

    User->>Browser: Type question
    Browser->>Go: POST /api/v1/chat (query)
    Go->>AI: ChatStream(gRPC)

    Note over AI: Step 1: Embed query
    AI->>AI: BGE-M3 encode query
    AI->>AI: Get 1024-dim vector

    Note over AI,DB: Step 2: Vector search
    AI->>DB: SELECT with vector similarity
    DB-->>AI: Top-K relevant documents

    Note over AI,LLM: Step 3: RAG generation
    AI->>AI: Build context from results
    AI->>LLM: POST /v1/chat/completions
    Note over LLM: System prompt + context + query

    loop Streaming response
        LLM-->>AI: Response chunk
        AI-->>Go: ChatResponse chunk (gRPC stream)
        Go-->>Browser: SSE chunk
        Browser-->>User: Display chunk
    end

    AI-->>Go: Final chunk + sources
    Go-->>Browser: Final response with sources
    Browser-->>User: Show source references
```

---

## 3. Asset Processing Worker Detail

Detailed view of the Python worker's processing logic.

```mermaid
flowchart TD
    Start[Worker Start] --> Connect[Connect to Redis, DB, MinIO]
    Connect --> Listen[BRPOP from queue]

    Listen --> Pop{Got asset_id?}
    Pop -->|No| Listen
    Pop -->|Yes| Load[Load asset from DB]

    Load --> CheckStatus{Status?}
    CheckStatus-->|Already processed| Listen
    CheckStatus-->|PENDING| UpdateProc[Update status: PROCESSING]
    CheckStatus-->|FAILED| UpdateProc

    UpdateProc --> Download[Download from MinIO]
    Download --> DetectType{MIME Type?}

    DetectType -->|image/*| ImageFlow[Image Processing]
    DetectType -->|application/pdf| DocFlow[Document Processing]
    DetectType -->|text/*| TextFlow[Text Processing]

    subgraph ImageProcessing [Image Processing]
        ImageFlow --> Caption[Generate Caption<br/>SmolVLM]
        Caption --> VisEmbed[Visual Embedding<br/>SigLIP 1152-dim]
    end

    subgraph DocumentProcessing [Document Processing]
        DocFlow --> Parse[Parse Document<br/>Docling]
        Parse --> Extract[Extract Text]
        Extract --> SemEmbed[Semantic Embedding<br/>BGE-M3 1024-dim]
    end

    subgraph TextProcessing [Text Processing]
        TextFlow --> TextEmbed[Semantic Embedding<br/>BGE-M3 1024-dim]
    end

    VisEmbed --> SaveResults[Save to DB]
    SemEmbed --> SaveResults
    TextEmbed --> SaveResults

    SaveResults --> UpdateComplete[Update status: COMPLETED]
    UpdateComplete --> Listen

    Caption -->|Error| HandleError[Log error, Update: FAILED]
    Parse -->|Error| HandleError
    HandleError --> Listen
```

---

## 4. Asset Retrieval Flow

How assets are retrieved for display in the gallery.

```mermaid
sequenceDiagram
    actor User
    participant Browser as Web UI
    participant Go as Go Backend
    participant DB as PostgreSQL
    participant Minio as MinIO

    User->>Browser: Open gallery page
    Browser->>Go: GET /api/v1/assets?page=1&per_page=20

    Go->>DB: SELECT COUNT(*) FROM assets
    DB-->>Go: total count

    Go->>DB: SELECT * FROM assets<br/>ORDER BY created_at DESC<br/>LIMIT 20 OFFSET 0
    DB-->>Go: asset rows

    loop For each asset
        Go->>Minio: Generate presigned URL (1hr TTL)
        Minio-->>Go: Signed URL
    end

    Go-->>Browser: 200 { assets, total, page, per_page }

    Browser->>Browser: Render bento grid
    Browser-->>User: Display assets with thumbnails

    Note over User,Browser: User scrolls / clicks load more
    Browser->>Go: GET /api/v1/assets?page=2
    Note over Go,Minio: Repeat process...
```

---

## 5. Error Recovery Flow

How the system handles processing failures.

```mermaid
flowchart TD
    Start[Processing Task] --> Execute[Execute Processing]

    Execute --> Check{Success?}
    Check -->|Yes| Complete[Mark COMPLETED]

    Check -->|No| Error[Capture Error]
    Error --> Log[Log error details]
    Log --> UpdateFail[Update status: FAILED]
    UpdateFail --> StoreErr[Store error_message in task]

    StoreErr --> Notify{Retry enabled?}
    Notify -->|Yes| Retry[Push back to queue<br/>with delay]
    Notify -->|No| End[End]

    Retry --> CheckRetry{Max retries?}
    CheckRetry -->|No| Wait[Wait exponential backoff]
    Wait --> Execute
    CheckRetry -->|Yes| Manual[Alert for manual review]
    Manual --> End

    Complete --> End
```

---

## 6. Vector Search Flow

Detailed view of how similarity search works.

```mermaid
sequenceDiagram
    participant Client
    participant AI as Python AI
    participant Embed as BGE-M3 Model
    participant DB as PostgreSQL<br/>+ pgvector

    Client->>AI: VectorSearch(query, limit, threshold)
    AI->>Embed: Encode query text

    Note over Embed: CPU inference
    Embed-->>AI: 1024-dim vector

    AI->>DB: SELECT asset_id, caption, metadata<br/>1 - (semantic_vector <=> query_vec) as score<br/>WHERE score > threshold<br/>ORDER BY score DESC<br/>LIMIT k

    Note over DB: Uses IVFFlat index<br/>for approximate search

    DB-->>AI: Results with similarity scores

    AI->>AI: Format results
    AI-->>Client: SearchResponse with results
```

### Vector Search SQL Example

```sql
-- Cosine similarity search (smaller distance = more similar)
SELECT
    a.id,
    a.caption,
    a.mime_type,
    1 - (e.semantic_vector <=> '[0.1, 0.2, ...]'::vector) as score
FROM assets a
JOIN asset_embeddings e ON a.id = e.asset_id
WHERE 1 - (e.semantic_vector <=> '[0.1, 0.2, ...]'::vector) > 0.7
ORDER BY e.semantic_vector <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```
