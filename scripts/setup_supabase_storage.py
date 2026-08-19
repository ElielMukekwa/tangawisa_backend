from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402


ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE = 10 * 1024 * 1024


def _bucket_value(bucket: object, field: str) -> object | None:
    if isinstance(bucket, dict):
        return bucket.get(field)
    return getattr(bucket, field, None)


def main() -> None:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError(
            "Configure SUPABASE_URL et SUPABASE_SECRET_KEY avant de preparer Storage."
        )

    from supabase import create_client

    storage = create_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    ).storage
    bucket_name = settings.supabase_storage_bucket
    buckets = storage.list_buckets()
    existing_bucket = next(
        (bucket for bucket in buckets if _bucket_value(bucket, "name") == bucket_name),
        None,
    )
    options = {
        "public": True,
        "allowed_mime_types": ALLOWED_MIME_TYPES,
        "file_size_limit": MAX_FILE_SIZE,
    }

    if existing_bucket is None:
        storage.create_bucket(bucket_name, options=options)
        action = "created"
    else:
        storage.update_bucket(bucket_name, options=options)
        action = "updated"

    print(f"Supabase Storage bucket {action}: {bucket_name}")


if __name__ == "__main__":
    main()
