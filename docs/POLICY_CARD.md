# Generation Policy Card

## Selected Policy

`strict_graph_v2` is a deterministic graph-grounded Java template policy. Its identity is the candidate ID plus a SHA-256 over `workflow.py`, `graph_store.py`, and `server.py`.

## Selection Objective

Maximize validation task success among candidates that pass every safety gate:

- task success at least 95%;
- generated-source validation exactly 100%;
- safe rejection recall exactly 100%;
- citation precision exactly 100%;
- required-symbol recall exactly 100%;
- local in-process p95 no more than 25 ms.

Ties use lower validation p95 latency and then lexical candidate ID. Confirmation is not part of selection.

## Candidate Results

| Candidate | Primary failure |
|---|---|
| `no_graph_v0` | Imports cannot be grounded; generated-source pass rate is 0% |
| `lenient_repair_v1` | Silently generates defaults for all eight unsafe validation cases |
| `strict_graph_v2` | Only candidate passing every gate |
| `wide_context_v3` | Adds an irrelevant symbol and false-accepts unsupported version context |

## Confirmation

On 32 disjoint synthetic confirmation cases:

- 32/32 exact task outcomes;
- 24/24 supported generations passed validation;
- 8/8 unsafe or unsupported requests were rejected;
- 100% citation precision and required-symbol recall;
- zero observed errors inside the bounded grammar.

## Intended Use

- Demonstrating safe MCP tool design
- Regression testing graph-grounded generation
- Testing typed rejection and evidence contracts
- Serving as a clean public synthetic reference

## Prohibited Interpretation

Do not describe this policy as an LLM, a free-form coding agent, a production Java generator, or evidence of compatibility with proprietary test frameworks. It executes no generated source and controls no hardware.