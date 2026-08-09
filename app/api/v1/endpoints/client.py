from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_client
from app.database.session import get_db
from app.models.user import User
from app.schemas.operations import (
    ClientDashboardResponse,
    ClientFavoriteResponse,
    ClientProfileUpdateRequest,
)
from app.services.operations_service import OperationsService

router = APIRouter()


@router.get("/dashboard", response_model=ClientDashboardResponse)
def read_client_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
) -> ClientDashboardResponse:
    return OperationsService(db).client_dashboard(current_user)


@router.put("/profile", response_model=ClientDashboardResponse)
def update_client_profile(
    payload: ClientProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
) -> ClientDashboardResponse:
    return OperationsService(db).update_client_profile(current_user, payload)


@router.put("/favorites/{product_id}", response_model=ClientFavoriteResponse)
def add_client_favorite(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
) -> ClientFavoriteResponse:
    try:
        return OperationsService(db).add_favorite(current_user, product_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/favorites/{product_id}", response_model=ClientFavoriteResponse)
def remove_client_favorite(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
) -> ClientFavoriteResponse:
    try:
        return OperationsService(db).remove_favorite(current_user, product_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
