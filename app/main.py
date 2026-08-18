import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.database.base import Base
from app.database.local_migrations import apply_local_schema_upgrades
from app.database.session import SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.services.dev_seed_service import seed_development_data


def create_application() -> FastAPI:
    backend_dir = Path(__file__).resolve().parents[1]
    project_root = backend_dir.parent
    static_dir = backend_dir / "app" / "public"
    presentation_dir = project_root / "site_presentation"

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/", include_in_schema=False)
    def presentation_home() -> RedirectResponse:
        return RedirectResponse(url="/presentation/")

    @app.get("/admin", include_in_schema=False)
    def admin_home() -> RedirectResponse:
        return RedirectResponse(url="/static/admin/login.html")

    @app.get("/admin/react", include_in_schema=False)
    def react_admin_home() -> RedirectResponse:
        return RedirectResponse(url="/static/admin/react-app/dist/index.html")

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    if presentation_dir.exists():
        app.mount("/presentation", StaticFiles(directory=presentation_dir, html=True), name="presentation")

    if settings.bootstrap_database:
        Base.metadata.create_all(bind=engine)
        apply_local_schema_upgrades(engine)
        if settings.should_seed_development_data:
            with SessionLocal() as db:
                seed_development_data(db)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
