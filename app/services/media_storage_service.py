from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.schemas.site_presentation import SitePresentationMediaItem


MEDIA_FOLDER = "site-presentation"


class MediaStorageError(RuntimeError):
    pass


class MediaStorage(Protocol):
    def upload(self, filename: str, content: bytes, content_type: str) -> str: ...

    def list_items(self) -> list[SitePresentationMediaItem]: ...


class LocalMediaStorage:
    def __init__(self) -> None:
        self.uploads_dir = (
            Path(__file__).resolve().parents[1] / "public" / "uploads" / MEDIA_FOLDER
        )

    def upload(self, filename: str, content: bytes, content_type: str) -> str:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        (self.uploads_dir / filename).write_bytes(content)
        return f"/static/uploads/{MEDIA_FOLDER}/{filename}"

    def list_items(self) -> list[SitePresentationMediaItem]:
        if not self.uploads_dir.exists():
            return []

        items: list[SitePresentationMediaItem] = []
        files = [path for path in self.uploads_dir.iterdir() if path.is_file()]
        for file_path in sorted(files, key=lambda path: path.stat().st_mtime, reverse=True):
            stat = file_path.stat()
            items.append(
                SitePresentationMediaItem(
                    filename=file_path.name,
                    url=f"/static/uploads/{MEDIA_FOLDER}/{file_path.name}",
                    size_bytes=stat.st_size,
                    created_at=str(int(stat.st_mtime)),
                )
            )
        return items


class SupabaseMediaStorage:
    def __init__(self) -> None:
        if not settings.supabase_url or not settings.supabase_secret_key:
            raise MediaStorageError(
                "SUPABASE_URL et SUPABASE_SECRET_KEY sont requis pour le stockage des medias."
            )

        from supabase import create_client

        self.bucket_name = settings.supabase_storage_bucket
        self.bucket = create_client(
            settings.supabase_url,
            settings.supabase_secret_key,
        ).storage.from_(self.bucket_name)

    def upload(self, filename: str, content: bytes, content_type: str) -> str:
        object_path = f"{MEDIA_FOLDER}/{filename}"
        try:
            self.bucket.upload(
                path=object_path,
                file=content,
                file_options={
                    "cache-control": "3600",
                    "content-type": content_type,
                    "upsert": "false",
                },
            )
            return self.bucket.get_public_url(object_path)
        except Exception as exc:
            raise MediaStorageError("Echec de l'envoi du media vers Supabase Storage.") from exc

    def list_items(self) -> list[SitePresentationMediaItem]:
        try:
            stored_items = self.bucket.list(
                MEDIA_FOLDER,
                {
                    "limit": 100,
                    "offset": 0,
                    "sortBy": {"column": "created_at", "order": "desc"},
                },
            )
        except Exception as exc:
            raise MediaStorageError("Echec de lecture des medias Supabase Storage.") from exc

        items: list[SitePresentationMediaItem] = []
        for stored_item in stored_items:
            item = (
                stored_item.model_dump(mode="json")
                if hasattr(stored_item, "model_dump")
                else dict(stored_item)
            )
            filename = str(item.get("name") or "").strip()
            if not filename:
                continue
            metadata = item.get("metadata") or {}
            items.append(
                SitePresentationMediaItem(
                    filename=filename,
                    url=self.bucket.get_public_url(f"{MEDIA_FOLDER}/{filename}"),
                    size_bytes=int(metadata.get("size") or 0),
                    created_at=str(item.get("created_at") or item.get("updated_at") or ""),
                )
            )
        return items


@lru_cache
def get_media_storage() -> MediaStorage:
    if settings.uses_supabase_storage:
        return SupabaseMediaStorage()
    return LocalMediaStorage()
