from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Create or update one Tangawisa admin account.")
    parser.add_argument("--email", required=True, help="Admin email address.")
    parser.add_argument("--full-name", required=True, help="Admin full name.")
    parser.add_argument("--phone-number", default=None, help="Optional admin phone number.")
    parser.add_argument("--password", default=None, help="Admin password. Omit to type it securely.")
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create missing tables before inserting the admin. Use mainly for local setup.",
    )
    return parser


def read_password(password: str | None) -> str:
    if password:
        return password

    typed_password = getpass("Admin password: ")
    confirmed_password = getpass("Confirm password: ")
    if typed_password != confirmed_password:
        raise ValueError("Les mots de passe ne correspondent pas.")
    return typed_password


def main() -> None:
    args = build_parser().parse_args()
    password = read_password(args.password)

    if len(password) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caracteres.")

    if args.create_tables:
        Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == args.email).first()
        if user is None:
            user = User(
                full_name=args.full_name,
                email=args.email,
                phone_number=args.phone_number,
                hashed_password=get_password_hash(password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(user)
            action = "created"
        else:
            user.full_name = args.full_name
            user.phone_number = args.phone_number
            user.hashed_password = get_password_hash(password)
            user.role = UserRole.admin
            user.is_active = True
            action = "updated"

        db.commit()
        db.refresh(user)
        print(f"Admin {action}: id={user.id} email={user.email} active={user.is_active}")


if __name__ == "__main__":
    main()
