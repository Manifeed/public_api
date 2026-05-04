from __future__ import annotations

from datetime import datetime, timezone

from app.services import admin_dashboard_service, jobs_service
from shared_backend.schemas.analytics.analysis_schema import AnalysisOverviewRead, SimilarSourceRead, SimilarSourcesRead
from shared_backend.schemas.health import HealthRead, HealthServiceRead
from shared_backend.schemas.jobs.job_automation_schema import JobAutomationRead
from shared_backend.schemas.jobs.job_enqueue_schema import JobEnqueueRead
from shared_backend.schemas.jobs.job_schema import (
    JobControlCommandRead,
    JobOverviewItemRead,
    JobStatusRead,
    JobTaskRead,
    JobsOverviewRead,
)
from shared_backend.schemas.sources.source_schema import UserSourceDetailRead

from .conftest import client_context, override_masked_admin_user


def test_admin_dashboard_routes_return_service_payloads(
    app_env,
    monkeypatch,
    admin_user,
) -> None:
    now = datetime.now(timezone.utc)
    health = HealthRead(
        status="ok",
        database="ok",
        services={
            "auth": HealthServiceRead(
                name="auth",
                kind="http",
                status="ok",
                detail="upstream_status=ok",
                latency_ms=12,
            )
        },
    )
    overview = AnalysisOverviewRead(
        total_sources=100,
        indexed_embeddings=95,
        qdrant_collection="sources",
    )
    source_detail = UserSourceDetailRead(
        id=88,
        title="Nearest source",
        authors=[],
        url="https://example.com/source",
        published_at=now,
        company_names=["ACME"],
        summary="nearest summary",
        feed_sections=["ai"],
    )
    similar = SimilarSourcesRead(
        source_id=88,
        worker_version="worker-v2",
        items=[SimilarSourceRead(score=0.91, source=source_detail)],
    )
    seen: dict[str, object] = {}

    monkeypatch.setattr(admin_dashboard_service, "read_health", lambda: health)
    monkeypatch.setattr(admin_dashboard_service, "read_analysis_overview", lambda: overview)
    monkeypatch.setattr(
        admin_dashboard_service,
        "read_similar_sources",
        lambda *, source_id, limit, worker_version: _capture(
            seen,
            "similar",
            {"source_id": source_id, "limit": limit, "worker_version": worker_version},
            similar,
        ),
    )

    with client_context() as client:
        override_masked_admin_user(client.app, admin_user)
        health_response = client.get("/api/admin/health/")
        overview_response = client.get("/api/admin/analysis/overview")
        similar_response = client.get(
            "/api/admin/analysis/similar-sources",
            params={"source_id": 88, "limit": 7, "worker_version": "worker-v2"},
        )

    assert health_response.status_code == 200
    assert health_response.json()["database"] == "ok"
    assert overview_response.status_code == 200
    assert overview_response.json()["indexed_embeddings"] == 95
    assert similar_response.status_code == 200
    assert similar_response.json()["items"][0]["source"]["id"] == 88
    assert seen["similar"] == {"source_id": 88, "limit": 7, "worker_version": "worker-v2"}


def test_jobs_routes_cover_overview_enqueue_automation_and_details(
    app_env,
    monkeypatch,
    admin_user,
) -> None:
    now = datetime.now(timezone.utc)
    jobs_overview = JobsOverviewRead(
        generated_at=now,
        items=[
            JobOverviewItemRead(
                job_id="job-1",
                job_kind="rss_scrape",
                status="queued",
                requested_at=now,
                task_total=3,
                task_processed=0,
                item_success=0,
                item_error=0,
            )
        ],
    )
    enqueue_result = JobEnqueueRead(
        job_id="job-2",
        job_kind="source_embedding",
        status="queued",
        worker_version="worker-v3",
        tasks_total=1,
        items_total=5,
    )
    automation = JobAutomationRead(
        enabled=True,
        interval_minutes=15,
        status="idle",
        message="ready",
        connected_workers=2,
        connected_rss_workers=1,
        connected_embedding_workers=1,
        last_cycle_started_at=now,
        next_run_at=now,
        current_ingest_job_id=None,
        current_ingest_status=None,
        current_embed_job_id=None,
        current_embed_status=None,
    )
    tasks = [
        JobTaskRead(
            task_id=1,
            status="pending",
            claimed_at=None,
            completed_at=None,
            claim_expires_at=None,
            item_total=2,
            item_success=0,
            item_error=0,
        )
    ]
    job_status = JobStatusRead(
        job_id="job-1",
        job_kind="rss_scrape",
        status="processing",
        requested_at=now,
        task_total=3,
        task_processed=1,
        item_success=10,
        item_error=1,
        worker_version="worker-v3",
        started_at=now,
        finished_at=None,
        item_total=11,
        finalized_at=None,
    )
    deleted_job = JobControlCommandRead(
        ok=True,
        job_id="job-1",
        status=None,
        deleted=True,
    )
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        jobs_service,
        "list_jobs",
        lambda *, limit: _capture(seen, "list_jobs", {"limit": limit}, jobs_overview),
    )
    monkeypatch.setattr(
        jobs_service,
        "enqueue_rss_scrape_job",
        lambda payload: _capture(seen, "rss_payload", payload.model_dump(), enqueue_result),
    )
    monkeypatch.setattr(
        jobs_service,
        "enqueue_source_embedding_job",
        lambda payload: _capture(seen, "embedding_payload", payload.model_dump(), enqueue_result),
    )
    monkeypatch.setattr(jobs_service, "read_job_automation", lambda: automation)
    monkeypatch.setattr(
        jobs_service,
        "update_job_automation",
        lambda payload: _capture(seen, "automation_payload", payload.model_dump(), automation),
    )
    monkeypatch.setattr(
        jobs_service,
        "list_job_tasks",
        lambda *, job_id: _capture(seen, "tasks_job_id", job_id, tasks),
    )
    monkeypatch.setattr(
        jobs_service,
        "read_job_status",
        lambda *, job_id: _capture(seen, "status_job_id", job_id, job_status),
    )
    monkeypatch.setattr(
        jobs_service,
        "pause_job",
        lambda *, job_id: _capture(seen, "pause_job_id", job_id, job_status.model_copy(update={"status": "paused"})),
    )
    monkeypatch.setattr(
        jobs_service,
        "resume_job",
        lambda *, job_id: _capture(seen, "resume_job_id", job_id, job_status),
    )
    monkeypatch.setattr(
        jobs_service,
        "cancel_job",
        lambda *, job_id: _capture(seen, "cancel_job_id", job_id, job_status.model_copy(update={"status": "cancelled"})),
    )
    monkeypatch.setattr(
        jobs_service,
        "delete_job",
        lambda *, job_id: _capture(seen, "delete_job_id", job_id, deleted_job),
    )

    with client_context() as client:
        override_masked_admin_user(client.app, admin_user)
        overview_response = client.get("/api/admin/jobs", params={"limit": 25})
        rss_enqueue_response = client.post(
            "/api/admin/jobs/rss-scrape",
            json={"feed_ids": [1, 2]},
            headers={"origin": "http://frontend.test"},
        )
        embedding_enqueue_response = client.post(
            "/api/admin/jobs/source-embedding",
            json={"reembed_model_mismatches": True},
            headers={"origin": "http://frontend.test"},
        )
        automation_response = client.get("/api/admin/jobs/automation")
        automation_update_response = client.patch(
            "/api/admin/jobs/automation",
            json={"enabled": False},
            headers={"origin": "http://frontend.test"},
        )
        tasks_response = client.get("/api/admin/jobs/job-1/tasks")
        status_response = client.get("/api/admin/jobs/job-1")
        pause_response = client.post(
            "/api/admin/jobs/job-1/pause",
            headers={"origin": "http://frontend.test"},
        )
        resume_response = client.post(
            "/api/admin/jobs/job-1/resume",
            headers={"origin": "http://frontend.test"},
        )
        cancel_response = client.post(
            "/api/admin/jobs/job-1/cancel",
            headers={"origin": "http://frontend.test"},
        )
        delete_response = client.delete(
            "/api/admin/jobs/job-1",
            headers={"origin": "http://frontend.test"},
        )

    assert overview_response.status_code == 200
    assert overview_response.json()["items"][0]["job_id"] == "job-1"
    assert seen["list_jobs"] == {"limit": 25}
    assert rss_enqueue_response.status_code == 200
    assert seen["rss_payload"] == {"feed_ids": [1, 2]}
    assert embedding_enqueue_response.status_code == 200
    assert seen["embedding_payload"] == {"reembed_model_mismatches": True}
    assert automation_response.status_code == 200
    assert automation_response.json()["status"] == "idle"
    assert automation_update_response.status_code == 200
    assert seen["automation_payload"] == {"enabled": False}
    assert tasks_response.status_code == 200
    assert tasks_response.json()[0]["task_id"] == 1
    assert seen["tasks_job_id"] == "job-1"
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "processing"
    assert seen["status_job_id"] == "job-1"
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"
    assert seen["pause_job_id"] == "job-1"
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "processing"
    assert seen["resume_job_id"] == "job-1"
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert seen["cancel_job_id"] == "job-1"
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
    assert seen["delete_job_id"] == "job-1"


def _capture(
    seen: dict[str, object],
    key: str,
    value: object,
    result,
):
    seen[key] = value
    return result
