# Neo4j 5.26 LTS Community for Graphiti on Railway (private network only).
# Upstream image pinned by version and digest; only a small start script is added.
FROM neo4j:5.26.33-community@sha256:577eb43120e8688e62e753e962c47d30044ecaa95147ee5386c29f226b878008

COPY --chmod=0755 start.sh /usr/local/bin/railway-start.sh

# Sized for a small Railway service; override any of them with a service variable
# of the same name (Neo4j's NEO4J_<setting> convention). Listen on :: so the
# IPv6 private network (*.railway.internal) reaches Bolt and HTTP.
ENV NEO4J_server_memory_heap_initial__size=512m \
    NEO4J_server_memory_heap_max__size=1G \
    NEO4J_server_memory_pagecache_size=512m \
    NEO4J_server_default__listen__address=:: \
    NEO4J_server_http_listen__address=:7474 \
    NEO4J_server_bolt_listen__address=:7687 \
    NEO4J_dbms_usage__report_enabled=false

EXPOSE 7474 7687
ENTRYPOINT ["tini", "-g", "--", "/usr/local/bin/railway-start.sh"]
CMD ["neo4j"]
