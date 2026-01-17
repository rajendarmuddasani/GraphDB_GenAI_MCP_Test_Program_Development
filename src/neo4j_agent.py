"""
Neo4j Agent: Main interface for ingesting Java projects into Neo4j knowledge graph

This module provides the core agent class for:
- Connecting to Neo4j database
- Ingesting Java projects (8-phase process)
- Querying the knowledge graph
- Version comparison and semantic analysis

Example usage:
    from neo4j_agent import Neo4jAgent
    
    agent = Neo4jAgent(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password"
    )
    
    # Ingest a Java project
    report = agent.ingest_project(
        version="v1.0.0",
        project_path="./examples/sample_project",
        build_xml_path="./examples/sample_project/build.xml"
    )
    
    print(f"Ingested {report['classes_ingested']} classes")
"""

from neo4j import GraphDatabase
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Neo4jAgent:
    """
    Main agent class for Neo4j knowledge graph ingestion and querying.
    
    Attributes:
        uri (str): Neo4j database connection URI
        user (str): Neo4j username
        password (str): Neo4j password
        driver: Neo4j driver instance
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j agent with database connection credentials.
        
        Args:
            uri: Neo4j bolt URI (e.g., 'bolt://localhost:7687')
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Neo4j agent initialized: {uri}")
    
    def close(self):
        """Close Neo4j database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def ingest_project(
        self, 
        version: str, 
        project_path: Path, 
        build_xml_path: str
    ) -> Dict:
        """
        Ingest a Java project into Neo4j knowledge graph.
        
        This method executes the 8-phase ingestion process:
        1. Project Structure
        2. Class Ingestion
        3. Members Extraction
        4. Dependency Graph
        5. Import Resolution
        6. Git Versioning
        7. Semantic Changes (for 2nd+ versions)
        8. Markdown Linking
        
        Args:
            version: Git version tag (e.g., 'v1.0.0')
            project_path: Path to Java project root directory
            build_xml_path: Path to build.xml file
            
        Returns:
            Dict containing ingestion report:
                - classes_ingested: Number of classes parsed
                - methods_extracted: Number of methods found
                - dependencies_mapped: Number of JAR dependencies
                - documentation_links: Number of markdown → class links
                - execution_time: Total ingestion time in seconds
        
        Example:
            >>> agent = Neo4jAgent('bolt://localhost:7687', 'neo4j', 'password')
            >>> report = agent.ingest_project('v1.0.0', Path('./project'), './build.xml')
            >>> print(f"Ingested {report['classes_ingested']} classes")
        """
        # TODO: Implement 8-phase ingestion
        # This is a placeholder showing the expected structure
        
        logger.info(f"Starting ingestion for version {version}")
        
        report = {
            'version': version,
            'classes_ingested': 0,
            'methods_extracted': 0,
            'dependencies_mapped': 0,
            'documentation_links': 0,
            'execution_time': 0.0
        }
        
        # Phase 1-8 implementation would go here
        # See DEVELOPER_GUIDE.md for full implementation details
        
        logger.info(f"Ingestion completed: {report}")
        return report
    
    def query(self, cypher: str, parameters: Optional[Dict] = None) -> list:
        """
        Execute a Cypher query against the Neo4j knowledge graph.
        
        Args:
            cypher: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of query results
            
        Example:
            >>> agent.query("MATCH (c:Class) RETURN c.name LIMIT 10")
        """
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]
    
    def clear_database(self):
        """
        Clear all nodes and relationships from the database.
        
        WARNING: This deletes all data. Use with caution!
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Database cleared")


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = Neo4jAgent(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    try:
        # Ingest example project
        report = agent.ingest_project(
            version="v1.0.0",
            project_path=Path("./examples/sample_project"),
            build_xml_path="./examples/sample_project/build.xml"
        )
        
        print(f"Ingestion Report:")
        print(f"  Classes: {report['classes_ingested']}")
        print(f"  Methods: {report['methods_extracted']}")
        print(f"  Dependencies: {report['dependencies_mapped']}")
        
    finally:
        agent.close()
