from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.employee import Employee
from app.schemas.ticket import (
    TicketStatisticsResponse,
    EmployeeSummary,
)
from app.services.ticket_service import (
    get_ticket_statistics,
    get_ticket_assignments,
    get_eligible_employees,
)

router = APIRouter(
    prefix="/api/v1/super-admin/tickets",
    tags=["Super Administrator"],
)


def require_super_admin(current_user: dict):
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=403,
            detail="Super Administrator access required",
        )


@router.get("/statistics", response_model=TicketStatisticsResponse)
def ticket_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_super_admin(current_user)
    return get_ticket_statistics(db)


@router.get("/assignments")
def ticket_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_super_admin(current_user)

    rows = get_ticket_assignments(db)

    return [
        {
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "status": ticket.ticket_status,
            "assigned_by_id": flow.assigned_by_id,
            "assigned_by": flow.assigned_by,
            "assigned_to_id": flow.assigned_to_id,
            "assigned_to": flow.assigned_to,
        }
        for ticket, flow in rows
    ]


@router.get("/employees", response_model=list[EmployeeSummary])
def eligible_employees(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_super_admin(current_user)

    return get_eligible_employees(db)