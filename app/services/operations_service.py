from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.conversation import Conversation
from app.models.favorite import Favorite
from app.models.message import Message
from app.models.product import Product
from app.models.shop import Shop
from app.models.site_content import SiteContent
from app.models.user import User, UserRole
from app.schemas.operations import (
    ActivityItemResponse,
    AdminDashboardResponse,
    AdminReportDetailResponse,
    AdminReportsResponse,
    AdminSupportOverviewResponse,
    AdminUpdateUserStatusRequest,
    AdminUserDetailResponse,
    AdminUserRecordResponse,
    AdminUsersResponse,
    ClientActivityResponse,
    ClientDashboardResponse,
    ClientFavoriteResponse,
    ClientProfileUpdateRequest,
    ClientNotificationResponse,
    ReportRecordResponse,
    SupportDashboardResponse,
    SupportTicketDetailResponse,
    SupportReportsResponse,
    SupportTicketResponse,
    SupportTicketsResponse,
    SupportUpdateReportRequest,
    SupportUpdateTicketRequest,
)
from app.services.marketplace_service import MarketplaceService

OPERATIONS_KEY = "operations_center"


def _default_operations_payload() -> dict:
    return {
        "reports": [
            {
                "id": "report-1",
                "title": "Produit potentiellement trompeur",
                "target_type": "product",
                "target_label": "Casque Aura V2",
                "reporter_name": "Jean-Pierre Kabasele",
                "status": "pending",
                "priority": "high",
                "created_label": "Aujourd hui",
                "reason": "Le prix annonce et les details du produit ne semblent pas coherents.",
                "support_comment": "",
                "product_id": "shop-urban-tech-casque-aura-v2",
                "shop_id": None,
                "user_id": None,
            },
            {
                "id": "report-2",
                "title": "Boutique a verifier",
                "target_type": "shop",
                "target_label": "Karibu Sneakers",
                "reporter_name": "Mireille Tshiama",
                "status": "in_review",
                "priority": "medium",
                "created_label": "Hier",
                "reason": "Le delai de reponse du vendeur reste trop long sur plusieurs conversations.",
                "support_comment": "",
                "product_id": None,
                "shop_id": "shop-karibu-sneakers",
                "user_id": None,
            },
            {
                "id": "report-3",
                "title": "Utilisateur signale pour spam",
                "target_type": "user",
                "target_label": "Blaise Masudi",
                "reporter_name": "Support Tangawisa",
                "status": "pending",
                "priority": "high",
                "created_label": "Hier",
                "reason": "Envois repetes de messages non sollicites a plusieurs vendeurs.",
                "support_comment": "",
                "product_id": None,
                "shop_id": None,
                "user_id": "8",
            },
        ],
        "tickets": [
            {
                "id": "ticket-1",
                "subject": "Compte client bloque apres connexion",
                "customer_name": "Jean-Pierre Kabasele",
                "requester_role": "client",
                "status": "new_ticket",
                "priority": "high",
                "created_label": "Aujourd hui",
                "last_message": "Je n arrive plus a acceder a mes conversations.",
                "assigned_agent": "Sarah Ilunga",
                "history": [
                    "Client: Je n arrive plus a acceder a mes conversations."
                ],
                "product_id": None,
                "shop_id": None,
            },
            {
                "id": "ticket-2",
                "subject": "Annonce refusee sans detail",
                "customer_name": "Amani Nsimba",
                "requester_role": "seller",
                "status": "in_progress",
                "priority": "medium",
                "created_label": "Aujourd hui",
                "last_message": "Le support analyse la derniere modification produit.",
                "assigned_agent": "Sarah Ilunga",
                "history": [
                    "Vendeur: Mon annonce n apparait plus dans la boutique.",
                    "Support: Nous verifions le statut du produit et son historique."
                ],
                "product_id": "shop-amani-couture-robe-amani-classic",
                "shop_id": None,
            },
            {
                "id": "ticket-3",
                "subject": "Conversation introuvable apres signalement",
                "customer_name": "Kevin Bahati",
                "requester_role": "seller",
                "status": "escalated",
                "priority": "high",
                "created_label": "Hier",
                "last_message": "Cas escalade a l administrateur pour verification.",
                "assigned_agent": "Sarah Ilunga",
                "history": [
                    "Vendeur: Une conversation a disparu apres moderation.",
                    "Support: Ticket escalade vers admin pour audit."
                ],
                "product_id": None,
                "shop_id": "shop-kivu-mobile",
            },
        ],
        "activities": [
            {
                "title": "Nouveau ticket support prioritaire",
                "subtitle": "Compte client bloque apres connexion",
                "time_label": "Il y a 12 min",
                "icon": "support_agent"
            },
            {
                "title": "Signalement produit a moderer",
                "subtitle": "Casque Aura V2 attend une verification",
                "time_label": "Il y a 27 min",
                "icon": "flag"
            },
            {
                "title": "Boutique vendeur recemment validee",
                "subtitle": "Maison Amani Couture a ete reconfirmee",
                "time_label": "Aujourd hui",
                "icon": "verified"
            },
        ],
    }


class OperationsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.marketplace = MarketplaceService(db)

    def admin_dashboard(self) -> AdminDashboardResponse:
        users = self._user_records()
        reports = self._reports()
        tickets = self._tickets()
        activities = self._activities()
        return AdminDashboardResponse(
            users=users,
            reports=reports,
            tickets=tickets,
            activities=activities,
            total_users=len(users),
            active_sellers=sum(1 for user in users if user.role == UserRole.seller and user.is_active),
            open_reports=sum(1 for report in reports if report.status != "resolved"),
            open_tickets=sum(1 for ticket in tickets if ticket.status not in {"resolved"}),
        )

    def admin_users(self) -> AdminUsersResponse:
        return AdminUsersResponse(users=self._user_records())

    def admin_user_detail(self, user_id: int) -> AdminUserDetailResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("Utilisateur introuvable.")
        shop = self.db.query(Shop).filter(Shop.owner_id == user.id).first()
        conversations_count = self.db.query(Conversation).filter(
            (Conversation.client_id == user.id) | (Conversation.seller_id == user.id)
        ).count()
        messages_count = self.db.query(Message).filter(Message.sender_id == user.id).count()
        recent_products = []
        if shop is not None:
            products = (
                self.db.query(Product)
                .filter(Product.shop_id == shop.id, Product.is_active.is_(True))
                .order_by(Product.id.desc())
                .limit(6)
                .all()
            )
            recent_products = [self.marketplace._product_to_schema(product) for product in products]
        return AdminUserDetailResponse(
            user=self._user_record(user),
            conversations_count=conversations_count,
            messages_count=messages_count,
            linked_shop=self.marketplace._shop_to_schema(shop) if shop is not None else None,
            recent_products=recent_products,
        )

    def update_user_status(self, user_id: int, payload: AdminUpdateUserStatusRequest) -> AdminUserRecordResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("Utilisateur introuvable.")
        user.is_active = payload.is_active
        self.db.commit()
        self.db.refresh(user)
        return self._user_record(user)

    def admin_reports(self) -> AdminReportsResponse:
        return AdminReportsResponse(reports=self._reports())

    def admin_report_detail(self, report_id: str) -> AdminReportDetailResponse:
        report = next((item for item in self._reports() if item.id == report_id), None)
        if report is None:
            raise ValueError("Signalement introuvable.")
        product = None
        shop = None
        user = None
        catalog = self.marketplace.catalog()
        if report.product_id:
            product = next((item for item in catalog.products if item.id == report.product_id), None)
        if report.shop_id:
            shop = next((item for item in catalog.shops if item.id == report.shop_id), None)
        if report.user_id:
            db_user = self.db.query(User).filter(User.id == int(report.user_id)).first()
            if db_user is not None:
                user = self._user_record(db_user)
        return AdminReportDetailResponse(
            report=report,
            product=product,
            shop=shop,
            user=user,
        )

    def admin_support_overview(self) -> AdminSupportOverviewResponse:
        tickets = self._tickets()
        reports = self._reports()
        return AdminSupportOverviewResponse(
            tickets=tickets,
            activities=self._activities(),
            unresolved_reports=sum(1 for report in reports if report.status != "resolved"),
            escalated_tickets=sum(1 for ticket in tickets if ticket.status == "escalated"),
        )

    def support_dashboard(self) -> SupportDashboardResponse:
        tickets = self._tickets()
        reports = self._reports()
        return SupportDashboardResponse(
            tickets=tickets,
            reports=reports,
            activities=self._activities(),
            open_tickets=sum(1 for ticket in tickets if ticket.status not in {"resolved"}),
            escalated_tickets=sum(1 for ticket in tickets if ticket.status == "escalated"),
            pending_reports=sum(1 for report in reports if report.status in {"pending", "in_review"}),
        )

    def support_tickets(self) -> SupportTicketsResponse:
        return SupportTicketsResponse(tickets=self._tickets())

    def support_ticket_detail(self, ticket_id: str) -> SupportTicketDetailResponse:
        ticket = next((item for item in self._tickets() if item.id == ticket_id), None)
        if ticket is None:
            raise ValueError("Ticket introuvable.")
        catalog = self.marketplace.catalog()
        product = None
        shop = None
        if ticket.product_id:
            product = next((item for item in catalog.products if item.id == ticket.product_id), None)
        if ticket.shop_id:
            shop = next((item for item in catalog.shops if item.id == ticket.shop_id), None)
        user = next(
            (
                record
                for record in self._user_records()
                if record.full_name.lower() == ticket.customer_name.lower()
            ),
            None,
        )
        return SupportTicketDetailResponse(
            ticket=ticket,
            product=product,
            shop=shop,
            user=user,
        )

    def update_ticket(self, ticket_id: str, payload: SupportUpdateTicketRequest) -> SupportTicketResponse:
        record = self._record()
        tickets = record.payload.get("tickets", [])
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["status"] = payload.status
                ticket["priority"] = payload.priority
                if payload.assigned_agent:
                    ticket["assigned_agent"] = payload.assigned_agent
                if payload.note:
                    ticket.setdefault("history", []).append(f"Support: {payload.note}")
                    ticket["last_message"] = payload.note
                flag_modified(record, "payload")
                self.db.commit()
                self.db.refresh(record)
                return SupportTicketResponse.model_validate(ticket)
        raise ValueError("Ticket introuvable.")

    def support_reports(self) -> SupportReportsResponse:
        return SupportReportsResponse(reports=self._reports())

    def update_report(self, report_id: str, payload: SupportUpdateReportRequest) -> ReportRecordResponse:
        record = self._record()
        reports = record.payload.get("reports", [])
        for report in reports:
            if report["id"] == report_id:
                report["status"] = payload.status
                if payload.support_comment is not None:
                    report["support_comment"] = payload.support_comment
                flag_modified(record, "payload")
                self.db.commit()
                self.db.refresh(record)
                return ReportRecordResponse.model_validate(report)
        raise ValueError("Signalement introuvable.")

    def client_dashboard(self, current_user: User) -> ClientDashboardResponse:
        conversations = self.marketplace.conversations_for_user(current_user).conversations
        favorite_products = self._favorite_products(current_user)
        recommended_shops = self.marketplace.catalog().top_shops[:3]
        activities = [
            ClientActivityResponse(
                title="Demande en discussion",
                subtitle=conversations[0].last_message if conversations else "Aucune conversation recente.",
                status="Discussion",
                icon="chat",
                tint="#B45309",
            ),
            ClientActivityResponse(
                title="Profil client actif",
                subtitle="Votre compte est synchronise avec le backend.",
                status="Actif",
                icon="person",
                tint="#0284C7",
            ),
        ]
        notifications = [
            ClientNotificationResponse(
                title="Nouveau message",
                subtitle=conversations[0].name if conversations else "Aucune nouvelle conversation.",
                icon="chat",
            ),
            ClientNotificationResponse(
                title="Favoris disponibles",
                subtitle=f"{len(favorite_products)} produits en favoris pour le moment.",
                icon="favorite",
            ),
        ]
        return ClientDashboardResponse(
            full_name=current_user.full_name,
            email=current_user.email,
            phone_number=current_user.phone_number,
            favorite_count=len(favorite_products),
            unread_notifications=sum(item.unread_count for item in conversations),
            conversations=conversations,
            favorite_products=favorite_products,
            recommended_shops=recommended_shops,
            activities=activities,
            notifications=notifications,
        )

    def add_favorite(self, current_user: User, product_id: str) -> ClientFavoriteResponse:
        product = self.marketplace.find_product_by_public_id(product_id)
        if product is None or not product.is_active:
            raise ValueError("Produit introuvable.")
        favorite = self.db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product.id,
        ).first()
        if favorite is None:
            self.db.add(Favorite(user_id=current_user.id, product_id=product.id))
            self.db.commit()
        return ClientFavoriteResponse(
            product_id=product_id,
            is_favorite=True,
            favorite_count=self._favorite_count(current_user),
        )

    def update_client_profile(
        self,
        current_user: User,
        payload: ClientProfileUpdateRequest,
    ) -> ClientDashboardResponse:
        current_user.full_name = payload.full_name.strip()
        current_user.phone_number = payload.phone_number.strip() if payload.phone_number else None
        self.db.commit()
        self.db.refresh(current_user)
        return self.client_dashboard(current_user)

    def remove_favorite(self, current_user: User, product_id: str) -> ClientFavoriteResponse:
        product = self.marketplace.find_product_by_public_id(product_id)
        if product is None:
            raise ValueError("Produit introuvable.")
        favorite = self.db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product.id,
        ).first()
        if favorite is not None:
            self.db.delete(favorite)
            self.db.commit()
        return ClientFavoriteResponse(
            product_id=product_id,
            is_favorite=False,
            favorite_count=self._favorite_count(current_user),
        )

    def _record(self) -> SiteContent:
        record = self.db.query(SiteContent).filter(SiteContent.site_key == OPERATIONS_KEY).first()
        if record is not None:
            return record
        record = SiteContent(site_key=OPERATIONS_KEY, payload=_default_operations_payload())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _reports(self) -> list[ReportRecordResponse]:
        return [ReportRecordResponse.model_validate(item) for item in self._record().payload.get("reports", [])]

    def _tickets(self) -> list[SupportTicketResponse]:
        return [SupportTicketResponse.model_validate(item) for item in self._record().payload.get("tickets", [])]

    def _activities(self) -> list[ActivityItemResponse]:
        return [ActivityItemResponse.model_validate(item) for item in self._record().payload.get("activities", [])]

    def _user_records(self) -> list[AdminUserRecordResponse]:
        users = self.db.query(User).order_by(User.id).all()
        return [self._user_record(user) for user in users]

    def _user_record(self, user: User) -> AdminUserRecordResponse:
        shop = self.db.query(Shop).filter(Shop.owner_id == user.id).first()
        conversation_count = (
            self.db.query(Conversation).filter(
                (Conversation.client_id == user.id) | (Conversation.seller_id == user.id)
            ).count()
        )
        last_message = (
            self.db.query(Message).filter(Message.sender_id == user.id).order_by(Message.id.desc()).first()
        )
        return AdminUserRecordResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            city=shop.city if shop and shop.city else "Kinshasa",
            is_active=user.is_active,
            last_activity=(
                f"{conversation_count} conversations actives"
                if conversation_count
                else (last_message.body[:48] if last_message and last_message.body else "Activite recente indisponible")
            ),
            linked_shop_name=shop.name if shop else None,
        )

    def _favorite_products(self, current_user: User):
        favorites = (
            self.db.query(Favorite)
            .filter(Favorite.user_id == current_user.id)
            .order_by(Favorite.id.desc())
            .all()
        )
        products: list = []
        for favorite in favorites:
            product = self.db.query(Product).filter(Product.id == favorite.product_id).first()
            if product is not None:
                shop = self.db.query(Shop).filter(Shop.id == product.shop_id).first()
                if shop is not None:
                    products.append(self.marketplace._product_to_schema(product))
        return products[:6]

    def _favorite_count(self, current_user: User) -> int:
        return self.db.query(Favorite).filter(Favorite.user_id == current_user.id).count()
