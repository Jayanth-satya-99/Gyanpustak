from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import (
    create_ticket,
    get_customer_tickets,
    get_customer_ticket,
)

router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["Customer Tickets"],
)


def require_student(current_user: dict):
    if current_user.get("designation") != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only students can perform this operation",
        )


@router.post("", response_model=TicketResponse, status_code=201)
def create_customer_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    return create_ticket(
        db=db,
        user_id=current_user["user_id"],
        designation=current_user["designation"],
        ticket_type=data.type,
        title=data.title,
        problem_description=data.problem_description,
    )


@router.get("", response_model=list[TicketResponse])
def list_customer_tickets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    return get_customer_tickets(
        db=db,
        user_id=current_user["user_id"],
        designation=current_user["designation"],
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_customer_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    return get_customer_ticket(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user["user_id"],
        designation=current_user["designation"],
    )