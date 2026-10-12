from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.employee import Employee
from app.schemas.ticket import (
    TicketResponse,
    TicketAssignment,
    TicketAssignmentResponse,
    TicketStatusUpdate,
    TicketResolve,
)
from app.services.ticket_service import (
    get_all_tickets,
    get_ticket_by_id,
    assign_ticket,
    update_ticket_status,
    resolve_ticket,
)

router = APIRouter(
    prefix="/api/v1/admin/tickets",
    tags=["Staff Ticket Management"],
)


def require_staff(current_user: dict):
    if current_user.get("designation") not in {
        "Customer Support",
        "Administrator",
        "Super Administrator",
    }:
        raise HTTPException(403, "Ticket staff access required")


def require_admin(current_user: dict):
    if current_user.get("designation") not in {
        "Administrator",
        "Super Administrator",
    }:
        raise HTTPException(403, "Administrator access required")


@router.get("", response_model=list[TicketResponse])
def list_all_tickets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_staff(current_user)
    return get_all_tickets(db)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_staff(current_user)
    return get_ticket_by_id(db, ticket_id)


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketAssignmentResponse,
)
def assign_ticket_endpoint(
    ticket_id: int,
    data: TicketAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)

    employee = (
        db.query(Employee)
        .filter(
            Employee.employee_id == current_user["user_id"],
            Employee.designation == current_user["designation"],
        )
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=403,
            detail="Administrator employee record not found",
        )

    return assign_ticket(
        db=db,
        ticket_id=ticket_id,
        assigned_by_id=employee.employee_id,
        assigned_to_id=data.assigned_to_id,
    )


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def change_ticket_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_staff(current_user)

    return update_ticket_status(
        db=db,
        ticket_id=ticket_id,
        status=data.ticket_status,
    )


@router.patch("/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket_endpoint(
    ticket_id: int,
    data: TicketResolve,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_staff(current_user)

    return resolve_ticket(
        db=db,
        ticket_id=ticket_id,
        solution_description=data.solution_description,
    )