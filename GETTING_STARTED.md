# Getting Started

This guide runs the accepted bounded intent-to-graph-to-Java workflow. The offline fixture path is the fastest start; Neo4j is optional but required to reproduce the live GraphDB evidence.

## Prerequisites

- Python 3.10 or 3.12
- Docker with Linux containers for the Compose and image gates, or a local Neo4j 5.26 instance
- JDK 21 for the `javac` compile gate

## Install

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
```

### Linux or macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
```

## Run the Offline MCP Path

The default backend reads the versioned CC0 JSON fixture. It does not need credentials or network access.

```bash
python scripts/container_smoke.py python -m graph_mcp.server
```

Expected result:

```json
{
  "status": "passed",
  "tool_count": 5,
  "groundedness": 1.0
}
```

To start the stdio server for an MCP client:

```bash
python -m graph_mcp.server
```

## Configure an MCP Client

Use an absolute path to the virtual-environment Python executable and set the repository as the working directory:

```json
{
  "servers": {
    "synthetic-java-test-generator": {
      "type": "stdio",
      "command": "ABSOLUTE_PATH_TO_PYTHON",
      "args": ["-m", "graph_mcp.server"],
      "cwd": "ABSOLUTE_PATH_TO_REPOSITORY",
      "env": {
        "GRAPH_BACKEND": "fixture"
      }
    }
  }
}
```

The client can call `get_fixture_metadata`, `search_graph`, `generate_java_test`, `generate_java_test_from_intent`, and `validate_java_source`.

## Try a Supported Intent

Call `generate_java_test_from_intent` with:

```text
Create VoltageMarginWorkflow as a Java test workflow in generated.tests backed by module voltage_margin and config testtables/VoltageMargin.toml for v1.0.0.
```

Requests outside the three documented grammar forms return `unrecognized_intent`. Traversal such as `../private.toml` returns `unsafe_config_path` before generation.

## Run with Live Neo4j

Set a local password without committing it:

```powershell
$env:NEO4J_PASSWORD = Read-Host -AsSecureString
```

For Compose, expose the password as a process environment variable in your shell, then start the service:

```bash
docker compose up -d neo4j
```

Set the runtime connection variables:

```text
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<local value>
```

Seed and verify the immutable fixture:

```bash
python scripts/wait_for_neo4j.py
python scripts/seed_graph.py
python scripts/verify_neo4j.py
```

Run MCP against Neo4j:

```bash
GRAPH_BACKEND=neo4j python -m graph_mcp.server
```

On PowerShell:

```powershell
$env:GRAPH_BACKEND = "neo4j"
python -m graph_mcp.server
```

## Reproduce the Candidate Study

The benchmark is deterministic except for measured latency:

```bash
python scripts/build_evaluation_fixture.py
python scripts/evaluate_workflow.py
python scripts/validate_evidence.py
```

The evaluator selects on validation only and evaluates confirmation only for `strict_graph_v2`. It records rejected candidates and all case-level outcomes.

## Compile Accepted Java

With JDK 21 on `PATH`:

```bash
python scripts/compile_generated.py --require-compiler
```

The harness compiles one accepted generated class plus seven CC0 synthetic framework stubs in a temporary directory and records no source outside the repository.

## Test and Security Gates

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=75
ruff check src tests scripts
pip-audit -r requirements.txt --progress-spinner off
bandit -r src scripts -q -ll
```

The live graph test is opt-in:

```bash
RUN_NEO4J_INTEGRATION=1 pytest tests/test_neo4j_live.py -q
```

The CI workflow additionally compiles Java with Temurin 21, runs Neo4j 5.26.29 as a service, exercises MCP against that live backend, builds the non-root image, and calls MCP over container stdio.

## Legacy Preflight Sample

`examples/sample_project` remains only for the earlier Ant/TOML preflight scanner:

```bash
python src/neo4j_agent.py preflight --version v1.0.0 --project-path examples/sample_project --build-xml-path examples/sample_project/build.xml
```

It is not the accepted generation benchmark and should not be used as evidence for the MCP workflow.