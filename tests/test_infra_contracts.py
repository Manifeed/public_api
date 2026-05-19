from __future__ import annotations

import re

from tests.repo_paths import repo_root


REPO_ROOT = repo_root()


def test_edge_nginx_is_traefik_internal_only_by_default() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    edge_section = _service_section(compose, "edge_nginx")

    assert "ports:" not in edge_section
    assert "- traefik_proxy" in edge_section
    assert "TRAEFIK_NETWORK_NAME:-traefik_proxy" in compose


def test_redis_stays_internal_without_host_ports() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    redis_section = _service_section(compose, "redis")
    assert "ports:" not in redis_section


def test_postgres_and_qdrant_publish_optional_local_tooling_ports() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    postgres_section = _service_section(compose, "postgres")
    qdrant_section = _service_section(compose, "qdrant")

    assert "5432:5432" in postgres_section
    assert "6333:6333" in qdrant_section


def _service_section(compose: str, service_name: str) -> str:
    match = re.search(rf"^  {re.escape(service_name)}:\n(?P<body>.*?)(?=^  \S|\Z)", compose, re.M | re.S)
    assert match is not None
    return match.group("body")
