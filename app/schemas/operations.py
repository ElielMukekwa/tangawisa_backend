from pydantic import BaseModel, Field

from app.models.user import UserRole
from app.schemas.marketplace import MarketplaceConversation, MarketplaceProduct, MarketplaceShop


class AdminUserRecordResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    city: str
    is_active: bool
    last_activity: str
    linked_shop_name: str | None = None


class AdminUpdateUserStatusRequest(BaseModel):
    is_active: bool


class ReportRecordResponse(BaseModel):
    id: str
    title: str
    target_type: str
    target_label: str
    reporter_name: str
    status: str
    priority: str
    created_label: str
    reason: str
    support_comment: str = ""
    product_id: str | None = None
    shop_id: str | None = None
    user_id: str | None = None


class SupportTicketResponse(BaseModel):
    id: str
    subject: str
    customer_name: str
    requester_role: UserRole
    status: str
    priority: str
    created_label: str
    last_message: str
    assigned_agent: str
    history: list[str]
    product_id: str | None = None
    shop_id: str | None = None


class ActivityItemResponse(BaseModel):
    title: str
    subtitle: str
    time_label: str
    icon: str


class AdminDashboardResponse(BaseModel):
    users: list[AdminUserRecordResponse]
    reports: list[ReportRecordResponse]
    tickets: list[SupportTicketResponse]
    activities: list[ActivityItemResponse]
    total_users: int
    active_sellers: int
    open_reports: int
    open_tickets: int


class AdminUsersResponse(BaseModel):
    users: list[AdminUserRecordResponse]


class AdminUserDetailResponse(BaseModel):
    user: AdminUserRecordResponse
    conversations_count: int
    messages_count: int
    linked_shop: MarketplaceShop | None = None
    recent_products: list[MarketplaceProduct]


class AdminReportsResponse(BaseModel):
    reports: list[ReportRecordResponse]


class AdminReportDetailResponse(BaseModel):
    report: ReportRecordResponse
    product: MarketplaceProduct | None = None
    shop: MarketplaceShop | None = None
    user: AdminUserRecordResponse | None = None


class AdminSupportOverviewResponse(BaseModel):
    tickets: list[SupportTicketResponse]
    activities: list[ActivityItemResponse]
    unresolved_reports: int
    escalated_tickets: int


class SupportDashboardResponse(BaseModel):
    tickets: list[SupportTicketResponse]
    reports: list[ReportRecordResponse]
    activities: list[ActivityItemResponse]
    open_tickets: int
    escalated_tickets: int
    pending_reports: int


class SupportTicketsResponse(BaseModel):
    tickets: list[SupportTicketResponse]


class SupportTicketDetailResponse(BaseModel):
    ticket: SupportTicketResponse
    product: MarketplaceProduct | None = None
    shop: MarketplaceShop | None = None
    user: AdminUserRecordResponse | None = None


class SupportReportsResponse(BaseModel):
    reports: list[ReportRecordResponse]


class SupportUpdateTicketRequest(BaseModel):
    status: str
    priority: str
    assigned_agent: str | None = None
    note: str | None = None


class SupportUpdateReportRequest(BaseModel):
    status: str
    support_comment: str | None = None


class ClientNotificationResponse(BaseModel):
    title: str
    subtitle: str
    icon: str


class ClientActivityResponse(BaseModel):
    title: str
    subtitle: str
    status: str
    icon: str
    tint: str


class ClientDashboardResponse(BaseModel):
    full_name: str
    email: str
    phone_number: str | None
    favorite_count: int
    unread_notifications: int
    conversations: list[MarketplaceConversation]
    favorite_products: list[MarketplaceProduct]
    recommended_shops: list[MarketplaceShop]
    activities: list[ClientActivityResponse]
    notifications: list[ClientNotificationResponse]


class ClientFavoriteResponse(BaseModel):
    product_id: str
    is_favorite: bool
    favorite_count: int


class ClientProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    phone_number: str | None = Field(default=None, max_length=30)
