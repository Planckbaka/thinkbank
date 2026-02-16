# ADR-004: PostgreSQL with pgvector for Vector Storage

## Status

**Accepted**

## Context

ThinkBank requires vector similarity search for:
- Semantic text search (RAG context retrieval)
- Image similarity search (visual search)
- Hybrid search combining both modalals

We need to store:
- Text embeddings: 1024 dimensions (BGE-M3)
- Image embeddings: 1152 dimensions (SigLIP)

## Decision

We will use **PostgreSQL with the pgvector extension** for vector storage and similarity search.

## Alternatives Considered

### 1. Specialized Vector Databases (Pinecone, Weaviate, Qdrant)

| Pros | Cons |
|------|------|
| Purpose-built for vectors | Additional infrastructure |
| Better scaling (billions of vectors) | Operational complexity |
| More indexing options | Data duplication (metadata in RDBMS) |
| Native hybrid search | Learning curve |

### 2. Elasticsearch with Vector Support

| Pros | Cons |
|------|------|
| Familiar to many teams | Heavier resource usage |
| Good for hybrid search | Java-based (memory) |
| Full-text search built-in | Vector support is newer |

### 3. SQLite with sqlite-vss

| Pros | Cons |
|------|------|
| Zero infrastructure | Not production-ready |
| Simple deployment | Limited scalability |
| Good for development | No concurrent writes |

### 4. PostgreSQL + pgvector (Chosen)

| Pros | Cons |
|------|------|
| Single database for all data | Less optimized than specialized DBs |
| ACID transactions | Fewer index types |
| Mature ecosystem | Scale limitations (~10M vectors) |
| No new infrastructure | |
| Familiar tooling | |

## Consequences

### Positive

- **Single source of truth**: Assets, embeddings, and metadata in one database
- **ACID guarantees**: Vector updates are transactional with asset updates
- **Operational simplicity**: One less service to deploy and monitor
- **Cost effective**: No separate vector DB licensing/hosting
- **SQL familiarity**: Team already knows PostgreSQL

### Negative

- **Scale limitations**: pgvector is optimized for <10M vectors
- **Index limitations**: Only IVFFlat and HNSW indexes available
- **Memory usage**: Vector indexes can be memory-intensive
- **Performance**: Specialized DBs are faster for pure vector search

### Neutral

- Requires PostgreSQL 11+ (using 16 for latest features)
- IVFFlat index works well for datasets of our expected size

## Scale Considerations

| Dataset Size | Recommendation |
|--------------|----------------|
| < 100K vectors | pgvector (excellent) |
| 100K - 1M vectors | pgvector (good) |
| 1M - 10M vectors | pgvector (acceptable with tuning) |
| > 10M vectors | Consider specialized DB |

For personal/single-tenant use, we expect <100K vectors per deployment.

## Index Strategy

We use IVFFlat (Inverted File) indexes:

```sql
CREATE INDEX idx_semantic_vector
ON asset_embeddings USING ivfflat (semantic_vector vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_visual_vector
ON asset_embeddings USING ivfflat (visual_vector vector_cosine_ops)
WITH (lists = 100);
```

### Why IVFFlat?

- **Faster build time** than HNSW
- **Lower memory usage**
- **Good enough accuracy** for our scale
- **Lists = 100** is appropriate for expected dataset sizes

## Schema Design

Vectors are stored in a separate table for performance:

```sql
-- Main assets table
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    -- ... other fields
);

-- Separate embeddings table
CREATE TABLE asset_embeddings (
    asset_id UUID PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
    semantic_vector vector(1024),
    visual_vector vector(1152)
);
```

**Rationale**: Separating embeddings allows:
- Independent backups
- Faster scans on assets table (no vector I/O)
- Option to move to specialized DB later

## Query Example

```sql
-- Cosine similarity search
SELECT
    a.id,
    a.caption,
    1 - (e.semantic_vector <=> :query_vector) AS score
FROM assets a
JOIN asset_embeddings e ON a.id = e.asset_id
WHERE 1 - (e.semantic_vector <=> :query_vector) > 0.7
ORDER BY e.semantic_vector <=> :query_vector
LIMIT 10;
```

## Migration Path

If we outgrow pgvector:

1. **Export vectors** from PostgreSQL
2. **Deploy specialized DB** (e.g., Qdrant)
3. **Dual-write** during transition
4. **Migrate queries** to new DB
5. **Remove pgvector** column

## Related

- [ADR-002: Separate Python Service for AI/ML](002-python-ai-service.md)
- [Data Dictionary: asset_embeddings](../data/data-dictionary.md)
