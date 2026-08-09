from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.marketplace import (
    MarketplaceCatalogResponse,
    MarketplaceConversation,
    MarketplaceConversationsResponse,
    MarketplaceCreateConversationRequest,
    MarketplaceProductDetailResponse,
    MarketplaceSendMessageRequest,
    MarketplaceShopDetailResponse,
)
from app.services.marketplace_service import MarketplaceService

router = APIRouter()


@router.get("/catalog", response_model=MarketplaceCatalogResponse)
def read_catalog(db: Session = Depends(get_db)) -> MarketplaceCatalogResponse:
    return MarketplaceService(db).catalog()


@router.get("/products/{product_id}", response_model=MarketplaceProductDetailResponse)
def read_product_detail(
    product_id: str,
    db: Session = Depends(get_db),
) -> MarketplaceProductDetailResponse:
    try:
        return MarketplaceService(db).product_detail(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/shops/{shop_id}", response_model=MarketplaceShopDetailResponse)
def read_shop_detail(
    shop_id: str,
    db: Session = Depends(get_db),
) -> MarketplaceShopDetailResponse:
    try:
        return MarketplaceService(db).shop_detail(shop_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/conversations", response_model=MarketplaceConversationsResponse)
def read_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketplaceConversationsResponse:
    return MarketplaceService(db).conversations_for_user(current_user)


@router.post("/conversations", response_model=MarketplaceConversation)
def get_or_create_conversation(
    payload: MarketplaceCreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketplaceConversation:
    try:
        return MarketplaceService(db).get_or_create_conversation(current_user, payload.shop_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/messages", response_model=MarketplaceConversation)
def create_message(
    conversation_id: int,
    payload: MarketplaceSendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketplaceConversation:
    try:
        return MarketplaceService(db).send_message(
            current_user=current_user,
            conversation_id=conversation_id,
            text=payload.text,
            media_url=payload.media_url,
            reply_to_message_id=payload.reply_to_message_id,
            reply_to_preview=payload.reply_to_preview,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/read", response_model=MarketplaceConversation)
def mark_conversation_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketplaceConversation:
    try:
        return MarketplaceService(db).mark_conversation_read(current_user, conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
