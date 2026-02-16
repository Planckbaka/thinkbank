# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records for ThinkBank.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences. ADRs help teams:

- **Remember why** a decision was made
- **Avoid re-litigating** the same decisions
- **Onboard new team members** faster
- **Track the evolution** of the architecture

## Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [001](001-go-backend.md) | Use Go for Main Backend Service | Accepted | 2024-01 |
| [002](002-python-ai-service.md) | Separate Python Service for AI/ML | Accepted | 2024-01 |
| [003](003-grpc-communication.md) | Use gRPC for Inter-Service Communication | Accepted | 2024-01 |
| [004](004-vector-database.md) | PostgreSQL with pgvector for Vector Storage | Accepted | 2024-01 |

## ADR Status

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet approved |
| **Accepted** | Approved and in effect |
| **Deprecated** | Replaced by a newer ADR |
| **Superseded** | Replaced; link to new ADR |

## Creating a New ADR

1. Copy [template.md](template.md) to a new file with the next number
2. Fill in all sections
3. Submit for review via pull request
4. Update this index after merge

### Naming Convention

```
NNN-short-title.md
```

- `NNN`: Three-digit sequential number (001, 002, etc.)
- `short-title`: Kebab-case title summarizing the decision

### Example

```
005-add-authentication.md
006-switch-to-graphql.md
```

## Template

See [template.md](template.md) for the standard ADR format.

## References

- [Documenting Architecture Decisions - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
