"""Wait for the configured Neo4j service to accept Bolt connections."""

from __future__ import annotations

import os
import sys
from time import monotonic, sleep

from neo4j import GraphDatabase


def main() -> int:
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    deadline = monotonic() + 90
    last_error = "not attempted"
    while monotonic() < deadline:
        try:
            with GraphDatabase.driver(uri, auth=auth) as driver:
                driver.verify_connectivity()
            print("Neo4j is ready")
            return 0
        except Exception as exc:  # startup can fail at several socket/auth layers
            last_error = f"{type(exc).__name__}: {exc}"
            sleep(1)
    print(f"Neo4j did not become ready: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
