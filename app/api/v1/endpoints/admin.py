from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_platform_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.operations import (
    AdminDashboardResponse,
    AdminReportDetailResponse,
    AdminReportsResponse,
    AdminSupportOverviewResponse,
    AdminUpdateUserStatusRequest,
    AdminUserDetailResponse,
    AdminUserRecordResponse,
    AdminUsersResponse,
)
from app.services.operations_service import OperationsService

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardResponse)
def read_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminDashboardResponse:
    return OperationsService(db).admin_dashboard()


@router.get("/users", response_model=AdminUsersResponse)
def read_admin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminUsersResponse:
    return OperationsService(db).admin_users()


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def read_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminUserDetailResponse:
    try:
        return OperationsService(db).admin_user_detail(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/users/{user_id}/status", response_model=AdminUserRecordResponse)
def update_admin_user_status(
    user_id: int,
    payload: AdminUpdateUserStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminUserRecordResponse:
    try:
        return OperationsService(db).update_user_status(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/reports", response_model=AdminReportsResponse)
def read_admin_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminReportsResponse:
    return OperationsService(db).admin_reports()


@router.get("/reports/{report_id}", response_model=AdminReportDetailResponse)
def read_admin_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminReportDetailResponse:
    try:
        return OperationsService(db).admin_report_detail(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/support/overview", response_model=AdminSupportOverviewResponse)
def read_admin_support_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
) -> AdminSupportOverviewResponse:
    return OperationsService(db).admin_support_overview()
