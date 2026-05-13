from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.services.crawler_rss_install_script import render_crawler_rss_install_script


install_router = APIRouter(prefix="/install", tags=["install"])


@install_router.get("", response_class=PlainTextResponse)
@install_router.get("/", response_class=PlainTextResponse)
def install_crawler_rss() -> PlainTextResponse:
    return PlainTextResponse(
        content=render_crawler_rss_install_script(),
        media_type="text/x-shellscript; charset=utf-8",
    )
