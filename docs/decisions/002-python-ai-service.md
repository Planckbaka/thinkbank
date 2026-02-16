# ADR-002: Separate Python Service for AI/ML

## Status

**Accepted**

## Context

ThinkBank requires AI/ML capabilities for:
- Text embeddings (BGE-M3)
- Image embeddings (SigLIP)
- Image captioning (SmolVLM)
- Document parsing (Docling)
- LLM inference orchestration

The Python ecosystem dominates the AI/ML space with the best library support for these tasks.

## Decision

We will implement a **separate Python service** for all AI/ML processing, communicating with the Go backend via gRPC.

## Alternatives Considered

### 1. All-in-One Go Service with CGO

| Pros | Cons |
|------|------|
| Single codebase | CGO complexity |
| No network latency | Limited ML library support |
| Simpler deployment | Performance overhead from Python C bindings |

**Rejected**: The Go ML ecosystem is immature. Most cutting-edge models have Python-first implementations.

### 2. All-in-One Python Service

| Pros | Cons |
|------|------|
| Best ML ecosystem | Slower HTTP performance |
| Simpler architecture | Not ideal for CRUD operations |
| Single codebase | Concurrency challenges |

**Rejected**: Python's async capabilities have improved, but Go is still better for high-throughput HTTP services.

### 3. Separate Python Service (Chosen)

| Pros | Cons |
|------|------|
| Best tool for each job | Increased operational complexity |
| Python's ML ecosystem | Inter-service communication latency |
| Independent scaling | Two codebases to maintain |
| Team can specialize | |

## Consequences

### Positive

- **Best-in-class libraries**: Access to Hugging Face, LangChain, sentence-transformers, etc.
- **Independent scaling**: AI service can scale based on GPU availability
- **Fault isolation**: AI failures don't crash the main API
- **Flexibility**: Easy to swap models without touching the Go backend

### Negative

- **Operational complexity**: Two services to deploy and monitor
- **Network latency**: gRPC calls add ~1-5ms overhead
- **Data serialization**: Protobuf encoding/decoding overhead
- **Debugging**: Cross-service tracing is more complex

### Neutral

- Need to maintain proto definitions in `go-backend/idl/`
- Redis queue bridges async processing between services

## Architecture

```
┌─────────────────┐     gRPC      ┌─────────────────┐
│   Go Backend    │ ─────────────▶│  Python AI      │
│   (HTTP API)    │               │  Service        │
└────────┬────────┘               └────────┬────────┘
         │                                 │
         │ Redis Queue                     │
         │ (asset_id)                      │
         └────────────┬────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Python Worker │
              │ (async tasks) │
              └───────────────┘
```

## Implementation Notes

- Python 3.11+ for performance improvements
- gRPC async server for concurrent request handling
- Separate worker process for queue consumption
- Loguru for structured logging

## Technology Choices

| Component | Library | Reason |
|-----------|---------|--------|
| gRPC Server | grpcio + grpcio-tools | Standard Python gRPC |
| LLM Client | langchain-openai | OpenAI-compatible API |
| Text Embeddings | sentence-transformers | BGE-M3 support |
| Image Embeddings | transformers | SigLIP support |
| Document Parsing | docling | PDF/DOCX support |

## Related

- [ADR-001: Use Go for Main Backend Service](001-go-backend.md)
- [ADR-003: Use gRPC for Inter-Service Communication](003-grpc-communication.md)
