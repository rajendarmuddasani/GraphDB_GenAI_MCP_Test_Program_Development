# Deployment and Operations

## Supported Runtime Modes

| Mode | Graph source | Intended use |
|---|---|---|
| Local fixture | `fixtures/synthetic_graph.json` | Reproducible development and offline MCP smoke |
| Local Neo4j | Neo4j 5.26 seeded by `seed_graph.py` | Live graph integration and latency measurement |
| Linux container | Fixture by default; Neo4j through environment | CI smoke and portable stdio server |

No cloud or production deployment is included.

## Container

The multi-stage image uses pinned Chainguard Python build/runtime manifests, installs the locked runtime requirements into a virtual environment, and runs as UID/GID `65532`.

```bash
docker build -t graph-mcp-java:local .
python scripts/container_smoke.py docker run --rm -i graph-mcp-java:local
```

The smoke client initializes MCP, lists tools, runs a supported intent, and asserts full grounding.

## Neo4j Compose Service

The Compose service binds Bolt and HTTP to localhost, requires `NEO4J_PASSWORD`, persists graph data in a named volume, and uses an authenticated Cypher health check.

```bash
docker compose up -d neo4j
python scripts/wait_for_neo4j.py
python scripts/seed_graph.py
python scripts/verify_neo4j.py
```

Do not reuse the local Compose password in another environment.

## CI Gates

The workflow defines four jobs:

1. Python 3.10/3.12 tests, coverage, lint, fixture replay, claim validation, dependency audit, and Bandit.
2. JDK 21 compilation of accepted generated Java plus synthetic stubs.
3. Neo4j 5.26.29 service, fixture materialization, live retrieval, and Neo4j-backed MCP protocol.
4. Non-root Linux image build, UID assertion, and MCP-over-container stdio smoke.

These are configured gates. A local environment cannot claim the remote CI result until a pushed workflow run passes.

## Observability

The stdio server returns typed status, error code, citations, and validation details for each call. The benchmark records task outcomes, protocol errors, p50/p95/p99/max latency, startup latency, backend, tool list, and external model calls.

There is no production metrics exporter, distributed tracing, alerting, autoscaling, or on-call integration. Those remain promotion work.

## Recovery

- If Neo4j is unavailable, stop the Neo4j-backed process and restart with `GRAPH_BACKEND=fixture` for offline development.
- If the fixture hash conflicts with an existing graph identity, investigate and use a new version rather than overwriting evidence.
- If any source validator fails, retain the typed rejection; do not bypass the gate.
- To reset local Compose data intentionally, stop Compose and remove its named volume manually after confirming no evidence is needed.