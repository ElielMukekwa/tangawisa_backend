from argparse import ArgumentParser
from pathlib import Path
import secrets
import socket
import sys
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.exc import OperationalError


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402


EXPECTED_TABLES = [
    "users",
    "categories",
    "shops",
    "products",
    "site_contents",
]


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Test the FastAPI backend connection to Supabase PostgreSQL."
    )
    parser.add_argument(
        "--auth-smoke",
        action="store_true",
        help="Also create a temporary client account through /auth/register and test /auth/login.",
    )
    return parser


def mask_database_url(database_url: str) -> str:
    if "@" not in database_url or "://" not in database_url:
        return database_url

    scheme, rest = database_url.split("://", 1)
    credentials, host = rest.split("@", 1)
    username = credentials.split(":", 1)[0]
    return f"{scheme}://{username}:***@{host}"


def validate_supabase_database_url() -> None:
    database_url = settings.database_url
    parsed_url = urlparse(database_url)
    invalid_parts = [
        "aws-0-region",
        "aws-0-xxx",
        "postgres.xxxxx",
        "TON_MOT_DE_PASSE",
        "VOTRE_MOT_DE_PASSE",
    ]
    if any(part in database_url for part in invalid_parts):
        raise RuntimeError(
            "DATABASE_URL contient encore des valeurs d'exemple. Copie la vraie URL PostgreSQL "
            "depuis Supabase > Project Settings > Database > Connection string."
        )

    if "sb_secret_" in database_url or "sb_publishable_" in database_url:
        raise RuntimeError(
            "DATABASE_URL ne doit jamais contenir une clé Supabase API. Utilise la connection "
            "string PostgreSQL, pas la Secret key ni la Publishable key."
        )

    if parsed_url.scheme.startswith("postgresql") and not parsed_url.password:
        raise RuntimeError(
            "DATABASE_URL ne contient pas le mot de passe PostgreSQL. Le format attendu est:\n"
            "postgresql://USER:PASSWORD@HOST:PORT/postgres"
        )

    hostname = parsed_url.hostname
    if hostname:
        try:
            socket.getaddrinfo(hostname, parsed_url.port)
        except socket.gaierror as exc:
            raise RuntimeError(
                f"Impossible de résoudre le host Supabase `{hostname}`. "
                "Copie la vraie connection string depuis Supabase > Project Settings > Database. "
                "Pour Vercel, préfère `Transaction pooler`."
            ) from exc


def test_database_connection() -> None:
    validate_supabase_database_url()

    try:
        from app.database.session import SessionLocal, engine
    except ModuleNotFoundError as exc:
        if exc.name == "psycopg2":
            raise RuntimeError(
                "Le driver PostgreSQL psycopg2 n'est pas installé. Lance:\n"
                "pip install -r requirements.txt\n"
                "ou:\n"
                "pip install psycopg2-binary"
            ) from exc
        raise

    print("DATABASE_URL:", mask_database_url(settings.database_url))
    print("Database driver:", engine.url.drivername)
    print("Pool:", engine.pool.__class__.__name__)

    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "Ce script doit tester Supabase PostgreSQL, mais le backend utilise actuellement "
            f"{engine.dialect.name}. Configure DATABASE_URL avec l'URL PostgreSQL Supabase."
        )

    with engine.connect() as connection:
        result = connection.execute(text("select 1")).scalar_one()
        print("SQL SELECT 1:", result)

    with SessionLocal() as db:
        table_rows = db.execute(
            text(
                "select table_name from information_schema.tables "
                "where table_schema = 'public' order by table_name"
            )
        ).scalars()
        tables = set(table_rows)

    missing_tables = [table for table in EXPECTED_TABLES if table not in tables]
    if missing_tables:
        raise RuntimeError(
            "Tables manquantes dans Supabase: "
            + ", ".join(missing_tables)
            + ". Lance scripts/supabase_schema.sql dans Supabase SQL Editor."
        )

    print("Tables Supabase:", "ok")


def test_fastapi_health() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    response.raise_for_status()
    print("FastAPI /health:", response.status_code, response.json())

    response = client.get("/health/ready")
    response.raise_for_status()
    print("FastAPI /health/ready:", response.status_code, response.json())

    response = client.get(f"{settings.api_v1_prefix}/system/info")
    response.raise_for_status()
    print("FastAPI /system/info:", response.status_code, response.json())


def test_auth_smoke() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    suffix = secrets.token_hex(4)
    password = f"Smoke-{suffix}-123"
    email = f"smoke-{suffix}@example.com"
    payload = {
        "full_name": "Smoke Supabase",
        "email": email,
        "password": password,
        "role": "client",
    }

    try:
        register_response = client.post(f"{settings.api_v1_prefix}/auth/register", json=payload)
        register_response.raise_for_status()
        print("FastAPI /auth/register:", register_response.status_code, email)

        login_response = client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": email, "password": password},
        )
        login_response.raise_for_status()
        has_token = bool(login_response.json().get("access_token"))
        print("FastAPI /auth/login:", login_response.status_code, f"token={has_token}")
    finally:
        from app.database.session import SessionLocal
        from app.models.user import User

        with SessionLocal() as db:
            db.query(User).filter(User.email == email).delete(synchronize_session=False)
            db.commit()
        print("Compte smoke Supabase supprime:", email)


def main() -> None:
    args = build_parser().parse_args()
    try:
        test_database_connection()
        test_fastapi_health()
        if args.auth_smoke:
            test_auth_smoke()
        print("Connexion Supabase + FastAPI: OK")
    except OperationalError as exc:
        print("Erreur: connexion PostgreSQL impossible.")
        print("Détail:", exc.orig)
        error_detail = str(exc.orig)
        if "tenant/user" in error_detail and "not found" in error_detail:
            print(
                "Cause probable: l'URL pooler a été devinée ou la région est incorrecte. "
                "Copie toute la connection string `Transaction pooler` depuis Supabase."
            )
        print("Vérifie DATABASE_URL, le mot de passe PostgreSQL et le pooler Supabase.")
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"Erreur: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
