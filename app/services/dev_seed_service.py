from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.category import Category
from app.models.conversation import Conversation
from app.models.message import Message, MessageStatus, MessageType
from app.models.product import Product
from app.models.shop import Shop
from app.models.user import User, UserRole


def seed_development_data(db: Session) -> None:
    dev_users = [
        {
            "full_name": "Jean-Pierre Kabasele",
            "email": "client@tangawisa.app",
            "phone_number": "+243000000001",
            "password": "secret123",
            "role": UserRole.client,
        },
        {
            "full_name": "Amani Nsimba",
            "email": "vendeur@tangawisa.app",
            "phone_number": "+243000000002",
            "password": "secret123",
            "role": UserRole.seller,
        },
        {
            "full_name": "Grace Mwamba",
            "email": "admin@tangawisa.app",
            "phone_number": "+243000000003",
            "password": "12345678",
            "role": UserRole.admin,
        },
        {
            "full_name": "Sarah Ilunga",
            "email": "support@tangawisa.app",
            "phone_number": "+243000000004",
            "password": "secret123",
            "role": UserRole.support,
        },
    ]

    existing_users = {user.email: user for user in db.query(User).all()}
    created_any_user = False

    for item in dev_users:
        existing_user = existing_users.get(item["email"])
        if existing_user is None:
            db.add(
                User(
                    full_name=item["full_name"],
                    email=item["email"],
                    phone_number=item["phone_number"],
                    hashed_password=get_password_hash(item["password"]),
                    role=item["role"],
                    is_active=True,
                )
            )
            created_any_user = True
            continue

        existing_user.full_name = item["full_name"]
        existing_user.phone_number = item["phone_number"]
        existing_user.hashed_password = get_password_hash(item["password"])
        existing_user.role = item["role"]
        existing_user.is_active = True

    if created_any_user:
        db.flush()

    db.commit()

    users = db.query(User).all()
    if db.query(Category).first() is not None:
        return

    category_rows = {
        "Electronique": Category(name="Electronique", slug="electronique", description="Produits electroniques"),
        "Mode": Category(name="Mode", slug="mode", description="Articles mode"),
        "Maison et deco": Category(name="Maison et deco", slug="maison-et-deco", description="Maison et decoration"),
        "Artisanat": Category(name="Artisanat", slug="artisanat", description="Artisanat local"),
        "Alimentation": Category(name="Alimentation", slug="alimentation", description="Produits alimentaires"),
    }
    db.add_all(category_rows.values())
    db.flush()

    seller = next(user for user in users if user.role == UserRole.seller)

    shops = [
        Shop(owner_id=seller.id, name="Atelier Kivu Mobile", slug="shop-kivu-mobile", description="Boutique specialisee dans les appareils mobiles, ecouteurs et accessoires utiles au quotidien.", logo_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=200&q=80", banner_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80", city="Goma", is_active=True),
        Shop(owner_id=seller.id, name="Maison Amani Couture", slug="shop-amani-couture", description="Mode feminine et urbaine, creee pour les sorties, ceremonies et looks du quotidien.", logo_url="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=200&q=80", banner_url="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=1200&q=80", city="Bukavu", is_active=True),
        Shop(owner_id=seller.id, name="Zuri Artistry", slug="shop-zuri-artistry", description="Objets artisanaux et textiles inspirants, selectionnes pour raconter une histoire forte.", logo_url="https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=200&q=80", banner_url="https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1200&q=80", city="Bukavu", is_active=True),
        Shop(owner_id=seller.id, name="Saveurs du Fleuve", slug="shop-saveurs-fleuve", description="Produits alimentaires pratiques et cadeaux gourmands a negocier directement avec le vendeur.", logo_url="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=200&q=80", banner_url="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80", city="Kinshasa", is_active=True),
    ]
    db.add_all(shops)
    db.flush()

    shop_by_slug = {shop.slug: shop for shop in shops}

    products = [
        Product(shop_id=shop_by_slug["shop-kivu-mobile"].id, category_id=category_rows["Electronique"].id, name="Smartphone Nova X12", description="Produit electronique pratique pour communication, travail et usage quotidien.", price_hint=12500, stock_quantity=7, is_active=True),
        Product(shop_id=shop_by_slug["shop-kivu-mobile"].id, category_id=category_rows["Electronique"].id, name="PowerBank River 20K", description="Accessoire utile pour energie mobile et deplacement.", price_hint=4200, stock_quantity=18, is_active=True),
        Product(shop_id=shop_by_slug["shop-amani-couture"].id, category_id=category_rows["Mode"].id, name="Robe Amani Classic", description="Piece mode confectionnee pour l elegance, le confort et les sorties choisies.", price_hint=14800, stock_quantity=5, is_active=True),
        Product(shop_id=shop_by_slug["shop-amani-couture"].id, category_id=category_rows["Mode"].id, name="Ensemble Beige Urbain", description="Mode feminine sobre et urbaine pour le quotidien.", price_hint=16200, stock_quantity=4, is_active=True),
        Product(shop_id=shop_by_slug["shop-zuri-artistry"].id, category_id=category_rows["Artisanat"].id, name="Tissage Heritage", description="Piece artisanale choisie pour sa matiere, son histoire et sa presence visuelle.", price_hint=11500, stock_quantity=3, is_active=True),
        Product(shop_id=shop_by_slug["shop-saveurs-fleuve"].id, category_id=category_rows["Alimentation"].id, name="Pack Jus Nature", description="Produit alimentaire pratique ou cadeau a partager selon le besoin du client.", price_hint=4100, stock_quantity=20, is_active=True),
    ]
    db.add_all(products)
    db.flush()

    client = next(user for user in users if user.role == UserRole.client)
    support = next(user for user in users if user.role == UserRole.support)

    seller_shop = shop_by_slug["shop-amani-couture"]
    support_shop = shop_by_slug["shop-kivu-mobile"]

    conversations = [
        Conversation(client_id=client.id, seller_id=seller.id, shop_id=seller_shop.id),
        Conversation(client_id=client.id, seller_id=support.id, shop_id=support_shop.id),
    ]
    db.add_all(conversations)
    db.flush()

    db.add_all([
        Message(conversation_id=conversations[0].id, sender_id=client.id, message_type=MessageType.text, body="Bonjour, cette robe en lin est encore disponible ?", status=MessageStatus.read),
        Message(conversation_id=conversations[0].id, sender_id=seller.id, message_type=MessageType.text, body="Oui, elle est disponible en beige et en terracotta.", status=MessageStatus.read),
        Message(conversation_id=conversations[0].id, sender_id=client.id, message_type=MessageType.text, body="Parfait. Je peux voir une photo portee ?", status=MessageStatus.sent),
        Message(conversation_id=conversations[1].id, sender_id=client.id, message_type=MessageType.text, body="Bonjour, je souhaite signaler une annonce en doublon.", status=MessageStatus.read),
        Message(conversation_id=conversations[1].id, sender_id=support.id, message_type=MessageType.text, body="Votre demande a bien ete enregistree.", status=MessageStatus.sent),
    ])

    db.commit()
