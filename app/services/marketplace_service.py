from datetime import datetime

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.conversation import Conversation
from app.models.message import Message, MessageStatus, MessageType
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.shop import Shop
from app.models.user import User, UserRole
from app.schemas.marketplace import (
    MarketplaceCatalogResponse,
    MarketplaceConversation,
    MarketplaceConversationsResponse,
    MarketplaceMessage,
    MarketplaceProductDetailResponse,
    MarketplaceProduct,
    MarketplaceShopDetailResponse,
    MarketplaceShop,
)
from app.utils.slugs import slugify


class MarketplaceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def catalog(self) -> MarketplaceCatalogResponse:
        shops = self.db.query(Shop).filter(Shop.is_active.is_(True)).all()
        products = self.db.query(Product).filter(Product.is_active.is_(True)).all()
        categories = ["Tout", *[item.name for item in self.db.query(Category).order_by(Category.name).all()]]

        shop_payloads = [self._shop_to_schema(shop) for shop in shops]
        product_payloads = [self._product_to_schema(product) for product in products]

        featured = [item for item in product_payloads if item.is_featured]
        arrivals = [item for item in product_payloads if item.is_new_arrival]
        top_shops = sorted(shop_payloads, key=lambda shop: shop.rating, reverse=True)

        return MarketplaceCatalogResponse(
            categories=categories,
            shops=shop_payloads,
            products=product_payloads,
            featured_products=featured,
            new_arrivals=arrivals,
            top_shops=top_shops,
        )

    def conversations_for_user(self, current_user: User) -> MarketplaceConversationsResponse:
        query = self.db.query(Conversation)
        if current_user.role == UserRole.client:
            conversations = query.filter(Conversation.client_id == current_user.id).all()
        else:
            conversations = query.filter(Conversation.seller_id == current_user.id).all()

        payloads = [self._conversation_to_schema(item, current_user) for item in conversations]
        return MarketplaceConversationsResponse(conversations=payloads)

    def product_detail(self, product_id: str) -> MarketplaceProductDetailResponse:
        catalog = self.catalog()
        product = next((item for item in catalog.products if item.id == product_id), None)
        if product is None:
            raise ValueError("Produit introuvable.")
        shop = next((item for item in catalog.shops if item.id == product.shop_id), None)
        if shop is None:
            raise ValueError("Boutique introuvable.")
        related_products = [
            item
            for item in catalog.products
            if item.shop_id == product.shop_id and item.id != product.id
        ][:6]
        return MarketplaceProductDetailResponse(
            product=product,
            shop=shop,
            related_products=related_products,
        )

    def find_product_by_public_id(self, product_id: str) -> Product | None:
        for product, shop in self.db.query(Product, Shop).join(Shop, Shop.id == Product.shop_id).all():
            if f"{shop.slug}-{slugify(product.name)}" == product_id:
                return product
        return None

    def shop_detail(self, shop_id: str) -> MarketplaceShopDetailResponse:
        catalog = self.catalog()
        shop = next((item for item in catalog.shops if item.id == shop_id), None)
        if shop is None:
            raise ValueError("Boutique introuvable.")
        products = [item for item in catalog.products if item.shop_id == shop_id][:12]
        return MarketplaceShopDetailResponse(shop=shop, products=products)

    def get_or_create_conversation(self, current_user: User, shop_slug: str) -> MarketplaceConversation:
        if current_user.role != UserRole.client:
            raise ValueError("Seul un client peut demarrer une conversation depuis une boutique.")

        shop = self.db.query(Shop).filter(Shop.slug == shop_slug, Shop.is_active.is_(True)).first()
        if shop is None:
            raise ValueError("Boutique introuvable.")

        seller_id = shop.owner_id
        conversation = self.db.query(Conversation).filter(
            Conversation.client_id == current_user.id,
            Conversation.seller_id == seller_id,
            Conversation.shop_id == shop.id,
        ).first()

        if conversation is None:
            conversation = Conversation(
                client_id=current_user.id,
                seller_id=seller_id,
                shop_id=shop.id,
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        return self._conversation_to_schema(conversation, current_user)

    def send_message(
        self,
        current_user: User,
        conversation_id: int,
        text: str,
        media_url: str | None = None,
        reply_to_message_id: str | None = None,
        reply_to_preview: str | None = None,
    ) -> MarketplaceConversation:
        conversation = self._get_user_conversation(current_user, conversation_id)
        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            message_type=MessageType.text,
            body=text.strip(),
            media_url=media_url,
            reply_to_message_id=reply_to_message_id,
            reply_to_preview=reply_to_preview,
            status=MessageStatus.sent,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return self._conversation_to_schema(conversation, current_user)

    def mark_conversation_read(self, current_user: User, conversation_id: int) -> MarketplaceConversation:
        conversation = self._get_user_conversation(current_user, conversation_id)
        partner_id = conversation.seller_id if current_user.role == UserRole.client else conversation.client_id
        self.db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.sender_id == partner_id,
            Message.status != MessageStatus.read,
        ).update({Message.status: MessageStatus.read}, synchronize_session=False)
        self.db.commit()
        return self._conversation_to_schema(conversation, current_user)

    def _get_user_conversation(self, current_user: User, conversation_id: int) -> Conversation:
        query = self.db.query(Conversation).filter(Conversation.id == conversation_id)
        if current_user.role == UserRole.client:
            query = query.filter(Conversation.client_id == current_user.id)
        else:
            query = query.filter(Conversation.seller_id == current_user.id)
        conversation = query.first()
        if conversation is None:
            raise ValueError("Conversation introuvable.")
        return conversation

    def _shop_to_schema(self, shop: Shop) -> MarketplaceShop:
        product_count = self.db.query(Product).filter(Product.shop_id == shop.id, Product.is_active.is_(True)).count()
        category_names = [category.name for category in self.db.query(Category).join(Product, Product.category_id == Category.id).filter(Product.shop_id == shop.id).distinct()]
        category = category_names[0] if category_names else "Boutique"
        rating = {
            "shop-kivu-mobile": 4.8,
            "shop-amani-couture": 4.9,
            "shop-zuri-artistry": 4.9,
            "shop-saveurs-fleuve": 4.8,
        }.get(shop.slug, 4.7)
        sales_label = {
            "shop-kivu-mobile": "1,8 k ventes",
            "shop-amani-couture": "1,2 k ventes",
            "shop-zuri-artistry": "1,2 k ventes",
            "shop-saveurs-fleuve": "560 ventes",
        }.get(shop.slug, f"{product_count * 100} ventes")
        tagline = {
            "shop-kivu-mobile": "Smartphones, audio et accessoires testes",
            "shop-amani-couture": "Pieces elegantes et finitions soignees",
            "shop-zuri-artistry": "Tissages, paniers et heritage visuel",
            "shop-saveurs-fleuve": "Boissons, douceurs et paniers gourmands",
        }.get(shop.slug, shop.name)
        return MarketplaceShop(
            id=shop.slug,
            name=shop.name,
            category=category,
            city=shop.city or "Kinshasa",
            tagline=tagline,
            description=shop.description or "",
            avatar_url=shop.logo_url or "",
            banner_url=shop.banner_url or "",
            sales_label=sales_label,
            rating=rating,
            product_count=product_count,
        )

    def _product_to_schema(self, product: Product) -> MarketplaceProduct:
        shop = self.db.query(Shop).filter(Shop.id == product.shop_id).first()
        category = self.db.query(Category).filter(Category.id == product.category_id).first()
        image = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == product.id)
            .order_by(ProductImage.display_order, ProductImage.id)
            .first()
        )
        return MarketplaceProduct(
            id=f"{shop.slug}-{slugify(product.name)}",
            shop_id=shop.slug,
            shop_name=shop.name,
            name=product.name,
            category=category.name if category else "Categorie",
            price_label=f"{int(product.price_hint or 0)} FC" if product.price_hint else "Prix discutable",
            rating={
                "Smartphone Nova X12": 4.8,
                "PowerBank River 20K": 4.5,
                "Robe Amani Classic": 4.9,
                "Ensemble Beige Urbain": 4.8,
                "Tissage Heritage": 4.9,
                "Pack Jus Nature": 4.8,
            }.get(product.name, 4.6),
            image_url=(image.image_url if image else None) or shop.banner_url or shop.logo_url or "",
            description=product.description or "",
            is_featured=product.is_featured,
            is_new_arrival=product.is_new_arrival,
        )

    def _conversation_to_schema(self, conversation: Conversation, current_user: User) -> MarketplaceConversation:
        shop = self.db.query(Shop).filter(Shop.id == conversation.shop_id).first()
        seller = self.db.query(User).filter(User.id == conversation.seller_id).first()
        messages = self.db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.id).all()
        last_message = messages[-1].body if messages else ""
        unread_count = sum(1 for msg in messages if msg.sender_id != current_user.id and msg.status != MessageStatus.read)
        category = self.db.query(Category).join(Product, Product.category_id == Category.id).filter(Product.shop_id == shop.id).first()

        return MarketplaceConversation(
            id=str(conversation.id),
            name="Support Tangawisa" if seller.role == UserRole.support else shop.name,
            shop_id="support" if seller.role == UserRole.support else shop.slug,
            category="Assistance" if seller.role == UserRole.support else (category.name if category else "Boutique"),
            avatar_url=shop.logo_url or "",
            last_message=last_message or "",
            unread_count=unread_count,
            time_label=self._time_label(messages[-1].created_at if messages else conversation.created_at),
            is_online=True,
            messages=[
                MarketplaceMessage(
                    id=str(message.id),
                    text=message.body or "",
                    is_mine=message.sender_id == current_user.id,
                    time_label=self._time_label(message.created_at, include_time=True),
                    media_url=message.media_url,
                    reply_to_message_id=message.reply_to_message_id,
                    reply_to_preview=message.reply_to_preview,
                )
                for message in messages
            ],
        )

    def _time_label(self, date_value: datetime, include_time: bool = False) -> str:
        if include_time:
            return date_value.strftime("%H:%M")
        return "Maintenant"
