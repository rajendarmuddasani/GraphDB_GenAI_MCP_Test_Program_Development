# Security Policy

## Supported Scope

Security fixes target the current default branch. This public repository contains only independently generated synthetic fixtures; do not submit employer, customer, product, hardware, test-program, infrastructure, or credential material.

## Implemented Controls

- MCP exposes five bounded tools and no shell, raw Cypher, source-write, or source-execution tool.
- Intent fields use strict length, identifier, package, version, and relative TOML path checks.
- Generated Java is parsed and checked for framework contract, graph grounding, and forbidden process, filesystem, network, native, and exit APIs.
- Neo4j uses fixed parameterized Cypher and rejects credentials embedded in URIs.
- Fixture identities are SHA-256 bound and cannot be overwritten with different content.
- XML preflight parsing uses `defusedxml`.
- The Linux image runs as a non-root user.
- CI runs dependency, source-security, evidence/privacy, live graph, compile, and container gates.

## Operational Boundary

Generated source is returned for review but is never written, compiled, or executed by the MCP server. The separate compile harness uses fixed local compiler commands, no shell expansion, temporary source paths, and synthetic stubs.

The repository does not claim sandboxing for arbitrary Java, multi-tenant isolation, production authentication, production secret management, or protection against every prompt or graph poisoning strategy.

## Secrets

- Keep `NEO4J_PASSWORD` in the process environment or a local secret store.
- Never commit an MCP client file containing real credentials.
- Do not put credentials in `NEO4J_URI`.
- Use unique local/CI passwords and rotate exposed values immediately.

## Reporting

Report suspected vulnerabilities privately to the repository maintainer before opening a public issue. Include the affected commit, reproduction steps using synthetic data, impact, and suggested mitigation. Do not include real credentials or confidential source in the report.