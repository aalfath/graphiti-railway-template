[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/graphiti?utm_medium=integration&utm_source=button&utm_campaign=graphiti)

# Graphiti on Railway

Railway template for [Graphiti](https://github.com/getzep/graphiti) by Zep, the open-source framework for temporal knowledge graphs that AI agents use as memory.

**Deploys Graphiti 0.31.2**, built from the official images, each pinned by version and digest:

| Service | Folder | Base image | Public |
|---|---|---|---|
| **Graphiti** (REST API, `graph_service`) | [`api/`](api) | `zepai/graphiti:0.31.2@sha256:ab861ecc…` | yes, port 8000 |
| **Graphiti MCP** (MCP server 1.1.3, streamable HTTP) | [`mcp/`](mcp) | `zepai/knowledge-graph-mcp:1.1.3-graphiti-0.31.2-standalone@sha256:76b835ab…` | yes, port 8000 |
| **Neo4j** 5.26 LTS Community | [`neo4j/`](neo4j) | `neo4j:5.26.33-community@sha256:577eb431…` | no (private network only), volume at `/data` |

The graph lives on the Neo4j volume, so it survives redeploys and restarts. The two Graphiti services are stateless and share that graph.

## What you get

| Endpoint | Use it for |
|---|---|
| `https://GRAPHITI-DOMAIN/docs` | Swagger UI for the REST API (`/messages`, `/search`, `/get-memory`, `/episodes/{group_id}`, …). Click **Authorize** and paste `GRAPHITI_API_KEY`. |
| `https://GRAPHITI-DOMAIN/healthcheck` | Health check (no key needed). |
| `https://GRAPHITI-MCP-DOMAIN/mcp` | MCP endpoint (streamable HTTP) for Claude Code, Cursor, VS Code and other MCP clients. |
| `https://GRAPHITI-MCP-DOMAIN/health` | Health check (no key needed). |

Both public services require `Authorization: Bearer GRAPHITI_API_KEY` (or `X-API-Key: GRAPHITI_API_KEY`). Upstream Graphiti has no authentication of its own; the small launcher in each folder adds this check and nothing else.

### Connect an MCP client

```sh
claude mcp add --transport http graphiti https://GRAPHITI-MCP-DOMAIN/mcp \
  --header "Authorization: Bearer GRAPHITI_API_KEY"
```

Cursor and VS Code: add an HTTP MCP server with that URL and the same `Authorization` header.

### Call the REST API

```sh
curl -X POST https://GRAPHITI-DOMAIN/messages \
  -H "Authorization: Bearer GRAPHITI_API_KEY" -H "Content-Type: application/json" \
  -d '{"group_id":"demo","messages":[{"content":"Alice moved to Berlin in 2024.","role_type":"user","role":"alice","timestamp":"2026-01-01T00:00:00Z"}]}'

curl -X POST https://GRAPHITI-DOMAIN/search \
  -H "Authorization: Bearer GRAPHITI_API_KEY" -H "Content-Type: application/json" \
  -d '{"group_ids":["demo"],"query":"Where does Alice live?","max_facts":5}'
```

## Variables

| Service | Variable | Default | Notes |
|---|---|---|---|
| Graphiti | `OPENAI_API_KEY` | *(you enter it)* | The only prompt. Graphiti uses it for entity extraction (LLM) and embeddings. |
| Graphiti | `GRAPHITI_API_KEY` | generated (`secret(48)`) | Bearer key for both public services. |
| Graphiti | `NEO4J_URI` | `bolt://${{Neo4j.RAILWAY_PRIVATE_DOMAIN}}:7687` | Private network. |
| Graphiti | `NEO4J_PASSWORD` | `${{Neo4j.NEO4J_PASSWORD}}` | |
| Graphiti MCP | `OPENAI_API_KEY`, `GRAPHITI_API_KEY` | references to the Graphiti service | One key to enter, one key to use. |
| Neo4j | `NEO4J_PASSWORD` | generated (`secret(32)`) | Password of the `neo4j` user, applied on the first start of an empty volume only. Change it later with `ALTER CURRENT USER SET PASSWORD` and update the variable to match. |

Optional, add them yourself:

- `MODEL_NAME` (both services): the OpenAI chat model used for extraction (upstream default otherwise).
- Embeddings use `text-embedding-3-small` at 1536 dimensions (`EMBEDDING_DIM`) on both services, so they share one graph. The MCP service can switch models with `EMBEDDER_MODEL`. Don't change the embedding size once the graph has data.
- `OPENAI_API_URL` (MCP): an OpenAI-compatible endpoint for both chat and embeddings. On the REST API, upstream's `OPENAI_BASE_URL` changes only the chat endpoint; embeddings still go to OpenAI.
- `GRAPHITI_GROUP_ID` (MCP): the default group (namespace), `main`.
- `GRAPHITI_TELEMETRY_ENABLED=true`: opt in to Graphiti's anonymous telemetry (off by default here).
- Neo4j memory: `NEO4J_server_memory_heap_max__size` (default `1G`) and `NEO4J_server_memory_pagecache_size` (default `512m`).

If you only need one interface, delete the other Graphiti service; the graph is unaffected.

## Updates

Each merge to this repo's `main` branch shows up as an "update available" notice in Railway projects deployed from the template. Read [CHANGELOG.md](CHANGELOG.md) before you apply one. Back up the Neo4j volume before major Neo4j upgrades.

## License

The wrapper in this repo is MIT. Graphiti is Apache-2.0 (Zep Software, Inc.). Neo4j Community Edition is GPLv3 (Neo4j, Inc.).
