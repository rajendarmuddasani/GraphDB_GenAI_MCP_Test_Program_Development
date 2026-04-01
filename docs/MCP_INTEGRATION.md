# MCP Integration Guide

This document outlines one practical way to connect a Neo4j-backed graph workflow to an MCP-capable client such as GitHub Copilot in VS Code.

## Integration Model

```text
Editor or MCP client
        |
        v
MCP server process
        |
        v
Curated graph tools
        |
        v
Neo4j database
```

The important design choice is to keep the MCP surface narrow. Expose a few reliable graph operations instead of a large number of loosely defined tools.

## Recommended Tool Categories

- project version lookup,
- class search,
- dependency discovery,
- controlled Cypher execution for diagnostics.

## Example Tool Configuration

Create a YAML file similar to the following and adapt it to your MCP server implementation:

```yaml
name: graph-code-intelligence
version: 1.0.0
description: "Neo4j-backed tools for Java test asset discovery"

connection:
  uri: bolt://localhost:7687
  user: neo4j
  password: ${NEO4J_PASSWORD}

tools:
  - name: get_project_version_context
    description: "Fetch classes and linked assets for a specific version"
    parameters:
      version:
        type: string
        required: true
    cypher: |
      MATCH (cls:Class)
      WHERE cls.gitTag = $version
      OPTIONAL MATCH (cls)-[:DEFINES_METHOD]->(m:Method)
      RETURN cls, collect(DISTINCT m) AS methods

  - name: search_class_by_name
    description: "Search for classes by partial name"
    parameters:
      class_name:
        type: string
        required: true
    cypher: |
      MATCH (cls:Class)
      WHERE cls.name CONTAINS $class_name
      RETURN cls.name, cls.qualifiedName, cls.gitTag
      ORDER BY cls.name

  - name: find_class_dependencies
    description: "Find dependencies for a specific class"
    parameters:
      class_name:
        type: string
        required: true
    cypher: |
      MATCH (cls:Class {name: $class_name})-[:DEPENDS_ON]->(dep)
      RETURN dep.name, dep.version

  - name: execute_diagnostic_cypher
    description: "Run a tightly controlled diagnostic Cypher query"
    parameters:
      cypher:
        type: string
        required: true
    handler: execute_raw_cypher
```

## VS Code Example

Configure your MCP client with a local server entry. The exact executable depends on the MCP server you choose to run.

```json
{
  "mcpServers": {
    "graph-code-intelligence": {
      "command": "/absolute/path/to/your-mcp-server",
      "args": [
        "serve",
        "--config",
        "/absolute/path/to/neo4j_tools.yaml"
      ],
      "type": "stdio",
      "env": {
        "NEO4J_PASSWORD": "replace-me"
      }
    }
  }
}
```

## Suggested Workflow

1. Run the preflight command in this repository to inventory the project inputs.
2. Load the relevant graph data into Neo4j using your ingestion pipeline.
3. Start the MCP server with a small, curated tool set.
4. Ask the editor to retrieve graph context before generating or modifying code.

## Validation Prompts

Once the MCP server is available, try targeted prompts such as:

```text
Use search_class_by_name to find classes related to ExampleTestMethod.
```

```text
Use find_class_dependencies to list the dependencies for ExampleTestMethod.
```

## Operational Notes

- Prefer version-scoped tools over open-ended graph reads.
- Keep Cypher handlers auditable and intentionally limited.
- Avoid embedding credentials directly in committed config files.
- Treat MCP as a context bridge, not as a replacement for ingestion discipline.

## Troubleshooting

### Authentication failures

If the MCP server cannot authenticate to Neo4j, verify that the password is being passed through the local MCP configuration and test the same credentials outside the editor first.

### Empty tool responses

If a tool runs but returns no rows, confirm that the expected graph data is present and that the query parameters match the version or class names stored in Neo4j.

## Security Notes

- Keep local MCP client configuration files out of version control when they contain secrets.
- Prefer environment variables for database credentials.
- Restrict any raw Cypher execution tool to trusted local workflows.

## Next Steps

- See [README.md](../README.md) for the project overview.
- See [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the repository design.
- See [GETTING_STARTED.md](../GETTING_STARTED.md) for local setup and command-line usage.
