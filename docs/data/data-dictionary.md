# Data Dictionary

This document provides detailed definitions for all database tables and fields.

---

## Table: `assets`

Primary table storing asset metadata.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `bucket_name` | VARCHAR(64) | NO | - | MinIO bucket name (e.g., "thinkbank") |
| `object_name` | VARCHAR(255) | NO | - | MinIO object path (e.g., `{uuid}/{uuid}`) |
| `mime_type` | VARCHAR(127) | NO | - | MIME type of the uploaded file |
| `size_bytes` | BIGINT | NO | - | File size in bytes |
| `caption` | TEXT | YES | NULL | AI-generated caption (images) or summary (documents) |
| `content_text` | TEXT | YES | NULL | Extracted text (OCR for images, parsed for documents) |
| `metadata` | JSONB | NO | `'{}'` | Additional metadata (EXIF, dimensions, etc.) |
| `processing_status` | VARCHAR(32) | NO | `'PENDING'` | Current processing status |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp (auto-updated) |

### Enum Values: `processing_status`

| Value | Description |
|-------|-------------|
| `PENDING` | Uploaded, waiting in processing queue |
| `PROCESSING` | Currently being processed by AI pipeline |
| `COMPLETED` | Successfully processed (embeddings generated) |
| `FAILED` | Processing failed (check `processing_tasks.error_message`) |

### JSONB: `metadata` Structure

```json
{
  // Image-specific
  "width": 1920,
  "height": 1080,
  "camera": "iPhone 14 Pro",
  "taken_at": "2024-01-15T10:30:00Z",
  "exif": {
    "focal_length": "4.2mm",
    "iso": 100,
    "aperture": "f/1.8"
  },

  // Document-specific
  "page_count": 12,
  "author": "Document Author",
  "title": "Document Title",

  // Common
  "original_filename": "photo.jpg"
}
```

---

## Table: `asset_embeddings`

Vector embeddings for semantic search. Separated from `assets` for performance.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `asset_id` | UUID | NO | - | Primary key, references `assets.id` |
| `semantic_vector` | VECTOR(1024) | YES | NULL | BGE-M3 text embedding |
| `visual_vector` | VECTOR(1152) | YES | NULL | SigLIP image embedding |

### Embedding Dimensions

| Vector Type | Model | Dimensions | Use Case |
|-------------|-------|------------|----------|
| `semantic_vector` | BAAI/bge-m3 | 1024 | Text semantic search |
| `visual_vector` | google/siglip-so400m-patch14-384 | 1152 | Image similarity search |

### Constraints

```sql
PRIMARY KEY (asset_id)
FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
```

---

## Table: `processing_tasks`

Tracks async processing job status.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `asset_id` | UUID | NO | - | References `assets.id` |
| `status` | VARCHAR(32) | NO | `'PENDING'` | Task status |
| `stage` | VARCHAR(32) | NO | `'QUEUED'` | Current processing stage |
| `progress` | FLOAT | NO | `0.0` | Progress percentage (0.0-1.0) |
| `error_message` | TEXT | YES | NULL | Error details if failed |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Task creation time |
| `started_at` | TIMESTAMPTZ | YES | NULL | When processing started |
| `completed_at` | TIMESTAMPTZ | YES | NULL | When processing finished |

### Enum Values: `status`

| Value | Description |
|-------|-------------|
| `PENDING` | Task created, not started |
| `PROCESSING` | Task in progress |
| `COMPLETED` | Task finished successfully |
| `FAILED` | Task failed (see `error_message`) |

### Enum Values: `stage`

| Value | Description |
|-------|-------------|
| `QUEUED` | Waiting in Redis queue |
| `DOWNLOADING` | Downloading file from MinIO |
| `PROCESSING` | Running AI models (caption, OCR, etc.) |
| `EMBEDDING` | Generating vector embeddings |
| `COMPLETED` | All stages finished |

### Constraints

```sql
FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
```

---

## Table: `chat_history`

Stores conversation history for RAG chat.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `session_id` | UUID | NO | - | Conversation session identifier |
| `role` | VARCHAR(16) | NO | - | Message sender role |
| `content` | TEXT | NO | - | Message content |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Message timestamp |

### Enum Values: `role`

| Value | Description |
|-------|-------------|
| `user` | Message from the user |
| `assistant` | Message from the AI assistant |

### Session Management

- Sessions are identified by `session_id` (UUID)
- Messages are ordered by `created_at` within each session
- Sessions can span multiple days
- No automatic cleanup (manual or scheduled job needed)

---

## Triggers

### Auto-update `updated_at`

```sql
CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

The `updated_at` column is automatically set to `NOW()` on every UPDATE.

---

## Common Queries

### Get assets by status

```sql
SELECT * FROM assets
WHERE processing_status = 'COMPLETED'
ORDER BY created_at DESC
LIMIT 20;
```

### Get processing queue size

```sql
SELECT status, COUNT(*)
FROM processing_tasks
GROUP BY status;
```

### Vector similarity search

```sql
SELECT
    a.id,
    a.caption,
    1 - (e.semantic_vector <=> '[0.1, 0.2, ...]'::vector) AS score
FROM assets a
JOIN asset_embeddings e ON a.id = e.asset_id
ORDER BY e.semantic_vector <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Get chat session history

```sql
SELECT role, content, created_at
FROM chat_history
WHERE session_id = 'session-uuid'
ORDER BY created_at ASC;
```

---

## Data Retention

| Data Type | Retention Policy |
|-----------|------------------|
| Assets | Until manually deleted |
| Processing Tasks | Until parent asset deleted |
| Chat History | Until session deleted (manual) |
| Embeddings | Until parent asset deleted |

---

## Backup Considerations

### Critical Data (Frequent backups)

- `assets` table
- `asset_embeddings` table

### Operational Data (Regular backups)

- `processing_tasks` table (can be regenerated)
- `chat_history` table

### Backup Command

```bash
# Full backup
pg_dump -U thinkbank -d thinkbank -F c -f thinkbank_backup.dump

# Schema only
pg_dump -U thinkbank -d thinkbank --schema-only -f schema.sql
```
