"""Tiny stdlib HTTP server exposing POST /interpret."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Iterable

from .adapters import LocalFilesAdapter
from .context import answer_from_context, context_bundle
from .rlm import RLMHarness

# Cap request bodies so a spoofed/huge Content-Length cannot drive an
# unbounded read into memory (DoS).
MAX_BODY_BYTES = 4 * 1024 * 1024  # 4 MiB


def _confine_paths(
    requested: Iterable[str | Path], roots: Iterable[str | Path]
) -> tuple[Path, ...]:
    """Restrict client-requested file paths to the configured roots.

    Each requested path must resolve to a configured file, or to a file under
    a configured directory root. Anything else raises ``PermissionError`` —
    without this, a client could pass ``paths=["/etc/passwd"]`` and exfiltrate
    arbitrary local files (path traversal). If no roots are configured, no
    client-supplied paths are permitted.
    """
    requested = tuple(requested)
    if not requested:
        return ()
    resolved_roots = [Path(root).resolve() for root in roots]
    safe: list[Path] = []
    for raw in requested:
        candidate = Path(raw).resolve()
        allowed = any(
            candidate == root or (root.is_dir() and root in candidate.parents)
            for root in resolved_roots
        )
        if not allowed:
            raise PermissionError(f"path not permitted: {raw}")
        safe.append(candidate)
    return tuple(safe)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json")
    handler.send_header("content-length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def make_handler(base_paths: Iterable[str | Path]) -> type[BaseHTTPRequestHandler]:
    configured_paths = tuple(str(path) for path in base_paths)

    class InterpretHandler(BaseHTTPRequestHandler):
        server_version = "KnitwebLens/0.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/health":
                _json_response(self, 200, {"ok": True, "route": "/interpret"})
                return
            _json_response(self, 404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/interpret":
                _json_response(self, 404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("content-length", "0"))
            except (TypeError, ValueError):
                _json_response(self, 400, {"error": "invalid content-length"})
                return
            if length < 0:
                _json_response(self, 400, {"error": "invalid content-length"})
                return
            if length > MAX_BODY_BYTES:
                _json_response(self, 413, {"error": "request body too large"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if "context" in payload:
                    answer = answer_from_context(payload["context"])
                else:
                    query = payload["query"]
                    requested = _confine_paths(payload.get("paths", ()), configured_paths)
                    paths = tuple(configured_paths) + requested
                    adapters = [LocalFilesAdapter(paths)] if paths else []
                    answer = RLMHarness().query(
                        query,
                        adapters=adapters,
                        max_chunks=int(payload.get("max_chunks", 8)),
                        budget_chars=int(payload.get("budget_chars", 4000)),
                    )
                response = answer.to_dict()
                if payload.get("include_context"):
                    response["context"] = context_bundle(answer.session)
                _json_response(self, 200, response)
            except PermissionError as exc:
                _json_response(self, 403, {"error": str(exc)})
            except Exception as exc:
                _json_response(self, 400, {"error": str(exc)})

    return InterpretHandler


def serve(paths: Iterable[str | Path], *, host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = HTTPServer((host, port), make_handler(paths))
    print(f"Lens serving /interpret on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
