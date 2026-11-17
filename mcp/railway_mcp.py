"""Railway launcher for the Graphiti MCP server (getzep/graphiti mcp_server).

Runs the unchanged upstream server (streamable HTTP at /mcp) and adds:
  * a bearer-token check (GRAPHITI_API_KEY) on everything except /health,
  * a wait for Neo4j before start-up,
  * listening on IPv4 and IPv6 ($PORT) so both Railway's public proxy and the private network reach it.
"""
import asyncio
import hmac
import json
import os
import socket
import sys
import time

sys.path.insert(0, "/app/mcp/src")

PUBLIC_PATHS = {"/health"}


def log(msg):
    print(f"[railway] {msg}", flush=True)


def wait_for_neo4j():
    uri = os.environ.get("NEO4J_URI")
    if not uri:
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
        body = json.dumps({"error": "Missing or invalid API key (Authorization: Bearer GRAPHITI_API_KEY)"}).encode()
        await send({"type": "http.response.start", "status": 401, "headers": [
            (b"content-type", b"application/json"), (b"www-authenticate", b"Bearer"),
            (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


async def serve():
    import uvicorn
    import graphiti_mcp_server as g

    cfg = await g.initialize_server()
    # host=0.0.0.0 keeps the SDK's localhost-only DNS-rebinding allow-list off: behind
    # Railway's proxy the Host header is the public domain. Access is guarded by the key instead.
    app = g.mcp.streamable_http_app(host="0.0.0.0")
    key = os.environ.get("GRAPHITI_API_KEY", "")
    if os.environ.get("GRAPHITI_AUTH", "on").lower() in ("off", "false", "0", "disabled"):
        log("GRAPHITI_AUTH=off: the MCP endpoint is open to anyone who knows the URL")
    elif len(key) < 16:
        log("GRAPHITI_API_KEY must be set (16+ characters), or set GRAPHITI_AUTH=off to run without auth")
        sys.exit(1)
    else:
        app = BearerAuth(app, key, PUBLIC_PATHS)
    port = int(os.environ.get("PORT", "8000"))
    log(f"MCP endpoint: /mcp on port {port} (transport {cfg.transport})")
    config = uvicorn.Config(app, host="::", port=port, proxy_headers=True, forwarded_allow_ips="*",
                            log_level="info")
    server = uvicorn.Server(config)
    g.configure_uvicorn_logging()
    await server.serve(sockets=[dual_stack_socket(port)])


if __name__ == "__main__":
    if "--config" not in sys.argv:
        sys.argv += ["--config", os.environ.get("CONFIG_PATH", "/app/mcp/config/config-docker-neo4j.yaml")]
    if "--transport" not in sys.argv:
        sys.argv += ["--transport", "http"]
    if not os.environ.get("OPENAI_API_KEY"):
        log("OPENAI_API_KEY is not set; Graphiti needs it for extraction and embeddings")
        sys.exit(1)
    wait_for_neo4j()
    asyncio.run(serve())
