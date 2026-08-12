# Repository Audit: Graph-Backed MCP Java Test Generation

## Audit Scope

- Base commit: `15a8fb63952f8c49eeb3201e0f29b0b7874bba6b`
- Public data rule: independently generated synthetic or licensed public material only
- Accepted policy: `strict_graph_v2`
- Canonical policy identity: recorded in `claims.json` and `task_evaluation.json`
- External services exercised locally: Neo4j Community 5.26.29

## Baseline Finding

The repository began as a tested starter, not an executable generation system. It provided:

- an Ant/TOML preflight scanner;
- a thin Neo4j driver wrapper and raw query CLI;
- fake-driver unit tests;
- MCP configuration guidance without an MCP server;
- unexecuted notebooks with default-password fallbacks;
- a hand-written Java example without the accepted validation or compilation loop;
- screenshots from an unrelated 11,378-node graph with visible local-path context.

The initial `ingest_project` path explicitly returned zero ingested classes, methods, relationships, documentation links, and execution time. No task-success, grounding, Java validation, live graph, MCP protocol, latency, error, or compile evidence existed.

## Claim Audit

| Original or implied claim | Baseline evidence | Classification before work | Resolution |
|---|---|---|---|
| Java files and Ant dependencies can be inventoried | `collect_project_snapshot` and tests | Measured | Retained as legacy preflight only |
| Java relationships are persisted in Neo4j | Design docs and manual seed script | Architecture | Replaced by immutable fixture materialization and live retrieval evidence |
| Graph context is exposed through MCP | YAML/JSON examples only | Unsupported | Implemented five official FastMCP stdio tools and protocol tests |
| Natural-language intent produces Java | Notebook template and checked-in example | Unsupported | Implemented three-form bounded grammar, graph citations, validation, and typed rejection |
| Generated source is valid | String checks only | Unsupported | Added Tree-sitter, contract, grounding, forbidden-API, and real compilation gates |
| Graph context improves generation | No candidate comparison | Unsupported | Measured four fixed policies; retained three rejected trials |
| Runtime is production-ready | No deployment or operations evidence | Unsupported | Removed; local runtime and CI architecture are stated precisely |

## Accepted Evidence Chain

| Surface | Executable source | Canonical artifact | Accepted result |
|---|---|---|---|
| Data contract | `build_evaluation_fixture.py` | `fixtures/evaluation_cases.json` | 96 cases; 32 per split; disjoint groups |
| Candidate selection | `evaluation.py` | `task_evaluation.json` | Only `strict_graph_v2` passed every validation gate |
| Confirmation | `evaluation.py` | `evaluation_trace.json` | 32/32 tasks; 24/24 generation; 8/8 rejection |
| Grounding | `workflow.py` | `task_evaluation.json` | 100% citation precision and required-symbol recall |
| Java safety | `workflow.py` | tests and case trace | Syntax, contract, source API, and path controls pass |
| Java compilation | `compile_generated.py` | `java_compile.json` | 8 source files compiled to 8 class files |
| Live graph | `graph_store.py`, `verify_neo4j.py` | `neo4j_integration.json` | Neo4j 5.26.29; 8 symbols; 12 methods |
| Official MCP | `server.py`, `benchmark_mcp.py` | `mcp_benchmark.json` | 120/120 expected outcomes; zero protocol errors |
| Claims/privacy | `validate_evidence.py` | `claims.json` | 14 public claims and 5 non-claim boundaries validated |

## Candidate Record

The protocol maximized validation task success among candidates passing every safety gate. Confirmation was not used for selection.

| Candidate | Validation task success | Safe rejection | Citation precision | Outcome |
|---|---:|---:|---:|---|
| `no_graph_v0` | 21.88% | 87.5% | 0% | Rejected for missing grounding |
| `lenient_repair_v1` | 75.0% | 0% | 100% | Rejected after eight unsafe false accepts |
| `strict_graph_v2` | 100% | 100% | 100% | Selected |
| `wide_context_v3` | 96.88% | 87.5% | 87.5% | Rejected for irrelevant context and one false accept |

## Data and Split Integrity

- Graph metadata, intents, and Java stubs are independently generated and labelled CC0-1.0.
- No internal source, identifiers, metrics, schemas, prompts, paths, screenshots, or data are used.
- Development, validation, and confirmation use different supported scenario families.
- Every request and case ID is unique.
- Confirmation is evaluated only for the selected candidate.
- No random model training occurs; `random_seed` is intentionally null.

## Security and Privacy Review

- Removed hard-coded/default-password notebook paths and the destructive legacy seeder.
- Replaced unsafe XML parsing with `defusedxml`.
- Parameterized all Neo4j search and materialization inputs.
- Removed raw Cypher from the MCP surface.
- Rejected embedded Neo4j URI credentials.
- Added path traversal, control character, identifier, source size, and forbidden Java API controls.
- Evidence validation rejects personal Windows user paths and the local temporary password marker.
- Runtime dependency audit reports no known vulnerabilities.
- Bandit reports zero medium/high findings; the remaining low findings are fixed-argument, no-shell compiler subprocess calls.

## Local Validation Envelope

- Python suite passes with the live Neo4j test skipped in ordinary offline runs.
- The opt-in live Neo4j adapter and Neo4j-backed MCP protocol tests pass separately.
- Strict Ruff passes across `src`, `tests`, and `scripts`.
- Evidence and privacy contract passes.
- Generated Java compiles locally with checksum-recorded Eclipse ECJ.
- Official MCP fixture smoke and 120-call live Neo4j benchmark pass.
- Compose configuration and GitHub Actions YAML parse successfully.

The available Docker daemon supports Windows containers, so the Linux image was not built locally. CI defines the non-root Linux build, UID assertion, and MCP-over-container smoke gate; that remains pending until publication approval and a remote workflow run.

## Removed Contradictory Material

- Three unexecuted notebooks using the older query/template path
- One stale generated Java example
- One destructive hard-coded Neo4j seeder
- Two unrelated graph screenshots containing unsupported node counts and local-path context
- Notebook-heavy and unused OpenAI, embedding, pandas, Git, TOML, and progress dependencies

## Audit Decision

The repository now supports a truthful public claim of a bounded, synthetic, graph-grounded MCP Java generation and validation workflow. It does not support claims of free-form GenAI reasoning, proprietary framework compatibility, production deployment, hardware control, or business impact.