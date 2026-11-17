# Changelog

Breaking changes are listed first in each entry.

## 0.31.2-1 (2026-11-17)

First release of the template.

- Graphiti REST API 0.31.2: `zepai/graphiti:0.31.2@sha256:ab861ecc909bc726de387e05cb36116c2c7e0856ca2720138b6c9d4f2bc80988`
- Graphiti MCP server 1.1.3 (graphiti-core 0.31.2): `zepai/knowledge-graph-mcp:1.1.3-graphiti-0.31.2-standalone@sha256:76b835abad42b6c47aea78860014850e300b6a237c0ce3de314b1e0b174c11a2`
- Neo4j 5.26.33 Community: `neo4j:5.26.33-community@sha256:577eb43120e8688e62e753e962c47d30044ecaa95147ee5386c29f226b878008`, data on a `/data` volume
- Bearer-key check (`GRAPHITI_API_KEY`) on both public services; health paths stay open.
