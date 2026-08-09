import re

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.shop import Shop
from app.models.user import User
from app.schemas.marketplace import MarketplaceConversation, MarketplaceProduct, MarketplaceShop
from app.schemas.seller import (
    SellerDashboardResponse,
    SellerFeedItem,
    SellerFeedResponse,
    SellerInventoryItem,
    SellerNotificationsResponse,
    SellerNotification,
    SellerProductUpsertRequest,
    SellerProductsResponse,
)
from app.services.marketplace_service import MarketplaceService
from app.utils.slugs import slugify


class SellerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.marketplace = MarketplaceService(db)

    def dashboard(self, current_user: User) -> SellerDashboardResponse:
        shop = self._get_shop(current_user)
        inventory = self._inventory_for_shop(shop)
        conversations = self.marketplace.conversations_for_user(current_user).conversations
        featured_products = sum(1 for item in inventory if item.product.is_featured)
        unread_messages = sum(item.unread_count for item in conversations)
        monthly_views = sum(self._views_from_label(item.secondary_label) for item in inventory)

        return SellerDashboardResponse(
            shop=self._shop_to_schema(shop),
            inventory=inventory,
            conversations=conversations,
            monthly_views=monthly_views,
            conversion_label=f"{len(conversations)} discussions actives",
            unread_messages=unread_messages,
            featured_products=featured_products,
        )

    def products(self, current_user: User) -> SellerProductsResponse:
        shop = self._get_shop(current_user)
        return SellerProductsResponse(
            shop=self._shop_to_schema(shop),
            inventory=self._inventory_for_shop(shop),
        )

    def notifications(self, current_user: User) -> SellerNotificationsResponse:
        shop = self._get_shop(current_user)
        inventory = self._inventory_for_shop(shop)
        latest_name = inventory[0].product.name if inventory else "votre article"
        return SellerNotificationsResponse(
            notifications=[
                SellerNotification(
                    id="notif-published",
                    title="Nouvelle annonce publiee",
                    message=f"{latest_name} est maintenant visible pour les clients.",
                    time_label="A l instant",
                    icon="campaign",
                ),
                SellerNotification(
                    id="notif-catalog",
                    title="Catalogue actualise",
                    message=f"{len(inventory)} articles sont actuellement lies a {shop.name}.",
                    time_label="Aujourd hui",
                    icon="edit",
                ),
                SellerNotification(
                    id="notif-chat",
                    title="Conversations a suivre",
                    message="Votre messagerie vendeur est synchronisee avec le backend.",
                    time_label="Aujourd hui",
                    icon="chat",
                ),
            ]
        )

    def feed(self, current_user: User) -> SellerFeedResponse:
        shop = self._get_shop(current_user)
        inventory = self._inventory_for_shop(shop)
        top_product = inventory[0].product if inventory else None
        feed_items: list[SellerFeedItem] = []
        if top_product is not None:
            feed_items.append(
                SellerFeedItem(
                    id="feed-product-highlight",
                    title=top_product.name,
                    subtitle=shop.name,
                    message=f"Produit visible dans la categorie {top_product.category} avec {top_product.price_label}.",
                    image_url=top_product.image_url,
                    time_label="A l instant",
                    badge="Produit",
                    kind="product",
                    target_product_id=top_product.id,
                    target_shop_id=shop.slug,
                )
            )
        feed_items.append(
            SellerFeedItem(
                id="feed-shop",
                title=shop.name,
                subtitle="Boutique vendeur",
                message=f"{len(inventory)} articles actifs et messagerie synchronisee.",
                image_url=shop.banner_url or shop.logo_url or "",
                time_label="Aujourd hui",
                badge="Boutique",
                kind="shop",
                target_shop_id=shop.slug,
            )
        )
        return SellerFeedResponse(feed_items=feed_items)

    def create_product(self, current_user: User, payload: SellerProductUpsertRequest) -> SellerInventoryItem:
        shop = self._get_shop(current_user)
        category = self._get_or_create_category(payload.category)
        product = Product(
            shop_id=shop.id,
            category_id=category.id,
            name=payload.name.strip(),
            description=payload.description.strip(),
            price_hint=self._parse_price(payload.price_label),
            is_active=payload.status != "draft",
            stock_quantity=1 if payload.status != "sold" else 0,
            is_featured=payload.is_featured,
            is_new_arrival=True,
        )
        self.db.add(product)
        self.db.flush()
        self.db.add(
            ProductImage(
                product_id=product.id,
                image_url=payload.image_url.strip(),
                display_order=0,
            )
        )
        self.db.commit()
        self.db.refresh(product)
        return self._inventory_item(product, shop, payload.image_url, payload.status, created_label="A l instant")

    def update_product(
        self,
        current_user: User,
        product_slug: str,
        payload: SellerProductUpsertRequest,
    ) -> SellerInventoryItem:
        shop = self._get_shop(current_user)
        product = self._find_shop_product(shop, product_slug)
        if product is None:
            raise ValueError("Produit vendeur introuvable.")

        category = self._get_or_create_category(payload.category)
        product.name = payload.name.strip()
        product.category_id = category.id
        product.description = payload.description.strip()
        product.price_hint = self._parse_price(payload.price_label)
        product.is_active = payload.status != "draft"
        product.stock_quantity = 0 if payload.status == "sold" else max(product.stock_quantity, 1)
        product.is_featured = payload.is_featured
        image = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == product.id)
            .order_by(ProductImage.display_order, ProductImage.id)
            .first()
        )
        if image is None:
            self.db.add(
                ProductImage(
                    product_id=product.id,
                    image_url=payload.image_url.strip(),
                    display_order=0,
                )
            )
        else:
            image.image_url = payload.image_url.strip()
        self.db.commit()
        self.db.refresh(product)
        return self._inventory_item(product, shop, payload.image_url, payload.status, created_label="Mis a jour")

    def _get_shop(self, current_user: User) -> Shop:
        shops = self.db.query(Shop).filter(Shop.owner_id == current_user.id).order_by(Shop.id).all()
        shop = next((item for item in shops if item.slug == "shop-amani-couture"), None)
        if shop is None and shops:
            shop = shops[0]
        if shop is None:
            raise ValueError("Aucune boutique n est associee a ce vendeur.")
        return shop

    def _get_or_create_category(self, category_name: str) -> Category:
        normalized = category_name.strip()
        category = self.db.query(Category).filter(Category.name == normalized).first()
        if category is not None:
            return category
        slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "categorie"
        category = Category(name=normalized, slug=slug, description=f"Categorie {normalized}")
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def _find_shop_product(self, shop: Shop, product_slug: str) -> Product | None:
        products = self.db.query(Product).filter(Product.shop_id == shop.id).all()
        for product in products:
            if self._product_public_id(shop, product) == product_slug:
                return product
        return None

    def _inventory_for_shop(self, shop: Shop) -> list[SellerInventoryItem]:
        products = self.db.query(Product).filter(Product.shop_id == shop.id).order_by(Product.id.desc()).all()
        return [self._inventory_item(product, shop) for product in products]

    def _inventory_item(
        self,
        product: Product,
        shop: Shop,
        image_url: str | None = None,
        forced_status: str | None = None,
        created_label: str | None = None,
    ) -> SellerInventoryItem:
        status = forced_status or self._infer_status(product)
        marketplace_product = self._product_to_schema(product, shop, image_url_override=image_url)
        secondary_label = (
            "Vendu recemment"
            if status == "sold"
            else f"{max(12, int((product.price_hint or 0) / 100))} vues"
        )
        secondary_icon = "sold" if status == "sold" else "views"
        return SellerInventoryItem(
            id=f"inventory-{self._product_public_id(shop, product)}",
            product=marketplace_product,
            status=status,
            created_label=created_label or "Aujourd hui",
            secondary_label=secondary_label,
            secondary_icon=secondary_icon,
        )

    def _shop_to_schema(self, shop: Shop) -> MarketplaceShop:
        return self.marketplace._shop_to_schema(shop)

    def _product_to_schema(
        self,
        product: Product,
        shop: Shop,
        image_url_override: str | None = None,
    ) -> MarketplaceProduct:
        category = self.db.query(Category).filter(Category.id == product.category_id).first()
        stored_image = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == product.id)
            .order_by(ProductImage.display_order, ProductImage.id)
            .first()
        )
        image_url = (
            image_url_override
            or (stored_image.image_url if stored_image else None)
            or shop.banner_url
            or shop.logo_url
            or ""
        )
        return MarketplaceProduct(
            id=self._product_public_id(shop, product),
            shop_id=shop.slug,
            shop_name=shop.name,
            name=product.name,
            category=category.name if category else "Categorie",
            price_label=f"{int(product.price_hint or 0)} FC" if product.price_hint else "Prix discutable",
            rating=4.8 if product.name.lower().startswith("robe") else 4.6,
            image_url=image_url,
            description=product.description or "",
            is_featured=product.is_featured,
            is_new_arrival=product.is_new_arrival,
        )

    def _product_public_id(self, shop: Shop, product: Product) -> str:
        return f"{shop.slug}-{slugify(product.name)}"

    def _infer_status(self, product: Product) -> str:
        if product.stock_quantity <= 0:
            return "sold"
        if not product.is_active:
            return "draft"
        return "on_sale"

    def _views_from_label(self, label: str) -> int:
        digits = re.sub(r"[^0-9]", "", label)
        return int(digits) if digits else 0

    def _parse_price(self, price_label: str) -> float | None:
        digits = re.sub(r"[^0-9]", "", price_label)
        return float(digits) if digits else None
