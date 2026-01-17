# Neo4j TestPilot: AI-Assisted Test Code Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j 5.0+](https://img.shields.io/badge/neo4j-5.0+-green.svg)](https://neo4j.com/)

> **Transform legacy semiconductor test codebases into AI-queryable knowledge graphs for automated test generation**

## 🎯 Overview

Neo4j TestPilot is an intelligent code generation system that ingests Java test programs into a Neo4j knowledge graph, enabling AI-assisted test method generation through Model Context Protocol (MCP) integration with GitHub Copilot.

### Key Features

- 📊 **Knowledge Graph Ingestion**: Parse 481+ Java classes with full dependency tracking
- 🔍 **Version Comparison**: Detect semantic changes between code versions
- 📚 **Documentation Linking**: Automatically link markdown docs to code
- 🤖 **AI Code Generation**: Generate production-ready test methods via MCP
- 🚀 **100% Parser Coverage**: Tree-sitter based Java parsing
- 🔗 **Git Integration**: Track code changes across commits/tags/branches

## 🏗️ Architecture

```
┌─────────────────────┐
│  Java Test Program  │
│   (481 classes)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  8-Phase Ingestion  │
│  ├─ Project Struct  │
│  ├─ Class Parsing   │
│  ├─ Members Extract │
│  ├─ Dependencies    │
│  ├─ Import Resolve  │
│  ├─ Git Versioning  │
│  ├─ Semantic Changes│
│  └─ Markdown Linking│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Neo4j Database    │
│  9 Node Types       │
│  9 Relationships    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   MCP Integration   │
│  (GenAI Toolbox)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GitHub Copilot     │
│  Code Generation    │
└─────────────────────┘
```

## 📊 Neo4j Graph Schema

### Node Types (9)

```cypher
(:Project)              # Root project node
(:Package)              # Java package hierarchy
(:Class)                # Java classes (481 in v0.15.2)
(:Method)               # Methods with signatures
(:Field)                # Class fields with types
(:Import)               # Import statements
(:ExternalDependency)   # JAR dependencies (44 detected)
(:GitVersion)           # Git commit/tag tracking
(:MarkdownFile)         # Documentation files
```

### Relationships (9)

```cypher
(:Project)-[:CONTAINS_PACKAGE]->(:Package)
(:Package)-[:CONTAINS_CLASS]->(:Class)
(:Class)-[:DEFINES_METHOD]->(:Method)
(:Class)-[:DEFINES_FIELD]->(:Field)
(:Class)-[:IMPORTS]->(:Import)
(:Class)-[:DEPENDS_ON]->(:ExternalDependency)
(:Class)-[:EXTENDS]->(:Class)
(:GitVersion)-[:DESCRIBES]->(:Project)
(:MarkdownFile)-[:DOCUMENTS_VERSION]->(:GitVersion)
(:MarkdownFile)-[:RESOLVES_TO]->(:Class)
```

### Example Graph Visualization

**Neo4j Graph Schema:**

![Neo4j Graph Schema](assets/neo4j-graph-schema.png)

*Figure 1: Complete Neo4j graph schema showing 9 node types and their relationships. The graph captures Java class hierarchy, dependencies, Git versioning, and documentation links.*

**Graph Query Visualization:**

![Neo4j Graph Query Result](assets/neo4j-graph-visualization.png)

*Figure 2: Example query result showing class inheritance hierarchy with EXTENDS relationships. This visual representation helps understand complex code dependencies at a glance.*

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.9+
python --version

# Neo4j Desktop or Server 5.0+
# Download from: https://neo4j.com/download/

# Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/neo4j-testpilot-public.git
cd neo4j-testpilot-public

# Install dependencies
pip install -r requirements.txt

# Configure Neo4j connection
cp configs/.env.example .env
# Edit .env with your Neo4j credentials
```

### Configuration

**`.env` file:**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Optional: Remote Neo4j server
NEO4J_URI_REMOTE=bolt://your-server:7687
NEO4J_USER_REMOTE=admin
NEO4J_PASSWORD_REMOTE=remote_password
```

### Usage

#### 1. Ingest Java Project

```python
from src.neo4j_agent import Neo4jAgent

# Initialize agent
agent = Neo4jAgent(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_password"
)

# Ingest project (v1.0.0)
ingestion_report = agent.ingest_project(
    version="v1.0.0",
    project_path="./examples/sample_project",
    build_xml_path="./examples/sample_project/build.xml"
)

print(f"Ingested {ingestion_report['classes_ingested']} classes")
```

#### 2. Query Neo4j Knowledge Graph

```cypher
// Find all classes in a package
MATCH (pkg:Package {name: "testmethod"})-[:CONTAINS_CLASS]->(cls:Class)
RETURN cls.name, cls.category

// Find class dependencies
MATCH (cls:Class {name: "GenericTestMethod"})-[:DEPENDS_ON]->(dep)
RETURN dep.name AS Dependency

// Find inheritance hierarchy
MATCH path = (child:Class)-[:EXTENDS*1..3]->(parent:Class)
RETURN path LIMIT 10
```

#### 3. Generate Code with MCP

```
User: Using v1.0.0 templates, generate a GenericTestMethod for the ExampleModule based on Example.toml

GitHub Copilot (via MCP):
1. Queries Neo4j for v1.0.0 templates
2. Reads Example.toml configuration
3. Generates production-ready Java code
```

## 📁 Project Structure

```
neo4j-testpilot-public/
├── README.md                   # This file
├── WALKTHROUGH.md              # STAR method interview guide
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── configs/
│   ├── .env.example            # Environment template
│   ├── mcp_config.json         # MCP server configuration
│   └── neo4j_tools.yaml        # Neo4j MCP tools definition
│
├── docs/
│   ├── DEVELOPER_GUIDE.md      # Complete technical guide
│   ├── MCP_SETUP.md            # MCP integration guide
│   ├── INGESTION_GUIDE.md      # Step-by-step ingestion
│   └── QUERY_EXAMPLES.md       # Neo4j query patterns
│
├── src/
│   ├── neo4j_agent.py          # Main agent class
│   ├── code_ingester.py        # Java parsing & ingestion
│   ├── git_manager.py          # Git version tracking
│   ├── semantic_analyzer.py    # Version comparison
│   └── markdown_linker.py      # Documentation linking
│
├── templates/
│   ├── GenericTestMethod.prompt.md  # Test method template
│   ├── AnalogTestCase.prompt.md     # Analog measurement template
│   └── FunctionalTest.prompt.md     # Functional test template
│
├── examples/
│   ├── sample_project/         # Dummy Java project
│   │   ├── src/
│   │   │   └── testmethod/
│   │   │       └── ExampleTest.java
│   │   ├── build.xml
│   │   └── Example.toml
│   ├── generated_code/         # Example generated files
│   │   ├── ExampleTestMethod.java
│   │   └── GENERATION_SUMMARY.md
│   └── queries/
│       └── common_queries.cypher  # Useful Neo4j queries
│
└── tests/
    ├── test_ingestion.py       # Unit tests
    └── test_queries.py         # Query validation
```

## 🎓 Use Cases

### 1. Code Generation

**Problem:** Manual test method creation is time-consuming and error-prone

**Solution:** Query Neo4j for templates + TOML config → Generate production-ready code

**Example:**
```
Input: GenericTestMethod.prompt.md + Example.toml
Output: ExampleTestMethod.java (148 lines, fully documented)
```

### 2. Version Comparison

**Problem:** Track breaking changes between code versions

**Solution:** Semantic analysis detects method signature changes, import removals

**Example:**
```json
{
  "file": "DcDeltaMeasurementDh.java",
  "removed_methods": ["processAndLogData(IBrickResult)"],
  "modified_methods": ["processAndLogData(IDcResult)"]
}
```

### 3. Documentation Maintenance

**Problem:** Keep documentation synchronized with code

**Solution:** Automatic markdown → code linking via RESOLVES_TO relationships

**Example:**
```cypher
(:MarkdownFile {path: "GenericTestMethod.md"})
  -[:RESOLVES_TO]->
(:Class {name: "GenericTestMethod"})
```

## 📈 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Classes Ingested** | 481 | First version (v0.15.2) |
| **JAR Dependencies** | 44 | External libraries detected |
| **Ingestion Time (First)** | ~5 min | INSERT operations |
| **Ingestion Time (Second)** | ~34 min | MERGE + semantic analysis |
| **Parser Coverage** | 100% | Tree-sitter Java parser |
| **Documentation Links** | 210 | Markdown → Class relationships |

## 🔧 MCP Integration

### Setup

1. **Install Prerequisites:**
   - Go 1.25+
   - MinGW GCC (for CGO)
   - Oracle Instant Client (Neo4j driver dependency)

2. **Build GenAI Toolbox:**
   ```bash
   cd genai-toolbox
   go build -o toolbox.exe
   ```

3. **Configure VS Code MCP:**
   ```json
   {
     "mcpServers": {
       "toolbox": {
         "command": "J:/path/to/genai-toolbox/toolbox.exe",
         "args": ["serve", "--config", "configs/neo4j_tools.yaml"],
         "type": "stdio"
       }
     }
   }
   ```

### Available MCP Tools

- `get_datas_from_particular_ingestion_version` - Fetch version-specific templates
- `search_class_by_name` - Search classes across all versions
- `neo4j_execute_cypher` - Execute custom Cypher queries

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- **Neo4j** - Graph database platform
- **Tree-sitter** - Parser framework
- **GitHub Copilot** - AI code generation
- **Model Context Protocol** - LLM integration standard

## 📞 Contact

For questions or support:
- Create an [Issue](https://github.com/yourusername/neo4j-testpilot-public/issues)
- Email: your.email@example.com

---

**Made with ❤️ for the semiconductor testing community**
