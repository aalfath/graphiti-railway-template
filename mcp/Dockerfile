# Graphiti MCP server (getzep/graphiti mcp_server) on Railway, Neo4j backend.
# Upstream standalone image pinned by version and digest; only a small launcher is added.
FROM zepai/knowledge-graph-mcp:1.1.3-graphiti-0.31.2-standalone@sha256:76b835abad42b6c47aea78860014850e300b6a237c0ce3de314b1e0b174c11a2

COPY --chmod=0644 railway_mcp.py /app/mcp/railway_mcp.py

# Upstream's Neo4j config file (reads NEO4J_*, OPENAI_*, MODEL_NAME, EMBEDDER_MODEL from env).
ENV CONFIG_PATH=/app/mcp/config/config-docker-neo4j.yaml \
    EMBEDDING_DIM=1536 \
    GRAPHITI_TELEMETRY_ENABLED=false \
    NEO4J_USER=neo4j \
    NEO4J_DATABASE=neo4j \
    PORT=8000

EXPOSE 8000
WORKDIR /app/mcp
CMD ["/app/mcp/.venv/bin/python", "/app/mcp/railway_mcp.py"]
