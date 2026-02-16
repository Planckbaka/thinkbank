# ADR-001: Use Go for Main Backend Service

## Status

**Accepted**

## Context

ThinkBank requires a high-performance HTTP backend to handle:
- File upload and download operations
- REST API for asset management
- Integration with multiple data stores (PostgreSQL, MinIO, Redis)
- Potential for high concurrent request volume

We evaluated several options for the backend implementation language and framework.

## Decision

We will use **Go (Golang) with CloudWeGo Hertz** as the main backend service.

## Alternatives Considered

### 1. Node.js with Express/Fastify

| Pros | Cons |
|------|------|
| Large ecosystem | Single-threaded event loop |
| Fast development | Weaker type system (even with TypeScript) |
| JSON native | Higher memory usage |
| Team familiarity | Callback complexity |

### 2. Python with FastAPI

| Pros | Cons |
|------|------|
| Excellent for AI integration | Slower raw performance |
| Modern async support | GIL limitations |
| Automatic OpenAPI docs | Not ideal for CPU-intensive tasks |

### 3. Rust with Actix/Axum

| Pros | Cons |
|------|------|
| Best performance | Steep learning curve |
| Memory safety | Slower development velocity |
| Zero-cost abstractions | Smaller talent pool |

### 4. Go with Hertz (Chosen)

| Pros | Cons |
|------|------|
| Excellent performance | Verbose error handling |
| Built-in concurrency (goroutines) | Less syntactic sugar than Python |
| Strong typing | Smaller ecosystem than Node.js |
| Single binary deployment | |
| CloudWeGo ecosystem (from ByteDance) | |

## Consequences

### Positive

- **High performance**: Go's compiled nature and efficient runtime handle high concurrency well
- **Simple deployment**: Single binary with no runtime dependencies
- **Strong typing**: Catches errors at compile time
- **Goroutines**: Natural concurrency model for handling multiple simultaneous operations
- **CloudWeGo ecosystem**: Modern, high-performance libraries from ByteDance

### Negative

- **Learning curve**: Team members need Go proficiency
- **Verbosity**: More boilerplate than Python for some operations
- **Error handling**: Explicit error checking can be repetitive

### Neutral

- GORM for database operations (not as powerful as some ORMs, but sufficient)
- Need to maintain separate proto definitions for gRPC

## Implementation Notes

- Use Go 1.25+ for latest features
- Hertz for HTTP framework (CloudWeGo)
- GORM for PostgreSQL access
- google/uuid for UUID generation

## Related

- [ADR-002: Separate Python Service for AI/ML](002-python-ai-service.md)
- [ADR-003: Use gRPC for Inter-Service Communication](003-grpc-communication.md)
