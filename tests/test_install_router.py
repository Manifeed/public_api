from __future__ import annotations

from .conftest import client_context


def test_install_returns_shell_script(app_env) -> None:
    with client_context() as client:
        response = client.get("/install/")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/x-shellscript")
    body = response.text
    assert body.startswith("#!/usr/bin/env sh")
    assert "Manifeed/workers" in body


def test_install_does_not_expose_api_key_route(app_env) -> None:
    with client_context() as client:
        response = client.get("/install/mk_some_token")
    assert response.status_code == 404
