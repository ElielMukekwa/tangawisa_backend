from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_support
from app.database.session import get_db
from app.models.user import User
from app.schemas.operations import (
    AdminReportDetailResponse,
    ReportRecordResponse,
    SupportDashboardResponse,
    SupportTicketDetailResponse,
    SupportReportsResponse,
    SupportTicketResponse,
    SupportTicketsResponse,
    SupportUpdateReportRequest,
    SupportUpdateTicketRequest,
)
from app.services.operations_service import OperationsService

router = APIRouter()


@router.get("/dashboard", response_model=SupportDashboardResponse)
def read_support_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> SupportDashboardResponse:
    return OperationsService(db).support_dashboard()


@router.get("/tickets", response_model=SupportTicketsResponse)
def read_support_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> SupportTicketsResponse:
    return OperationsService(db).support_tickets()


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
def read_support_ticket_detail(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> SupportTicketDetailResponse:
    try:
        return OperationsService(db).support_ticket_detail(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/tickets/{ticket_id}", response_model=SupportTicketResponse)
def update_support_ticket(
    ticket_id: str,
    payload: SupportUpdateTicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> SupportTicketResponse:
    try:
        return OperationsService(db).update_ticket(ticket_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/reports", response_model=SupportReportsResponse)
def read_support_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> SupportReportsResponse:
    return OperationsService(db).support_reports()


@router.get("/reports/{report_id}", response_model=AdminReportDetailResponse)
def read_support_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> AdminReportDetailResponse:
    try:
        return OperationsService(db).admin_report_detail(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/reports/{report_id}", response_model=ReportRecordResponse)
def update_support_report(
    report_id: str,
    payload: SupportUpdateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support),
) -> ReportRecordResponse:
    try:
        return OperationsService(db).update_report(report_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
