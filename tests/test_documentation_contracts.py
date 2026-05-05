from __future__ import annotations

from pathlib import Path


def test_account_password_docs_mention_server_side_session_revocation() -> None:
    content = Path("public_api/doc/03-api.md").read_text(encoding="utf-8")
    assert "revokes active server-side sessions" in content


def test_docs_mention_traefik_edge_and_account_context_contract() -> None:
    backend_doc = Path("docs/backend/backend.md").read_text(encoding="utf-8")
    account_doc = Path("docs/backend/routes/account.md").read_text(encoding="utf-8")
    user_doc = Path("user_service/doc/03-api.md").read_text(encoding="utf-8")

    assert "Client -> Traefik HTTPS/domain -> nginx HTTP interne -> public_api -> services internes" in backend_doc
    assert "transmet le contexte utilisateur deja resolu" in account_doc
    assert "GET /internal/users/account/api-keys" in user_doc
    assert "DELETE /internal/users/account/api-keys/{api_key_id}" in user_doc
