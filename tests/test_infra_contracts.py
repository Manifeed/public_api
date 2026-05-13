from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_edge_nginx_is_traefik_internal_only_by_default() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    edge_section = _service_section(compose, "edge_nginx")

    assert "ports:" not in edge_section
    assert "- traefik_proxy" in edge_section
    assert "TRAEFIK_NETWORK_NAME:-traefik_proxy" in compose


def test_stateful_services_do_not_publish_host_ports_by_default() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    for service_name in ("postgres", "redis", "qdrant"):
        section = _service_section(compose, service_name)
        assert "ports:" not in section


def _service_section(compose: str, service_name: str) -> str:
    match = re.search(rf"^  {re.escape(service_name)}:\n(?P<body>.*?)(?=^  \S|\Z)", compose, re.M | re.S)
    assert match is not None
    return match.group("body")
