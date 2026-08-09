from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, payload: RegisterRequest) -> TokenResponse:
        if payload.role not in {UserRole.client, UserRole.seller}:
            raise ValueError("Seuls les comptes client et vendeur peuvent etre crees publiquement.")
        existing_user = self.db.query(User).filter(User.email == payload.email).first()
        if existing_user is not None:
            raise ValueError("Un compte existe deja avec cet email.")

        user = User(
            full_name=payload.full_name,
            email=str(payload.email),
            phone_number=payload.phone_number,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return self._build_token_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse | None:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if user is None or not verify_password(payload.password, user.hashed_password):
            return None
        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        token = create_access_token(subject=user.email)
        return TokenResponse(
            access_token=token,
            user=UserProfile.model_validate(user),
        )
