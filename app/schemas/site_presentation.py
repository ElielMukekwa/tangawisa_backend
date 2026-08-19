from pydantic import BaseModel, Field


class HeroStat(BaseModel):
    value: str
    label: str


class HeroContent(BaseModel):
    badge: str
    title: str
    description: str
    primary_cta_label: str
    primary_cta_href: str
    secondary_cta_label: str
    secondary_cta_href: str
    preview_image_url: str
    preview_image_alt: str
    stats: list[HeroStat]


class FeatureItem(BaseModel):
    icon: str
    title: str
    description: str


class ScreenshotItem(BaseModel):
    title: str
    description: str
    image_url: str
    image_alt: str


class DownloadVersion(BaseModel):
    version: str
    date: str
    size: str
    android_min: str
    changes: str
    apk_url: str


class VersionHistoryItem(BaseModel):
    version: str
    date: str
    apk_url: str


class UpdatePost(BaseModel):
    version: str
    date: str
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)


class FaqItem(BaseModel):
    question: str
    answer: str


class ContactChannel(BaseModel):
    name: str
    label: str
    description: str
    url: str


class SharedSection(BaseModel):
    eyebrow: str
    title: str
    description: str


class DownloadSection(SharedSection):
    steps: list[str]
    latest_version: DownloadVersion
    history: list[VersionHistoryItem]


class UpdatesSection(SharedSection):
    posts: list[UpdatePost]


class FaqSection(SharedSection):
    items: list[FaqItem]


class ContactSection(SharedSection):
    channels: list[ContactChannel]


class FooterContent(BaseModel):
    copyright: str
    primary_links: list[ContactChannel] = Field(default_factory=list)
    legal_links: list[ContactChannel] = Field(default_factory=list)


class LegalSectionItem(BaseModel):
    title: str
    body: str


class LegalPageContent(BaseModel):
    eyebrow: str
    title: str
    description: str
    sections: list[LegalSectionItem]


class SitePresentationContent(BaseModel):
    app_name: str
    hero: HeroContent
    features: SharedSection
    feature_items: list[FeatureItem]
    screenshots: SharedSection
    screenshot_items: list[ScreenshotItem]
    download: DownloadSection
    updates: UpdatesSection
    faq: FaqSection
    contact: ContactSection
    privacy: LegalPageContent
    terms: LegalPageContent
    footer: FooterContent


class SitePresentationAdminResponse(BaseModel):
    content: SitePresentationContent
    source: str


class SitePresentationImageUploadResponse(BaseModel):
    filename: str
    url: str


class SitePresentationMediaItem(BaseModel):
    filename: str
    url: str
    size_bytes: int
    created_at: str


class SitePresentationMediaLibraryResponse(BaseModel):
    items: list[SitePresentationMediaItem]


class SitePresentationSummaryStats(BaseModel):
    total_users: int
    total_clients: int
    total_sellers: int
    total_admins_support: int
    active_shops: int
    active_products: int
    conversations: int
    open_tickets: int
    open_reports: int
    uploaded_images: int


class SitePresentationAdminSummaryResponse(BaseModel):
    app_name: str
    source: str
    current_version: str
    last_updated_at: str | None
    content_blocks: dict[str, int]
    stats: SitePresentationSummaryStats


class SitePresentationPublicStat(BaseModel):
    value: str
    label: str


class SitePresentationPublicSummaryResponse(BaseModel):
    app_name: str
    current_version: str
    stats: list[SitePresentationPublicStat]
