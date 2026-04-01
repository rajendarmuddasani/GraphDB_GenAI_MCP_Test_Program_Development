# Getting Started

This guide sets up the repository for local exploration and validates the sample project before you wire in a live Neo4j instance.

## Prerequisites

- Python 3.9 or newer
- Neo4j 5.x, if you want to run connection checks or queries
- A shell with standard development tooling

## Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure Environment

```bash
cp configs/.env.example .env
```

Set the values that match your Neo4j environment.

## Run A Project Preflight Scan

The preflight command validates the input paths and summarizes the sample Java project without requiring a live database connection.

```bash
python src/neo4j_agent.py preflight \
    --version v1.0.0 \
    --project-path examples/sample_project \
    --build-xml-path examples/sample_project/build.xml
```

Expected output is JSON containing:

- discovered Java files,
- package count,
- build dependency names from `build.xml`,
- the exact paths that would be used for a fuller ingestion flow.

## Check Neo4j Connectivity

Once Neo4j is running, verify the connection:

```bash
python src/neo4j_agent.py health-check --env-file .env
```

## Execute A Cypher Query

```bash
python src/neo4j_agent.py query \
    --env-file .env \
    --cypher "MATCH (n) RETURN count(n) AS total"
```

## Explore The Included Assets

- `examples/sample_project` contains a compact Java, TOML, and Ant-based sample.
- `templates/` contains prompt templates for structured code generation flows.
- `examples/*.ipynb` contains notebook-based walkthroughs for interactive exploration.
- `docs/MCP_INTEGRATION.md` covers MCP setup details.

## Run Tests

```bash
pytest
```

## Seed the Graph (Optional)

If you want to populate Neo4j with the sample dataset used by the notebooks:

```bash
python scripts/seed_neo4j.py
```

This creates two versions of a Java test framework (v2.3.0 and v2.4.0) with classes, methods, inheritance, dependencies, imports, and documentation links.

## Cypher Query Reference

Once the database is seeded, try these queries in the Neo4j Browser (`http://localhost:7474`) or via the CLI.

### Browse All Classes

```cypher
MATCH (c:Class)
RETURN c.name AS ClassName, c.category AS Category, c.gitTag AS Version
ORDER BY c.name
```

### Inheritance Hierarchy

```cypher
MATCH path = (child:Class)-[:EXTENDS]->(parent:Class)
RETURN child.name AS Child, parent.name AS Parent
```

### Methods Defined by a Specific Class

```cypher
MATCH (c:Class {name: 'ExampleTestMethod'})-[:DEFINES_METHOD]->(m:Method)
RETURN m.name AS MethodName, m.visibility AS Visibility, m.returnType AS ReturnType
ORDER BY m.name
```

### Dependency Hot Spots

```cypher
MATCH (c:Class)-[:DEPENDS_ON]->(dep:ExternalDependency)
WITH c, count(dep) AS DepCount, collect(dep.name) AS Dependencies
RETURN c.name AS Class, DepCount, Dependencies
ORDER BY DepCount DESC
LIMIT 10
```

### Classes Using a Specific Dependency

```cypher
MATCH (c:Class)-[:DEPENDS_ON]->(dep:ExternalDependency)
WHERE dep.name CONTAINS 'core-runtime'
RETURN c.name AS Class, c.category AS Category
ORDER BY c.name
```

### Most-Extended Base Classes

```cypher
MATCH (child:Class)-[:EXTENDS]->(parent:Class)
WITH parent, count(child) AS ChildCount, collect(child.name) AS Children
WHERE ChildCount > 1
RETURN parent.name AS BaseClass, ChildCount, Children
ORDER BY ChildCount DESC
```

### Import Usage Frequency

```cypher
MATCH (c:Class)-[:IMPORTS]->(i:Import)
WITH i.path AS ImportPath, count(c) AS UsageCount
RETURN ImportPath, UsageCount
ORDER BY UsageCount DESC
LIMIT 10
```

### Documentation Coverage

```cypher
MATCH (c:Class)
OPTIONAL MATCH (md:MarkdownFile)-[:RESOLVES_TO]->(c)
WITH c, count(md) AS DocCount
RETURN
  count(c) AS TotalClasses,
  sum(CASE WHEN DocCount > 0 THEN 1 ELSE 0 END) AS DocumentedClasses,
  round(100.0 * sum(CASE WHEN DocCount > 0 THEN 1 ELSE 0 END) / count(c), 1) AS CoveragePercent
```

### Compare Versions

```cypher
MATCH (c:Class)
WHERE c.gitTag IN ['v2.3.0', 'v2.4.0']
WITH c.gitTag AS Version, count(c) AS ClassCount
RETURN Version, ClassCount
ORDER BY Version
```

### Classes Added in a New Version

```cypher
MATCH (c:Class {gitTag: 'v2.4.0'})
WHERE NOT EXISTS {
  MATCH (old:Class {gitTag: 'v2.3.0', qualifiedName: c.qualifiedName})
}
RETURN c.name AS NewClass, c.category AS Category
```

### Database Statistics

```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(*) AS Count
ORDER BY Count DESC
```

### Visual Graph Queries (Neo4j Browser)

These produce interactive graph visualizations when run in the Neo4j Browser:

```cypher
// Full inheritance tree (graph view)
MATCH path = (child:Class)-[:EXTENDS]->(parent:Class) RETURN path

// ExampleTestMethod neighborhood
MATCH (c:Class {name: 'ExampleTestMethod', gitTag: 'v2.3.0'})-[r]->(n) RETURN c, r, n

// Complete graph overview
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```

## Next Steps

1. Extend `src/neo4j_agent.py` with parser-backed extraction and Neo4j persistence.
2. Add your MCP server configuration from [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md).
3. Replace the sample project with a sanitized internal code sample when you are ready.
