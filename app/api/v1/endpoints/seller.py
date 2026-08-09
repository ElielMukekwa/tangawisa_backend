from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_seller
from app.database.session import get_db
from app.models.user import User
from app.schemas.seller import (
    SellerDashboardResponse,
    SellerFeedResponse,
    SellerInventoryItem,
    SellerNotificationsResponse,
    SellerProductUpsertRequest,
    SellerProductsResponse,
)
from app.services.seller_service import SellerService

router = APIRouter()


@router.get("/dashboard", response_model=SellerDashboardResponse)
def read_seller_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerDashboardResponse:
    try:
        return SellerService(db).dashboard(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/products", response_model=SellerProductsResponse)
def read_seller_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerProductsResponse:
    try:
        return SellerService(db).products(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/products", response_model=SellerInventoryItem, status_code=status.HTTP_201_CREATED)
def create_seller_product(
    payload: SellerProductUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerInventoryItem:
    try:
        return SellerService(db).create_product(current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/products/{product_id}", response_model=SellerInventoryItem)
def update_seller_product(
    product_id: str,
    payload: SellerProductUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerInventoryItem:
    try:
        return SellerService(db).update_product(current_user, product_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/notifications", response_model=SellerNotificationsResponse)
def read_seller_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerNotificationsResponse:
    try:
        return SellerService(db).notifications(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/feed", response_model=SellerFeedResponse)
def read_seller_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller),
) -> SellerFeedResponse:
    try:
        return SellerService(db).feed(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

