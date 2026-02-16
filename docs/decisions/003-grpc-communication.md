# ADR-003: Use gRPC for Inter-Service Communication

## Status

**Accepted**

## Context

ThinkBank's architecture involves communication between:
- Go backend (HTTP API)
- Python AI service (ML processing)

We needed a communication protocol that supports:
- Strong typing and schema enforcement
- Efficient binary serialization
- Streaming capabilities for real-time responses
- Code generation for multiple languages

## Decision

We will use **gRPC with Protocol Buffers** for all inter-service communication between Go and Python services.

## Alternatives Considered

### 1. REST/HTTP

| Pros | Cons |
|------|------|
| Simple to implement | Text-based (JSON) overhead |
| Universal support | No native streaming |
| Easy debugging | Schema drift issues |
| No code generation needed | Manual serialization |

### 2. GraphQL

| Pros | Cons |
|------|------|
| Flexible queries | Overkill for service-to-service |
| Strong typing | Complex setup |
| Single endpoint | No streaming (subscriptions are complex) |

### 3. Message Queue Only (Redis/RabbitMQ)

| Pros | Cons |
|------|------|
| Async decoupling | Not suitable for request/response |
| Retry built-in | Latency for real-time needs |
| Load balancing | No synchronous operations |

### 4. gRPC with Protobuf (Chosen)

| Pros | Cons |
|------|------|
| Binary protocol (efficient) | Learning curve |
| Strong typing via .proto | Harder to debug (binary) |
| Streaming support | Requires proto compilation |
| Multi-language codegen | HTTP/2 requirement |
| Schema evolution | |

## Consequences

### Positive

- **Type safety**: Proto definitions ensure contract compliance
- **Performance**: Binary serialization is 3-10x faster than JSON
- **Streaming**: Native support for server-streaming (ChatStream RPC)
- **Code generation**: Auto-generated client/server code in both Go and Python
- **Schema documentation**: Proto files serve as living documentation

### Negative

- **Tooling complexity**: Need `protoc` and plugins for code generation
- **Debugging difficulty**: Binary format harder to inspect
- **Browser incompatibility**: gRPC-Web or REST gateway needed for frontend
- **Versioning**: Proto changes require careful management

### Neutral

- Proto files live in `go-backend/idl/`
- Both Go and Python generate code from the same definitions

## Protocol Definition

```protobuf
service AiWorker {
  rpc ProcessAsset(AssetRequest) returns (ProcessStatus);
  rpc ChatStream(ChatRequest) returns (stream ChatResponse);
  rpc GetEmbedding(EmbeddingRequest) returns (EmbeddingResponse);
  rpc VectorSearch(SearchRequest) returns (SearchResponse);
}
```

## Streaming Use Case

The `ChatStream` RPC uses server-side streaming for real-time LLM responses:

```
Client                    Server
   │                        │
   │──ChatRequest──────────▶│
   │                        │
   │◀─ChatResponse(chunk)───│
   │◀─ChatResponse(chunk)───│
   │◀─ChatResponse(chunk)───│
   │◀─ChatResponse(final)───│
   │                        │
```

## Code Generation

### Go

```bash
protoc --go_out=. --go-grpc_out=. \
  go-backend/idl/ai_service.proto
```

### Python

```bash
python -m grpc_tools.protoc \
  -I. --python_out=. --grpc_python_out=. \
  go-backend/idl/ai_service.proto
```

## Error Handling

gRPC uses status codes that map to HTTP concepts:

| gRPC Code | HTTP Equivalent | Use Case |
|-----------|-----------------|----------|
| OK | 200 | Success |
| INVALID_ARGUMENT | 400 | Bad request |
| NOT_FOUND | 404 | Resource not found |
| INTERNAL | 500 | Server error |
| UNAVAILABLE | 503 | Service unavailable |

## Related

- [ADR-001: Use Go for Main Backend Service](001-go-backend.md)
- [ADR-002: Separate Python Service for AI/ML](002-python-ai-service.md)
