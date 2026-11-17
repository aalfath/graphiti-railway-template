"""Railway launcher for the Graphiti REST API (getzep/graphiti server/graph_service).

Adds three things around the unchanged upstream app:
  * a bearer-token check (GRAPHITI_API_KEY) on every route except /healthcheck and the API docs,
  * a wait for Neo4j before start-up (the app builds indices on start and exits if Neo4j is down),
  * listening on IPv4 and IPv6 ($PORT) so both Railway's public proxy and the private network reach it.
"""
import hmac
import json
import os
import socket
import sys
import time

import uvicorn
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse

PUBLIC_PATHS = {"/healthcheck", "/docs", "/docs/oauth2-redirect", "/openapi.json", "/"}


def log(msg):
    print(f"[railway] {msg}", flush=True)


def wait_for_neo4j():
    uri = os.environ.get("NEO4J_URI")
    if not uri or os.environ.get("DB_BACKEND", os.environ.get("db_backend", "neo4j")) != "neo4j":
        return
    from neo4j import GraphDatabase

    deadline = time.time() + int(os.environ.get("NEO4J_WAIT_SECONDS", "240"))
    auth = (os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", ""))
    while True:
        try:
            with GraphDatabase.driver(uri, auth=auth) as driver:
                driver.verify_connectivity()
            log(f"Neo4j is reachable at {uri}")
            return
        except Exception as e:  # noqa: BLE001
            if time.time() > deadline:
                log(f"Neo4j still unreachable at {uri}: {e}")
                sys.exit(1)
            log(f"waiting for Neo4j at {uri}: {type(e).__name__}")
            time.sleep(3)


def dual_stack_socket(port):
    """One socket for IPv4 and IPv6. asyncio sets IPV6_V6ONLY on '::', which would refuse IPv4."""
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::", port))
    sock.set_inheritable(True)
    return sock


class BearerAuth:
    """Pure ASGI middleware: requires `Authorization: Bearer <key>` (or `X-API-Key: <key>`)."""

    def __init__(self, app, key, public_paths):
        self.app, self.key, self.public = app, key.encode(), public_paths

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") in self.public:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"")
        token = auth[7:].strip() if auth[:7].lower() == b"bearer " else headers.get(b"x-api-key", b"").strip()
        if token and hmac.compare_digest(token, self.key):
            return await self.app(scope, receive, send)
        body = json.dumps({"detail": "Missing or invalid API key (Authorization: Bearer GRAPHITI_API_KEY)"}).encode()
        await send({"type": "http.response.start", "status": 401, "headers": [
            (b"content-type", b"application/json"), (b"www-authenticate", b"Bearer"),
            (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


def build_app():
    from graph_service.main import app

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse("/docs")

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title="Graphiti", version="0.31.2", routes=app.routes)
        schema.setdefault("components", {})["securitySchemes"] = {"bearerAuth": {"type": "http", "scheme": "bearer"}}
        schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = openapi

    key = os.environ.get("GRAPHITI_API_KEY", "")
    if os.environ.get("GRAPHITI_AUTH", "on").lower() in ("off", "false", "0", "disabled"):
        log("GRAPHITI_AUTH=off: the API is open to anyone who knows the URL")
        return app
    if len(key) < 16:
        log("GRAPHITI_API_KEY must be set (16+ characters), or set GRAPHITI_AUTH=off to run without auth")
        sys.exit(1)
    return BearerAuth(app, key, PUBLIC_PATHS)


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        log("OPENAI_API_KEY is not set; Graphiti needs it for extraction and embeddings")
        sys.exit(1)
    wait_for_neo4j()
    port = int(os.environ.get("PORT", "8000"))
    config = uvicorn.Config(build_app(), host="::", port=port, proxy_headers=True, forwarded_allow_ips="*")
    uvicorn.Server(config).run(sockets=[dual_stack_socket(port)])
