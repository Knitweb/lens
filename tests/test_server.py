from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest

from knitweb_lens.server import _confine_paths, make_handler


def test_confine_rejects_paths_outside_roots(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "ok.md").write_text("hello", encoding="utf-8")
    with pytest.raises(PermissionError):
        _confine_paths(["/etc/passwd"], [root])


def test_confine_rejects_traversal_escape(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    secret = tmp_path / "secret.md"
    secret.write_text("top secret", encoding="utf-8")
    # ../secret.md escapes the configured root → rejected.
    with pytest.raises(PermissionError):
        _confine_paths([str(root / ".." / "secret.md")], [root])


def test_confine_allows_file_under_root(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    ok = root / "ok.md"
    ok.write_text("hello", encoding="utf-8")
    result = _confine_paths([str(ok)], [root])
    assert result == (ok.resolve(),)


def test_confine_no_roots_permits_nothing(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(PermissionError):
        _confine_paths([str(f)], [])


def test_confine_empty_request_is_noop(tmp_path):
    assert _confine_paths([], [tmp_path]) == ()


@pytest.fixture
def server(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "doc.md").write_text("knitweb fabric notes", encoding="utf-8")
    httpd = HTTPServer(("127.0.0.1", 0), make_handler([root]))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd, tmp_path
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _post(httpd, body: bytes, headers: dict | None = None):
    host, port = httpd.server_address
    req = urllib.request.Request(
        f"http://{host}:{port}/interpret",
        data=body,
        headers=headers or {"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_post_rejects_client_path_outside_root(server):
    httpd, _ = server
    body = json.dumps({"query": "secrets", "paths": ["/etc/passwd"]}).encode("utf-8")
    status, payload = _post(httpd, body)
    assert status == 403
    assert "not permitted" in payload["error"]


def test_post_rejects_oversized_body(server):
    httpd, _ = server
    # Lie about a huge Content-Length without sending the bytes.
    headers = {"content-type": "application/json", "content-length": str(10 * 1024 * 1024)}
    status, payload = _post(httpd, b"{}", headers=headers)
    assert status == 413
    assert "too large" in payload["error"]
