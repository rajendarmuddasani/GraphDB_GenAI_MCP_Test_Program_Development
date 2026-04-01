# Security Policy

## Supported Scope

This repository is intended for publishable sample code and reference workflows.

Do not commit:

- live credentials,
- customer or employer source code,
- internal infrastructure details,
- data sets that are not approved for public distribution.

## Reporting

If you discover a security issue in the code that is published here, report it privately to the maintainer before opening a public issue.

## Hardening Notes

- keep Neo4j credentials in environment variables,
- keep MCP server configurations local when they contain secrets,
- avoid broad raw-query handlers unless you trust the client and access path.