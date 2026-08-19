import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.site_content import SiteContent
from app.models.conversation import Conversation
from app.models.product import Product
from app.models.report import Report
from app.models.shop import Shop
from app.models.support_ticket import SupportTicket
from app.models.user import User, UserRole
from app.schemas.site_presentation import (
    SitePresentationAdminSummaryResponse,
    SitePresentationContent,
    SitePresentationMediaItem,
    SitePresentationPublicStat,
    SitePresentationPublicSummaryResponse,
    SitePresentationSummaryStats,
)
from app.services.media_storage_service import get_media_storage

SITE_PRESENTATION_KEY = "site_presentation"


def _content_path() -> Path:
    return Path(__file__).resolve().parents[1] / "content" / "site_presentation.json"


def load_default_site_presentation_payload() -> dict:
    return json.loads(_content_path().read_text(encoding="utf-8"))


def get_site_presentation_record(db: Session) -> SiteContent | None:
    return db.query(SiteContent).filter(SiteContent.site_key == SITE_PRESENTATION_KEY).first()


def get_site_presentation_content(db: Session | None = None) -> SitePresentationContent:
    if db is not None:
        record = get_site_presentation_record(db)
        if record is not None:
            return SitePresentationContent.model_validate(record.payload)

    return SitePresentationContent.model_validate(load_default_site_presentation_payload())


def get_or_create_site_presentation_content(db: Session) -> tuple[SitePresentationContent, str]:
    record = get_site_presentation_record(db)
    if record is not None:
        return SitePresentationContent.model_validate(record.payload), "database"

    payload = load_default_site_presentation_payload()
    record = SiteContent(site_key=SITE_PRESENTATION_KEY, payload=payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return SitePresentationContent.model_validate(record.payload), "seeded_from_json"


def update_site_presentation_content(
    db: Session,
    payload: SitePresentationContent,
) -> SitePresentationContent:
    record = get_site_presentation_record(db)
    serialized_payload = payload.model_dump(mode="json")

    if record is None:
        record = SiteContent(site_key=SITE_PRESENTATION_KEY, payload=serialized_payload)
        db.add(record)
    else:
        record.payload = serialized_payload

    db.commit()
    db.refresh(record)
    return SitePresentationContent.model_validate(record.payload)


def list_site_presentation_media_items() -> list[SitePresentationMediaItem]:
    return get_media_storage().list_items()


def get_site_presentation_summary(db: Session) -> SitePresentationAdminSummaryResponse:
    content, source = get_or_create_site_presentation_content(db)
    record = get_site_presentation_record(db)

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_clients = db.query(func.count(User.id)).filter(User.role == UserRole.client).scalar() or 0
    total_sellers = db.query(func.count(User.id)).filter(User.role == UserRole.seller).scalar() or 0
    total_admins_support = (
        db.query(func.count(User.id))
        .filter(User.role.in_([UserRole.admin, UserRole.support]))
        .scalar()
        or 0
    )
    active_shops = db.query(func.count(Shop.id)).filter(Shop.is_active.is_(True)).scalar() or 0
    active_products = db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0
    conversations = db.query(func.count(Conversation.id)).scalar() or 0
    open_tickets = db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "open").scalar() or 0
    open_reports = db.query(func.count(Report.id)).filter(Report.status == "open").scalar() or 0
    uploaded_images = len(list_site_presentation_media_items())

    return SitePresentationAdminSummaryResponse(
        app_name=content.app_name,
        source=source,
        current_version=content.download.latest_version.version,
        last_updated_at=record.updated_at.isoformat() if record else None,
        content_blocks={
            "hero_stats": len(content.hero.stats),
            "features": len(content.feature_items),
            "screenshots": len(content.screenshot_items),
            "download_steps": len(content.download.steps),
            "history_versions": len(content.download.history),
            "updates": len(content.updates.posts),
            "faq_items": len(content.faq.items),
            "contact_channels": len(content.contact.channels),
            "privacy_sections": len(content.privacy.sections),
            "terms_sections": len(content.terms.sections),
        },
        stats=SitePresentationSummaryStats(
            total_users=total_users,
            total_clients=total_clients,
            total_sellers=total_sellers,
            total_admins_support=total_admins_support,
            active_shops=active_shops,
            active_products=active_products,
            conversations=conversations,
            open_tickets=open_tickets,
            open_reports=open_reports,
            uploaded_images=uploaded_images,
        ),
    )


def get_site_presentation_public_summary(db: Session) -> SitePresentationPublicSummaryResponse:
    summary = get_site_presentation_summary(db)
    return SitePresentationPublicSummaryResponse(
        app_name=summary.app_name,
        current_version=summary.current_version,
        stats=[
            SitePresentationPublicStat(value=str(summary.stats.total_users), label="Utilisateurs inscrits"),
            SitePresentationPublicStat(value=str(summary.stats.active_products), label="Produits actifs"),
            SitePresentationPublicStat(value=str(summary.stats.active_shops), label="Boutiques actives"),
            SitePresentationPublicStat(value=str(summary.stats.conversations), label="Conversations lancees"),
        ],
    )
