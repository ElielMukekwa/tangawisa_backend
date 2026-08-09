import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.services.dev_seed_service import seed_development_data


class WriteFlowIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        with cls.session_factory() as session:
            seed_development_data(session)

        def override_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def _token(self, email: str, password: str) -> str:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_public_registration_cannot_create_privileged_roles(self) -> None:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Faux Administrateur",
                "email": "forbidden-admin@tangawisa.app",
                "password": "secret123",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)

    def test_seller_product_fields_survive_reload(self) -> None:
        token = self._token("vendeur@tangawisa.app", "secret123")
        payload = {
            "name": "Sac Edition Locale",
            "category": "Mode",
            "price_label": "18500 FC",
            "description": "Un sac local durable cree pour les usages quotidiens.",
            "image_url": "https://example.com/sac-local.jpg",
            "status": "on_sale",
            "is_featured": True,
        }
        created = self.client.post(
            "/api/v1/seller/products",
            headers=self._headers(token),
            json=payload,
        )
        self.assertEqual(created.status_code, 201, created.text)
        product_id = created.json()["product"]["id"]

        products = self.client.get(
            "/api/v1/seller/products",
            headers=self._headers(token),
        )
        self.assertEqual(products.status_code, 200, products.text)
        reloaded = next(
            item["product"]
            for item in products.json()["inventory"]
            if item["product"]["id"] == product_id
        )
        self.assertEqual(reloaded["image_url"], payload["image_url"])
        self.assertTrue(reloaded["is_featured"])

    def test_client_favorites_are_persistent(self) -> None:
        token = self._token("client@tangawisa.app", "secret123")
        catalog = self.client.get("/api/v1/marketplace/catalog").json()
        product_id = catalog["products"][0]["id"]

        added = self.client.put(
            f"/api/v1/client/favorites/{product_id}",
            headers=self._headers(token),
        )
        self.assertEqual(added.status_code, 200, added.text)
        dashboard = self.client.get(
            "/api/v1/client/dashboard",
            headers=self._headers(token),
        ).json()
        self.assertIn(product_id, {item["id"] for item in dashboard["favorite_products"]})

        removed = self.client.delete(
            f"/api/v1/client/favorites/{product_id}",
            headers=self._headers(token),
        )
        self.assertEqual(removed.status_code, 200, removed.text)
        self.assertFalse(removed.json()["is_favorite"])

    def test_client_profile_update_is_persistent(self) -> None:
        token = self._token("client@tangawisa.app", "secret123")
        response = self.client.put(
            "/api/v1/client/profile",
            headers=self._headers(token),
            json={
                "full_name": "Jean-Pierre Kabasele Actualise",
                "phone_number": "+243 810 222 333",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["full_name"], "Jean-Pierre Kabasele Actualise")

        reloaded = self.client.get(
            "/api/v1/client/dashboard",
            headers=self._headers(token),
        )
        self.assertEqual(reloaded.status_code, 200, reloaded.text)
        self.assertEqual(reloaded.json()["phone_number"], "+243 810 222 333")

    def test_message_reply_metadata_is_persistent(self) -> None:
        token = self._token("client@tangawisa.app", "secret123")
        conversation = self.client.post(
            "/api/v1/marketplace/conversations",
            headers=self._headers(token),
            json={"shop_id": "shop-amani-couture"},
        ).json()
        replied_to = conversation["messages"][0]
        response = self.client.post(
            f"/api/v1/marketplace/conversations/{conversation['id']}/messages",
            headers=self._headers(token),
            json={
                "text": "Merci, je confirme ma demande.",
                "reply_to_message_id": replied_to["id"],
                "reply_to_preview": replied_to["text"],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        message = response.json()["messages"][-1]
        self.assertEqual(message["reply_to_message_id"], replied_to["id"])
        self.assertEqual(message["reply_to_preview"], replied_to["text"])

    def test_support_updates_survive_a_new_request(self) -> None:
        token = self._token("support@tangawisa.app", "secret123")
        updated_ticket = self.client.put(
            "/api/v1/support/tickets/ticket-1",
            headers=self._headers(token),
            json={
                "status": "in_progress",
                "priority": "medium",
                "assigned_agent": "Sarah Ilunga",
                "note": "Verification backend terminee.",
            },
        )
        self.assertEqual(updated_ticket.status_code, 200, updated_ticket.text)
        reloaded_ticket = self.client.get(
            "/api/v1/support/tickets/ticket-1",
            headers=self._headers(token),
        )
        self.assertEqual(reloaded_ticket.status_code, 200, reloaded_ticket.text)
        self.assertEqual(reloaded_ticket.json()["ticket"]["last_message"], "Verification backend terminee.")

        updated_report = self.client.put(
            "/api/v1/support/reports/report-1",
            headers=self._headers(token),
            json={"status": "resolved", "support_comment": "Cas verifie et cloture."},
        )
        self.assertEqual(updated_report.status_code, 200, updated_report.text)
        reloaded_report = self.client.get(
            "/api/v1/support/reports/report-1",
            headers=self._headers(token),
        )
        self.assertEqual(reloaded_report.json()["report"]["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
