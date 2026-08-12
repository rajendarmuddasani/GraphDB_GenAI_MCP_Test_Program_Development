# Metric Improvement Plan

## Current Accepted Baseline

`strict_graph_v2` is accepted for the bounded synthetic task because it alone passed every predeclared validation gate. Confirmation has no observed failures across 32 cases, so the next work must expand challenge diversity rather than tune on the same confirmation set.

## Completed Experiments

| Experiment | Hypothesis | Result | Decision |
|---|---|---|---|
| No graph context | Template structure may be sufficient | 0% generated-source validation and 0% citation precision | Reject |
| Lenient default repair | Repair may improve completion | 8/8 unsafe requests became false accepts | Reject |
| Strict exact graph | Minimal versioned context may satisfy quality and safety | Passed every validation gate | Select |
| Wide graph context | More context may improve robustness | Added an irrelevant symbol and false-accepted unsupported version | Reject |

## Promotion Experiments

### 1. Independent paraphrase challenge

- Build a new CC0 confirmation set with unseen sentence structures, punctuation, casing, and incomplete requests.
- Keep it disjoint from the three existing grammar templates.
- Primary metric: exact task success.
- Safety gates: 100% traversal/injection rejection and zero source returned for ambiguous requirements.
- Promotion rule: do not modify the current confirmation set after inspecting results.

### 2. Missing and conflicting graph context

- Remove required symbols, methods, or versions from independently versioned fixtures.
- Add contradictory method metadata and duplicate names.
- Metrics: missing-context recall, unsafe generation count, typed-error accuracy, and recovery latency.
- Gate: zero accepted source when any required symbol identity is unresolved.

### 3. Open-source Java framework integration

- Select a small permissively licensed public Java API.
- Build graph metadata from source with a structured parser rather than hand-authored fixture rows.
- Compile generated code against the actual public dependency.
- Metrics: compile pass rate, API-symbol precision/recall, deprecation errors, and reviewer correction count.
- Boundary: do not use proprietary framework source or identifiers.

### 4. Concurrent MCP and graph load

- Run fixed 1, 5, 10, and 20-client workloads against a containerized Neo4j backend.
- Record throughput, p50/p95/p99, timeout rate, protocol errors, CPU, memory, and graph connection-pool saturation.
- Add outage and recovery tests that restart Neo4j mid-workload.
- Gate: no incorrect source during partial graph availability.

### 5. Human review study

- Recruit independent reviewers for accepted and rejected synthetic tasks.
- Measure acceptance precision, correction rate, review time, disagreement, and unsafe-source recall.
- Preserve reviewer comments without personal or confidential data.
- Gate: no autonomous execution; reviewer approval remains mandatory.

### 6. Optional LLM challenger

- Add only after selecting a locally runnable or explicitly priced public model.
- Keep the deterministic strict policy as the baseline and safety envelope.
- Measure task success, grounding, hallucination taxonomy, prompt-injection behavior, latency, token use, and cost.
- Never describe deterministic evidence as LLM quality.

## Engineering Gates

- Pass the configured Linux container job and record the exact remote workflow run.
- Add a read-only health/metrics endpoint only if the deployment mode changes from stdio.
- Add signed release artifacts and SBOM after publication is approved.
- Raise coverage for `server.py` and the live Neo4j branches without replacing protocol tests with mocks.
- Add graph schema constraints and index migration evidence for larger fixtures.

## Claims That Remain Out of Scope

- Production SLO, availability, or scale
- Free-form language understanding
- Proprietary framework compatibility
- Hardware or test-equipment control
- Productivity, cost, yield, or test-time savings
- Production adoption

These remain unsupported until a new evidence protocol, accepted artifacts, and independent confirmation exist.