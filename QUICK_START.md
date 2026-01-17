# Quick Start Guide

Get Neo4j TestPilot running in 5 minutes!

## Prerequisites

- Python 3.9+
- Neo4j Desktop installed and running
- Git (for cloning)

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/neo4j-testpilot-public.git
cd neo4j-testpilot-public
```

## Step 2: Setup Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Neo4j

```bash
# Copy environment template
cp configs/.env.example .env

# Edit .env with your credentials
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

## Step 4: Start Neo4j

1. Open Neo4j Desktop
2. Start your database
3. Note the bolt URI (default: bolt://localhost:7687)

## Step 5: Run Example Ingestion

```python
from src.neo4j_agent import Neo4jAgent
from pathlib import Path

# Initialize agent
agent = Neo4jAgent(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_password"
)

# Ingest example project
report = agent.ingest_project(
    version="v1.0.0",
    project_path=Path("./examples/sample_project"),
    build_xml_path="./examples/sample_project/build.xml"
)

print(f"Success! Ingested {report['classes_ingested']} classes")
```

## Step 6: Query the Graph

Open Neo4j Browser: http://localhost:7474

Try these queries:

```cypher
// View all classes
MATCH (c:Class) RETURN c LIMIT 10

// Find inheritance hierarchy
MATCH path = (child:Class)-[:EXTENDS]->(parent:Class)
RETURN path

// Count nodes by type
MATCH (n)
RETURN labels(n) AS NodeType, count(*) AS Count
ORDER BY Count DESC
```

## Step 7: Setup MCP (Optional)

See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for full MCP integration guide.

Quick version:
1. Build GenAI Toolbox
2. Configure `mcp.json` in VS Code
3. Restart VS Code
4. Use GitHub Copilot to query Neo4j

## Next Steps

- Read [WALKTHROUGH.md](WALKTHROUGH.md) for project overview (STAR format)
- See [examples/](examples/) for more sample projects
- Explore [templates/](templates/) for code generation prompts

## Troubleshooting

**Issue:** Neo4j connection refused

**Solution:** Ensure Neo4j Desktop database is started (green ▶️ button)

**Issue:** Import errors

**Solution:** Activate virtual environment and reinstall requirements:
```bash
pip install -r requirements.txt
```

**Issue:** Permission denied on .venv

**Solution:** Run with elevated permissions or use user-local installation:
```bash
pip install --user -r requirements.txt
```

## Support

- GitHub Issues: [Create an issue](https://github.com/yourusername/neo4j-testpilot-public/issues)
- Documentation: [README.md](README.md)
- Examples: [examples/](examples/)

---

**Ready to go!** 🚀
