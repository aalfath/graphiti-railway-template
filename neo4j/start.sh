#!/bin/bash
# Sets the initial neo4j password from NEO4J_PASSWORD, then runs the image's own entrypoint.
set -euo pipefail

if [ -z "${NEO4J_AUTH:-}" ]; then
  pw="${NEO4J_PASSWORD:-}"
  if [ "${#pw}" -lt 8 ]; then
    echo "NEO4J_PASSWORD must be set (8+ characters)." >&2
    exit 1
  fi
  export NEO4J_AUTH="neo4j/${pw}"
fi
# The entrypoint turns every NEO4J_* variable into a Neo4j setting, so drop ours first.
unset NEO4J_PASSWORD
exec /startup/docker-entrypoint.sh "$@"
