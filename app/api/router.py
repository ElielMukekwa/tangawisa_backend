from fastapi import APIRouter

from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.client import router as client_router
from app.api.v1.endpoints.marketplace import router as marketplace_router
from app.api.v1.endpoints.seller import router as seller_router
from app.api.v1.endpoints.site_presentation import router as site_presentation_router
from app.api.v1.endpoints.support import router as support_router
from app.api.v1.endpoints.system import router as system_router

api_router = APIRouter()
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(client_router, prefix="/client", tags=["client"])
api_router.include_router(marketplace_router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(seller_router, prefix="/seller", tags=["seller"])
api_router.include_router(site_presentation_router, prefix="/site-presentation", tags=["site-presentation"])
api_router.include_router(support_router, prefix="/support", tags=["support"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
