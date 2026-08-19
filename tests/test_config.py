import unittest

from pydantic import ValidationError

from app.core.config import Settings, _parse_cors_origins


class SettingsTest(unittest.TestCase):
    def test_cors_origins_accept_csv_and_remove_trailing_slashes(self) -> None:
        self.assertEqual(
            _parse_cors_origins(
                "https://app.example.com/, http://localhost:3000/"
            ),
            ["https://app.example.com", "http://localhost:3000"],
        )

    def test_production_rejects_ephemeral_database_and_default_secret(self) -> None:
        with self.assertRaisesRegex(ValidationError, "DATABASE_URL"):
            Settings(
                _env_file=None,
                app_env="production",
                database_url="sqlite:///./temporary.db",
                jwt_secret_key="change-me-in-production",
                media_storage_backend="local",
            )

    def test_production_accepts_postgres_with_secure_secret(self) -> None:
        production_settings = Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql://backend:password@localhost:5432/tangawisa",
            jwt_secret_key="x" * 32,
            media_storage_backend="local",
        )
        self.assertTrue(production_settings.database_url.startswith("postgresql://"))


if __name__ == "__main__":
    unittest.main()
