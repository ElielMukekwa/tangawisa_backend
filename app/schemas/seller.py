from pydantic import BaseModel, Field

from app.schemas.marketplace import MarketplaceConversation, MarketplaceProduct, MarketplaceShop


class SellerNotification(BaseModel):
    id: str
    title: str
    message: str
    time_label: str
    icon: str


class SellerFeedItem(BaseModel):
    id: str
    title: str
    subtitle: str
    message: str
    image_url: str
    time_label: str
    badge: str
    kind: str
    target_product_id: str | None = None
    target_shop_id: str | None = None


class SellerInventoryItem(BaseModel):
    id: str
    product: MarketplaceProduct
    status: str
    created_label: str
    secondary_label: str
    secondary_icon: str


class SellerDashboardResponse(BaseModel):
    shop: MarketplaceShop
    inventory: list[SellerInventoryItem]
    conversations: list[MarketplaceConversation]
    monthly_views: int
    conversion_label: str
    unread_messages: int
    featured_products: int


class SellerProductsResponse(BaseModel):
    shop: MarketplaceShop
    inventory: list[SellerInventoryItem]


class SellerNotificationsResponse(BaseModel):
    notifications: list[SellerNotification]


class SellerFeedResponse(BaseModel):
    feed_items: list[SellerFeedItem]


class SellerProductUpsertRequest(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    category: str = Field(min_length=2, max_length=80)
    price_label: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=12, max_length=1000)
    image_url: str = Field(min_length=5, max_length=255)
    status: str = Field(default="on_sale")
    is_featured: bool = True

