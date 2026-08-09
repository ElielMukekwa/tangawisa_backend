import unittest

from fastapi.testclient import TestClient

from app.main import app


class LocalIntegrationSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _login(self, email: str, password: str) -> str:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def _authenticated_get(self, path: str, token: str) -> None:
        response = self.client.get(
            path,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_public_surfaces_and_catalog(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/presentation/").status_code, 200)
        self.assertEqual(self.client.get("/static/admin/login.html").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/marketplace/catalog").status_code, 200)

    def test_role_dashboards(self) -> None:
        accounts = [
            ("client@tangawisa.app", "secret123", "/api/v1/client/dashboard"),
            ("vendeur@tangawisa.app", "secret123", "/api/v1/seller/dashboard"),
            ("admin@tangawisa.app", "12345678", "/api/v1/admin/dashboard"),
            ("support@tangawisa.app", "secret123", "/api/v1/support/dashboard"),
        ]
        for email, password, dashboard in accounts:
            with self.subTest(email=email):
                self._authenticated_get(dashboard, self._login(email, password))


if __name__ == "__main__":
    unittest.main()
