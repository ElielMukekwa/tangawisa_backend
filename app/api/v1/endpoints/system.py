from fastapi import APIRouter

from app.core.config import settings
from app.schemas.system import SystemInfo

router = APIRouter()


@router.get("/info", response_model=SystemInfo)
def get_system_info() -> SystemInfo:
    return SystemInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_prefix=settings.api_v1_prefix,
    )
