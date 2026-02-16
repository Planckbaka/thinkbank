# ThinkBank Documentation

Welcome to the ThinkBank documentation hub. This folder contains comprehensive documentation following the **Docs-as-Code** philosophy.

## Quick Navigation

| Category | Description | Link |
|----------|-------------|------|
| **API** | REST API specification & error codes | [api/](api/) |
| **Architecture** | System design, diagrams & tech stack | [architecture/](architecture/) |
| **Data** | Database schema, ER diagrams & data dictionary | [data/](data/) |
| **Decisions (ADR)** | Architecture Decision Records | [decisions/](decisions/) |
| **Operations** | Deployment, configuration & troubleshooting | [operations/](operations/) |
| **Development** | Getting started & contributing guides | [development/](development/) |

## Documentation Structure

```
docs/
├── api/                    # API Documentation
│   ├── openapi.yaml        # OpenAPI 3.0 Specification
│   └── error-codes.md      # Error codes reference
├── architecture/           # Architecture Documentation
│   ├── system-overview.md  # C4 diagrams & components
│   ├── sequence-diagrams.md # Workflow diagrams
│   └── tech-stack.md       # Technology decisions
├── data/                   # Data Documentation
│   ├── er-diagram.md       # Entity-Relationship diagram
│   └── data-dictionary.md  # Field definitions
├── decisions/              # Architecture Decision Records
│   ├── README.md           # ADR index
│   ├── 001-*.md            # Decision records
│   └── template.md         # ADR template
├── operations/             # Operations Documentation
│   ├── deployment.md       # Deployment guides
│   ├── configuration.md    # Configuration reference
│   ├── troubleshooting.md  # Common issues
│   └── monitoring.md       # Health & logging
└── development/            # Development Documentation
    ├── getting-started.md  # Setup guide
    ├── contributing.md     # Contribution guidelines
    └── testing.md          # Testing strategy
```

## For New Developers

1. Start with [development/getting-started.md](development/getting-started.md) to set up your environment
2. Read [architecture/system-overview.md](architecture/system-overview.md) to understand the system
3. Check [api/openapi.yaml](api/openapi.yaml) for API specifications
4. Review [decisions/](decisions/) to understand key architectural choices

## For DevOps / SRE

1. [operations/deployment.md](operations/deployment.md) - Deployment procedures
2. [operations/configuration.md](operations/configuration.md) - Environment variables
3. [operations/troubleshooting.md](operations/troubleshooting.md) - Common issues

## Documentation Maintenance

### When to Update Docs

- **API changes**: Update `api/openapi.yaml` before merging code changes
- **New features**: Update relevant architecture/sequence diagrams
- **Database changes**: Update `data/` documentation
- **Tech decisions**: Create new ADR in `decisions/`

### Docs-as-Code Principles

1. Documentation lives in the same repository as code
2. Changes go through the same PR review process
3. Use Mermaid for diagrams (renders natively in GitHub/VSCode)
4. Keep documentation close to the truth (code)

### Diagram Tools

- **Mermaid**: For flowcharts, sequence diagrams, ER diagrams
- **VSCode Extension**: "Markdown Preview Mermaid Support"
- **Online Editor**: [mermaid.live](https://mermaid.live/)

## Contributing to Documentation

See [development/contributing.md](development/contributing.md) for guidelines on:
- Documentation style guide
- PR requirements
- Review process
