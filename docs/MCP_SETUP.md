# MCP (Model Context Protocol) Setup Guide

## Overview

This guide explains how to integrate Neo4j with GitHub Copilot using Model Context Protocol (MCP), enabling AI-assisted code generation from the knowledge graph.

## Architecture

```
GitHub Copilot
    ↓ (MCP Request)
VS Code MCP Client
    ↓ (stdio)
GenAI Toolbox Server
    ↓ (Cypher Query)
Neo4j Database
    ↓ (JSON Response)
GitHub Copilot
```

## Prerequisites

1. **Go 1.25+**: Required to build GenAI Toolbox
2. **MinGW GCC**: C compiler for CGO compilation
3. **Oracle Instant Client**: Neo4j driver dependency
4. **Neo4j Desktop**: Local database (or remote Neo4j server)

## Step 1: Build GenAI Toolbox

```bash
# Clone GenAI Toolbox repository
git clone https://github.com/your-org/genai-toolbox.git
cd genai-toolbox

# Build the MCP server
go build -o toolbox.exe

# Verify build
./toolbox.exe --version
```

## Step 2: Configure MCP Tools

Create `neo4j_tools.yaml`:

```yaml
name: neo4j-testpilot
version: 1.0.0
description: "Neo4j knowledge graph tools for test code generation"

connection:
  uri: bolt://localhost:7687
  user: neo4j
  password: ${NEO4J_PASSWORD}

tools:
  - name: get_datas_from_particular_ingestion_version
    description: "Fetch classes and documentation for specific Git version"
    parameters:
      Ingestion_Version:
        type: string
        required: true
        description: "Git version tag (e.g., 'v1.0.0')"
        example: "v0.16.0"
    
    cypher: |
      MATCH (cls:Class)
      WHERE cls.gitTag = $Ingestion_Version
      OPTIONAL MATCH (cls)-[:DEFINES_METHOD]->(m:Method)
      OPTIONAL MATCH (md:MarkdownFile)-[:RESOLVES_TO]->(cls)
      RETURN cls, collect(DISTINCT m) as methods, collect(DISTINCT md) as docs

  - name: search_class_by_name
    description: "Search for classes across all versions"
    parameters:
      class_name:
        type: string
        required: true
        description: "Class name to search for"
    
    cypher: |
      MATCH (cls:Class)
      WHERE cls.name CONTAINS $class_name
      RETURN cls.name, cls.qualifiedName, cls.gitTag
      ORDER BY cls.name

  - name: find_class_dependencies
    description: "Find all dependencies for a specific class"
    parameters:
      class_name:
        type: string
        required: true
    
    cypher: |
      MATCH (cls:Class {name: $class_name})-[:DEPENDS_ON]->(dep)
      RETURN dep.name, dep.version

  - name: neo4j_execute_cypher
    description: "Execute custom Cypher query"
    parameters:
      cypher:
        type: string
        required: true
        description: "Cypher query to execute"
    
    handler: execute_raw_cypher
```

## Step 3: Configure VS Code MCP

Create `mcp.json` in VS Code settings directory:

**Windows:** `C:\Users\USERNAME\AppData\Roaming\Code\User\mcp.json`
**macOS:** `~/Library/Application Support/Code/User/mcp.json`
**Linux:** `~/.config/Code/User/mcp.json`

```json
{
  "mcpServers": {
    "neo4j-testpilot": {
      "command": "/absolute/path/to/genai-toolbox/toolbox.exe",
      "args": [
        "serve",
        "--config",
        "/absolute/path/to/neo4j_tools.yaml"
      ],
      "type": "stdio",
      "env": {
        "NEO4J_PASSWORD": "your_password_here"
      }
    }
  }
}
```

## Step 4: Restart VS Code

Close and reopen VS Code to load the MCP server.

## Step 5: Test MCP Integration

Open GitHub Copilot Chat and try:

```
@workspace Use get_datas_from_particular_ingestion_version to fetch classes for version v1.0.0
```

Expected output:
```json
{
  "classes": [
    {
      "name": "ExampleTestMethod",
      "qualifiedName": "testmethod.ExampleTestMethod",
      "category": "TestMethod"
    }
  ],
  "methods": [...],
  "documentation": [...]
}
```

## Step 6: Generate Code

Try this prompt:

```
Using v1.0.0 templates, generate a test method for ExampleModule based on Example.toml:

1. Read Example.toml configuration
2. Create test method class extending TlistBaseTm
3. Implement defineTestSequences() with dynamic test case loading
4. Follow v1.0.0 code standards (explicit imports, full Javadoc)
```

## Available MCP Tools

### 1. `get_datas_from_particular_ingestion_version`

**Purpose:** Fetch all classes, methods, and documentation for a specific Git version

**Parameters:**
- `Ingestion_Version` (string): Git tag (e.g., "v1.0.0")

**Example:**
```
Get all v1.0.0 templates using get_datas_from_particular_ingestion_version
```

### 2. `search_class_by_name`

**Purpose:** Search for classes across all versions

**Parameters:**
- `class_name` (string): Class name pattern

**Example:**
```
Search for "TestMethod" classes using search_class_by_name
```

### 3. `find_class_dependencies`

**Purpose:** Find JAR dependencies for a specific class

**Parameters:**
- `class_name` (string): Exact class name

**Example:**
```
Find dependencies for "ExampleTestMethod"
```

### 4. `neo4j_execute_cypher`

**Purpose:** Execute custom Cypher query

**Parameters:**
- `cypher` (string): Cypher query

**Example:**
```
Execute this Cypher query:
MATCH (c:Class)-[:EXTENDS]->(parent)
RETURN c.name, parent.name
LIMIT 10
```

## Troubleshooting

### Issue: MCP Server Not Starting

**Symptoms:**
- Copilot can't access Neo4j tools
- VS Code logs show "MCP connection failed"

**Solutions:**
1. Check toolbox.exe path in mcp.json
2. Verify neo4j_tools.yaml exists
3. Check Neo4j database is running
4. Review VS Code logs: View → Output → GitHub Copilot

### Issue: Authentication Failed

**Symptoms:**
- "Neo4j authentication failed" error

**Solutions:**
1. Verify NEO4J_PASSWORD in mcp.json env section
2. Test connection manually:
   ```bash
   cypher-shell -a bolt://localhost:7687 -u neo4j -p your_password
   ```

### Issue: Tool Results Empty

**Symptoms:**
- MCP tool executes but returns no data

**Solutions:**
1. Verify data exists in Neo4j:
   ```cypher
   MATCH (c:Class) RETURN count(c)
   ```
2. Check Ingestion_Version parameter matches Git tags
3. Review Cypher query in neo4j_tools.yaml

## Performance Tips

1. **Limit Query Results:** Add `LIMIT` to Cypher queries
2. **Index Properties:** Create indexes in Neo4j:
   ```cypher
   CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)
   CREATE INDEX class_gittag IF NOT EXISTS FOR (c:Class) ON (c.gitTag)
   ```
3. **Cache Results:** MCP server caches query results for 5 minutes

## Security Considerations

1. **Never commit mcp.json** to Git (contains passwords)
2. **Use environment variables** for sensitive data
3. **Restrict Neo4j access** to localhost only
4. **Enable Neo4j authentication** in production

## Next Steps

- See [DEVELOPER_GUIDE.md](../docs/DEVELOPER_GUIDE.md) for full ingestion workflow
- See [WALKTHROUGH.md](../WALKTHROUGH.md) for project overview in STAR format
- See [examples/](../examples/) for sample projects and generated code

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2026
