# Entity-Relationship Diagram

This document visualizes the database schema using Mermaid ER diagrams.

## Complete Schema

```mermaid
erDiagram
    assets ||--o| asset_embeddings : "has"
    assets ||--o{ processing_tasks : "has"
    assets ||--o{ chat_history : "references"

    assets {
        uuid id PK "Primary key, auto-generated"
        varchar bucket_name "MinIO bucket name"
        varchar object_name "MinIO object path"
        varchar mime_type "File MIME type"
        bigint size_bytes "File size in bytes"
        text caption "AI-generated description"
        text content_text "Extracted/OCR text"
        jsonb metadata "EXIF, dimensions, etc."
        varchar processing_status "PENDING/PROCESSING/COMPLETED/FAILED"
        timestamp created_at "Upload timestamp"
        timestamp updated_at "Last modification"
    }

    asset_embeddings {
        uuid asset_id PK,FK "References assets.id"
        vector semantic_vector "BGE-M3 embedding (1024 dims)"
        vector visual_vector "SigLIP embedding (1152 dims)"
    }

    processing_tasks {
        uuid id PK "Task identifier"
        uuid asset_id FK "References assets.id"
        varchar status "PENDING/PROCESSING/COMPLETED/FAILED"
        varchar stage "QUEUED/DOWNLOADING/PROCESSING/EMBEDDING/COMPLETED"
        float progress "0.0 to 1.0"
        text error_message "Error details if failed"
        timestamp created_at "Task creation time"
        timestamp started_at "Processing start time"
        timestamp completed_at "Processing end time"
    }

    chat_history {
        uuid id PK "Message identifier"
        uuid session_id "Conversation session"
        varchar role "user or assistant"
        text content "Message content"
        timestamp created_at "Message timestamp"
    }
```

## Relationships Explained

### assets ↔ asset_embeddings (1:1)

- Each asset has at most one embedding record
- Embeddings are stored separately for performance
- **On Delete**: CASCADE (deleting asset removes embeddings)

### assets ↔ processing_tasks (1:N)

- Each asset can have multiple processing tasks (retries)
- Most recent task indicates current processing state
- **On Delete**: CASCADE

### chat_history (Standalone)

- Chat messages are independent of assets
- Grouped by `session_id` for conversation continuity
- Assets may be referenced in content (not enforced by FK)

---

## Index Strategy

```mermaid
graph LR
    subgraph assets
        PK[id PK]
        IDX1[mime_type]
        IDX2[processing_status]
        IDX3[created_at DESC]
        IDX4[metadata GIN]
    end

    subgraph asset_embeddings
        PK2[asset_id PK]
        V1[semantic_vector IVFFlat]
        V2[visual_vector IVFFlat]
    end

    subgraph processing_tasks
        PK3[id PK]
        IDX5[status]
    end

    subgraph chat_history
        PK4[id PK]
        IDX6[session_id, created_at]
    end
```

### Index Details

| Table | Index Name | Type | Columns | Purpose |
|-------|------------|------|---------|---------|
| assets | `assets_pkey` | B-tree | `id` | Primary key lookup |
| assets | `idx_assets_mime_type` | B-tree | `mime_type` | Filter by file type |
| assets | `idx_assets_processing_status` | B-tree | `processing_status` | Filter by status |
| assets | `idx_assets_created_at` | B-tree | `created_at DESC` | Chronological ordering |
| assets | `idx_assets_metadata` | GIN | `metadata` | JSONB queries |
| asset_embeddings | `asset_embeddings_pkey` | B-tree | `asset_id` | FK lookup |
| asset_embeddings | `idx_semantic_vector` | IVFFlat | `semantic_vector` | Text similarity search |
| asset_embeddings | `idx_visual_vector` | IVFFlat | `visual_vector` | Image similarity search |
| processing_tasks | `idx_processing_tasks_status` | B-tree | `status` | Queue monitoring |
| chat_history | `idx_chat_history_session` | B-tree | `session_id, created_at` | Conversation retrieval |

---

## Vector Index Configuration

The IVFFlat indexes for vector similarity search use the following configuration:

```sql
-- Semantic vector index (BGE-M3, 1024 dimensions)
CREATE INDEX idx_semantic_vector
ON asset_embeddings USING ivfflat (semantic_vector vector_cosine_ops)
WITH (lists = 100);

-- Visual vector index (SigLIP, 1152 dimensions)
CREATE INDEX idx_visual_vector
ON asset_embeddings USING ivfflat (visual_vector vector_cosine_ops)
WITH (lists = 100);
```

### Parameters

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| `lists` | 100 | Number of clusters for IVF indexing |
| `vector_cosine_ops` | - | Uses cosine distance (1 - similarity) |

### When to Reindex

Recreate indexes when dataset size changes significantly:

| Asset Count | Recommended `lists` |
|-------------|---------------------|
| < 10,000 | 10-50 |
| 10,000 - 100,000 | 100 |
| 100,000 - 1,000,000 | 200-500 |
| > 1,000,000 | 500-1000 |
