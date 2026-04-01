# Architecture Overview

This repository is organized around a simple but extensible workflow for graph-backed developer tooling.

## Core Components

### Python entry point

`src/neo4j_agent.py` provides:

- environment-based Neo4j configuration,
- project preflight scanning,
- connection health checks,
- Cypher query execution,
- a small command-line interface for local usage.

### Sample assets

`examples/sample_project` includes a compact Java test asset, TOML configuration, and Ant build file. These files are intentionally small so the repository remains portable while still demonstrating the structure of a real workflow.

### Prompt templates

`templates/` stores prompt assets that can be paired with graph lookups and editor workflows.

### Notebook examples

The notebooks in `examples/` are optional exploration assets for local experimentation and explanation.

## Extension Path

The cleanest way to expand this project is:

1. parse Java files with a structured parser such as Tree-sitter,
2. materialize classes, methods, fields, and dependencies into Neo4j,
3. expose a small MCP toolset on top of the graph,
4. use prompt templates to drive context-aware generation.

## Design Constraints

- keep the repository publishable,
- separate reusable code from private operational notes,
- prefer honest scaffolding over inflated claims,
- make local validation possible even without a live graph database.