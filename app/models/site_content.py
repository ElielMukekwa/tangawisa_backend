from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class SiteContent(Base, TimestampMixin):
    __tablename__ = "site_contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    site_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
