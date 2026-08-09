from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.site_presentation import (
    SitePresentationAdminResponse,
    SitePresentationAdminSummaryResponse,
    SitePresentationContent,
    SitePresentationImageUploadResponse,
    SitePresentationMediaLibraryResponse,
    SitePresentationPublicSummaryResponse,
)
from app.services.site_presentation_service import (
    get_or_create_site_presentation_content,
    get_site_presentation_content,
    get_site_presentation_public_summary,
    get_site_presentation_summary,
    get_site_presentation_uploads_dir,
    list_site_presentation_media_items,
    update_site_presentation_content,
)

router = APIRouter()


@router.get("/content", response_model=SitePresentationContent)
def read_site_presentation_content(db: Session = Depends(get_db)) -> SitePresentationContent:
    return get_site_presentation_content(db)


@router.get("/summary", response_model=SitePresentationPublicSummaryResponse)
def read_site_presentation_public_summary(
    db: Session = Depends(get_db),
) -> SitePresentationPublicSummaryResponse:
    return get_site_presentation_public_summary(db)


@router.get("/admin/content", response_model=SitePresentationAdminResponse)
def read_site_presentation_admin_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SitePresentationAdminResponse:
    content, source = get_or_create_site_presentation_content(db)
    return SitePresentationAdminResponse(content=content, source=source)


@router.put("/admin/content", response_model=SitePresentationAdminResponse)
def write_site_presentation_admin_content(
    payload: SitePresentationContent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SitePresentationAdminResponse:
    updated_content = update_site_presentation_content(db, payload)
    return SitePresentationAdminResponse(content=updated_content, source="database")


@router.get("/admin/media", response_model=SitePresentationMediaLibraryResponse)
def read_site_presentation_media_library(
    current_user: User = Depends(get_current_admin),
) -> SitePresentationMediaLibraryResponse:
    return SitePresentationMediaLibraryResponse(items=list_site_presentation_media_items())


@router.get("/admin/summary", response_model=SitePresentationAdminSummaryResponse)
def read_site_presentation_admin_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SitePresentationAdminSummaryResponse:
    return get_site_presentation_summary(db)


@router.post(
    "/admin/upload-image",
    response_model=SitePresentationImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_site_presentation_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
) -> SitePresentationImageUploadResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit etre une image.",
        )

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
    original_suffix = Path(image.filename or "").suffix.lower()
    suffix = original_suffix if original_suffix in allowed_extensions else ".png"

    uploads_dir = get_site_presentation_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    destination = uploads_dir / filename
    content = await image.read()

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'image depasse la taille maximale autorisee de 10 Mo.",
        )

    destination.write_bytes(content)

    return SitePresentationImageUploadResponse(
        filename=filename,
        url=f"/static/uploads/site-presentation/{filename}",
    )
