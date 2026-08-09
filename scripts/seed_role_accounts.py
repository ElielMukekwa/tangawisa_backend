from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


ROLE_ACCOUNTS = [
    {
        "full_name": "Client Tangawisa",
        "email": "client@tangawisa.app",
        "phone_number": "+243000000001",
        "password": "12345678",
        "role": UserRole.client,
    },
    {
        "full_name": "Vendeur Tangawisa",
        "email": "vendeur@tangawisa.app",
        "phone_number": "+243000000002",
        "password": "12345678",
        "role": UserRole.seller,
    },
    {
        "full_name": "Admin Tangawisa",
        "email": "admin@tangawisa.app",
        "phone_number": "+243000000003",
        "password": "12345678",
        "role": UserRole.admin,
    },
    {
        "full_name": "Support Tangawisa",
        "email": "support@tangawisa.app",
        "phone_number": "+243000000004",
        "password": "12345678",
        "role": UserRole.support,
    },
]


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for account in ROLE_ACCOUNTS:
            user = db.query(User).filter(User.email == account["email"]).first()
            if user is None:
                user = User(
                    full_name=account["full_name"],
                    email=account["email"],
                    phone_number=account["phone_number"],
                    hashed_password=get_password_hash(account["password"]),
                    role=account["role"],
                    is_active=True,
                )
                db.add(user)
            else:
                user.full_name = account["full_name"]
                user.phone_number = account["phone_number"]
                user.hashed_password = get_password_hash(account["password"])
                user.role = account["role"]
                user.is_active = True

        db.commit()

        users = db.query(User).order_by(User.id.asc()).all()
        for user in users:
            print(f"{user.id} | {user.role.value} | {user.email} | active={user.is_active}")


if __name__ == "__main__":
    main()
