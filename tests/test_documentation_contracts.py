from __future__ import annotations

from tests.repo_paths import public_api_root, repo_root

REPO_ROOT = repo_root()
PUBLIC_API_ROOT = public_api_root()


def test_account_password_docs_mention_server_side_session_revocation() -> None:
    content = (PUBLIC_API_ROOT / "doc" / "03-api.md").read_text(encoding="utf-8")
    assert "revokes active server-side sessions" in content


def test_docs_mention_traefik_edge_and_account_context_contract() -> None:
    backend_doc = (REPO_ROOT / "infra" / "README.md").read_text(encoding="utf-8")
    account_doc = (PUBLIC_API_ROOT / "README.md").read_text(encoding="utf-8")
    user_doc = (REPO_ROOT / "user_service" / "doc" / "03-api.md").read_text(encoding="utf-8")

    assert "Client -> Traefik HTTPS/domain -> nginx internal HTTP -> public_api -> internal services" in backend_doc
    assert "Account routes pass the resolved current-user context to `user_service`" in account_doc
    assert "GET /internal/users/account/api-keys" in user_doc
    assert "DELETE /internal/users/account/api-keys/{api_key_id}" in user_doc
