from __future__ import annotations

from datetime import datetime, timezone

from app.clients.networking.content_service_networking_client import ContentImageRead
from shared_backend.schemas.analytics.analysis_schema import SimilarSourceRead, SimilarSourcesRead
from shared_backend.schemas.rss.rss_company_schema import RssCompanyRead
from shared_backend.schemas.rss.rss_feed_schema import RssFeedRead
from shared_backend.schemas.rss.rss_sync_schema import RssSyncRead
from shared_backend.schemas.sources.source_schema import (
    RssSourceDetailRead,
    RssSourcePageRead,
    RssSourceRead,
    UserSourceDetailRead,
    UserSourcePageRead,
    UserSourceRead,
)
from app.services import rss_service, sources_service

from .conftest import (
    client_context,
    override_authenticated_user,
    override_masked_admin_user,
)


def test_admin_rss_routes_delegate_and_return_payload(
    app_env,
    monkeypatch,
    admin_user,
) -> None:
    company = RssCompanyRead(id=1, name="ACME", icon_url="https://cdn.test/icon.svg", enabled=True)
    feed = RssFeedRead(
        id=9,
        url="https://example.com/rss.xml",
        section="tech",
        enabled=True,
        trust_score=0.8,
        fetchprotection=1,
        consecutive_error_count=0,
        company=company,
    )
    sync_result = RssSyncRead(
        repository_action="up_to_date",
        mode="noop",
        current_revision="abc123",
        applied_from_revision="abc123",
        files_processed=0,
        companies_removed=0,
        feeds_removed=0,
    )
    seen: dict[str, object] = {}

    monkeypatch.setattr(rss_service, "list_rss_companies", lambda: [company])
    monkeypatch.setattr(
        rss_service,
        "list_rss_feeds",
        lambda *, company_id: _store_and_return(seen, "company_id", company_id, [feed]),
    )
    monkeypatch.setattr(
        rss_service,
        "sync_rss_catalog",
        lambda *, force: _store_and_return(seen, "sync_force", force, sync_result),
    )
    monkeypatch.setattr(
        rss_service,
        "toggle_rss_feed_enabled",
        lambda *, feed_id, payload: {"feed_id": feed_id, "enabled": payload.enabled},
    )
    monkeypatch.setattr(
        rss_service,
        "toggle_rss_company_enabled",
        lambda *, company_id, payload: {"company_id": company_id, "enabled": payload.enabled},
    )

    with client_context() as client:
        override_masked_admin_user(client.app, admin_user)

        companies_response = client.get("/api/admin/rss/companies")
        feeds_response = client.get("/api/admin/rss/", params={"company_id": 1})
        sync_response = client.post("/api/admin/rss/sync?force=true", headers={"origin": "http://frontend.test"})
        feed_toggle_response = client.patch(
            "/api/admin/rss/feeds/9/enabled",
            json={"enabled": False},
            headers={"origin": "http://frontend.test"},
        )
        company_toggle_response = client.patch(
            "/api/admin/rss/companies/1/enabled",
            json={"enabled": False},
            headers={"origin": "http://frontend.test"},
        )

    assert companies_response.status_code == 200
    assert companies_response.json()[0]["name"] == "ACME"
    assert feeds_response.status_code == 200
    assert feeds_response.json()[0]["id"] == 9
    assert seen["company_id"] == 1
    assert sync_response.status_code == 200
    assert sync_response.json()["repository_action"] == "up_to_date"
    assert seen["sync_force"] is True
    assert feed_toggle_response.status_code == 200
    assert feed_toggle_response.json() == {"feed_id": 9, "enabled": False}
    assert company_toggle_response.status_code == 200
    assert company_toggle_response.json() == {"company_id": 1, "enabled": False}


def test_public_rss_icon_streams_content_and_filename(app_env, monkeypatch) -> None:
    monkeypatch.setattr(
        rss_service,
        "read_rss_icon",
        lambda *, icon_url: ContentImageRead(
            content=b"<svg></svg>",
            media_type="image/svg+xml",
            filename="logo.svg",
        ),
    )

    with client_context() as client:
        response = client.get("/api/rss/img/assets/logo.svg")

    assert response.status_code == 200
    assert response.content == b"<svg></svg>"
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["content-disposition"] == 'attachment; filename="logo.svg"'


def test_sources_routes_cover_user_and_admin_flows(
    app_env,
    monkeypatch,
    authenticated_user,
    admin_user,
) -> None:
    now = datetime.now(timezone.utc)
    rss_page = RssSourcePageRead(
        items=[
            RssSourceRead(
                id=11,
                title="Admin source",
                authors=[],
                url="https://example.com/admin-source",
                published_at=now,
                company_names=["ACME"],
                image_url="https://cdn.test/admin.png",
            )
        ],
        total=1,
        limit=50,
        offset=0,
    )
    user_page = UserSourcePageRead(
        items=[
            UserSourceRead(
                id=21,
                title="User source",
                authors=[],
                url="https://example.com/user-source",
                published_at=now,
                company_names=["ACME"],
            )
        ],
        total=1,
        limit=24,
        offset=0,
    )
    user_detail = UserSourceDetailRead(
        id=21,
        title="User source",
        authors=[],
        url="https://example.com/user-source",
        published_at=now,
        company_names=["ACME"],
        summary="summary",
        feed_sections=["tech"],
    )
    admin_detail = RssSourceDetailRead(
        id=11,
        title="Admin source",
        authors=[],
        url="https://example.com/admin-source",
        published_at=now,
        company_names=["ACME"],
        summary="admin-summary",
        feed_sections=["tech"],
        image_url="https://cdn.test/admin.png",
    )
    similar = SimilarSourcesRead(
        source_id=21,
        worker_version="worker-v1",
        items=[SimilarSourceRead(score=0.9, source=user_detail)],
    )
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        sources_service,
        "list_admin_sources",
        lambda *, limit, offset, author_id: _capture(
            seen,
            "admin_sources",
            {"limit": limit, "offset": offset, "author_id": author_id},
            rss_page,
        ),
    )
    monkeypatch.setattr(
        sources_service,
        "list_admin_sources_by_feed",
        lambda *, feed_id, limit, offset, author_id: _capture(
            seen,
            "admin_by_feed",
            {"feed_id": feed_id, "limit": limit, "offset": offset, "author_id": author_id},
            rss_page,
        ),
    )
    monkeypatch.setattr(
        sources_service,
        "list_admin_sources_by_company",
        lambda *, company_id, limit, offset, author_id: _capture(
            seen,
            "admin_by_company",
            {"company_id": company_id, "limit": limit, "offset": offset, "author_id": author_id},
            rss_page,
        ),
    )
    monkeypatch.setattr(sources_service, "read_admin_source", lambda *, source_id: admin_detail)
    monkeypatch.setattr(
        sources_service,
        "list_user_sources",
        lambda *, limit, offset: _capture(
            seen,
            "user_sources",
            {"limit": limit, "offset": offset},
            user_page,
        ),
    )
    monkeypatch.setattr(sources_service, "read_user_source", lambda *, source_id: user_detail)
    monkeypatch.setattr(
        sources_service,
        "read_similar_sources",
        lambda *, source_id, limit, worker_version: _capture(
            seen,
            "similar",
            {"source_id": source_id, "limit": limit, "worker_version": worker_version},
            similar,
        ),
    )

    with client_context() as client:
        override_authenticated_user(client.app, authenticated_user)
        override_masked_admin_user(client.app, admin_user)
        client.cookies.set("manifeed_session", "session-token")

        admin_sources_response = client.get("/api/admin/sources/", params={"author_id": 5})
        admin_feed_response = client.get("/api/admin/sources/feeds/7", params={"offset": 10})
        admin_company_response = client.get("/api/admin/sources/companies/3", params={"limit": 20})
        admin_source_response = client.get("/api/admin/sources/11")
        user_sources_response = client.get("/api/sources/")
        user_source_response = client.get("/api/sources/21")
        similar_response = client.get(
            "/api/sources/21/similar",
            params={"limit": 5, "worker_version": "worker-v1"},
        )

    assert admin_sources_response.status_code == 200
    assert admin_sources_response.json()["items"][0]["id"] == 11
    assert seen["admin_sources"] == {"limit": 50, "offset": 0, "author_id": 5}
    assert admin_feed_response.status_code == 200
    assert seen["admin_by_feed"] == {"feed_id": 7, "limit": 50, "offset": 10, "author_id": None}
    assert admin_company_response.status_code == 200
    assert seen["admin_by_company"] == {"company_id": 3, "limit": 20, "offset": 0, "author_id": None}
    assert admin_source_response.status_code == 200
    assert admin_source_response.json()["summary"] == "admin-summary"
    assert user_sources_response.status_code == 200
    assert user_sources_response.json()["items"][0]["id"] == 21
    assert seen["user_sources"] == {"limit": 24, "offset": 0}
    assert user_source_response.status_code == 200
    assert user_source_response.json()["summary"] == "summary"
    assert similar_response.status_code == 200
    assert similar_response.json()["items"][0]["score"] == 0.9
    assert seen["similar"] == {"source_id": 21, "limit": 5, "worker_version": "worker-v1"}


def _store_and_return(
    seen: dict[str, object],
    key: str,
    value: object,
    result,
):
    seen[key] = value
    return result


def _capture(
    seen: dict[str, object],
    key: str,
    value: object,
    result,
):
    seen[key] = value
    return result
