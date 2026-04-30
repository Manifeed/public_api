from __future__ import annotations

from pathlib import Path


def test_account_password_docs_mention_server_side_session_revocation() -> None:
    content = Path("public_api/doc/03-api.md").read_text(encoding="utf-8")
    assert "revokes active server-side sessions" in content
