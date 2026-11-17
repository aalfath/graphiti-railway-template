# Graphiti REST API server (graph_service) on Railway.
# Upstream image pinned by version and digest; only a small launcher is added.
FROM zepai/graphiti:0.31.2@sha256:ab861ecc909bc726de387e05cb36116c2c7e0856ca2720138b6c9d4f2bc80988

COPY --chmod=0644 railway_app.py /app/railway_app.py

# Same embedding size as the MCP service (text-embedding-3-small = 1536), so both
# can share one graph. Telemetry off by default; set it to true to opt in.
ENV EMBEDDING_DIM=1536 \
    GRAPHITI_TELEMETRY_ENABLED=false \
    NEO4J_USER=neo4j \
    PORT=8000

EXPOSE 8000
CMD ["python", "/app/railway_app.py"]
