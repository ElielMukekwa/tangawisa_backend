from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class MarketplaceUser(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole


class MarketplaceShop(BaseModel):
    id: str
    name: str
    category: str
    city: str
    tagline: str
    description: str
    avatar_url: str
    banner_url: str
    sales_label: str
    rating: float
    product_count: int


class MarketplaceProduct(BaseModel):
    id: str
    shop_id: str
    shop_name: str
    name: str
    category: str
    price_label: str
    rating: float
    image_url: str
    description: str
    is_featured: bool
    is_new_arrival: bool


class MarketplaceCatalogResponse(BaseModel):
    categories: list[str]
    shops: list[MarketplaceShop]
    products: list[MarketplaceProduct]
    featured_products: list[MarketplaceProduct]
    new_arrivals: list[MarketplaceProduct]
    top_shops: list[MarketplaceShop]


class MarketplaceProductDetailResponse(BaseModel):
    product: MarketplaceProduct
    shop: MarketplaceShop
    related_products: list[MarketplaceProduct]


class MarketplaceShopDetailResponse(BaseModel):
    shop: MarketplaceShop
    products: list[MarketplaceProduct]


class MarketplaceMessage(BaseModel):
    id: str
    text: str
    is_mine: bool
    time_label: str
    media_url: str | None = None
    reply_to_message_id: str | None = None
    reply_to_preview: str | None = None


class MarketplaceConversation(BaseModel):
    id: str
    name: str
    shop_id: str
    category: str
    avatar_url: str
    last_message: str
    unread_count: int
    time_label: str
    is_online: bool
    messages: list[MarketplaceMessage]


class MarketplaceSendMessageRequest(BaseModel):
    text: str
    media_url: str | None = None
    reply_to_message_id: str | None = None
    reply_to_preview: str | None = None


class MarketplaceCreateConversationRequest(BaseModel):
    shop_id: str


class MarketplaceConversationsResponse(BaseModel):
    conversations: list[MarketplaceConversation]
