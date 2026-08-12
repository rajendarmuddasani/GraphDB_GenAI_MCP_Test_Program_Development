# MCP Integration

## Server Contract

The server uses the official MCP Python SDK and stdio transport. It deliberately omits raw Cypher, arbitrary file writes, shell execution, and generated-code execution.

## Client Configuration

### Offline fixture backend

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

### Neo4j backend

Add the following process environment variables through the client or operating system. Do not put real values in a committed JSON file.

```text
GRAPH_BACKEND=neo4j
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secret local value>
```

The graph must be seeded first with `python scripts/seed_graph.py`.

## Tools

### `get_fixture_metadata`

No parameters. Returns fixture ID, version, provenance, license, backend, and symbol count.

### `search_graph`

| Parameter | Type | Constraint |
|---|---|---|
| `query` | string | 1-80 characters |
| `version` | string | Must match the configured fixture version |
| `limit` | integer | 1-20 |

The Neo4j implementation uses a fixed query with `search_text`, `version`, `fixture_id`, and `limit` parameters.

### `generate_java_test`

Accepts structured `class_name`, `package_name`, `module_name`, `config_path`, and `version` fields. Unknown fields cannot enter this typed MCP surface.

### `generate_java_test_from_intent`

Accepts one `request` string. Supported forms are intentionally narrow:

```text
Generate a configuration-driven Java test method named CLASS in package PACKAGE for module MODULE using CONFIG.toml on framework VERSION.

Create CLASS as a Java test workflow in PACKAGE backed by module MODULE and config CONFIG.toml for VERSION.

For framework VERSION, generate class CLASS under package PACKAGE from module MODULE and config CONFIG.toml
```

This grammar is a safety and evaluation choice, not evidence of broad language understanding.

### `validate_java_source`

Accepts source plus the same structured identity fields. Source is limited to 20,000 characters and is parsed, checked, and discarded. The tool does not compile, write, or execute it.

## Response Semantics

Successful generation returns:

```json
{
  "status": "generated",
  "source": "...",
  "citations": [],
  "validation": {
    "valid": true,
    "syntax_valid": true,
    "contract_valid": true,
    "security_valid": true,
    "groundedness": 1.0
  },
  "error": null
}
```

Rejected input returns no source:

```json
{
  "status": "rejected",
  "source": null,
  "citations": [],
  "validation": null,
  "error": {
    "code": "unsafe_config_path",
    "message": "Config path must remain inside the project"
  }
}
```

Generated source that fails a downstream gate returns `validation_failed` and no source.

## Protocol Validation

`tests/test_mcp_protocol.py` launches the server as a subprocess, performs a real MCP initialization and tool-list exchange, calls valid generation, and verifies traversal rejection. `MCP_TEST_GRAPH_BACKEND=neo4j` runs the same protocol against the live graph service.

The local live benchmark executed 120 sequential calls through Neo4j with zero protocol errors. See `evidence/mcp_benchmark.json`; those local measurements are not a production SLO.