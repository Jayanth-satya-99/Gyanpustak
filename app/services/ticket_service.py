from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_flow import TicketFlow
from app.models.employee import Employee


ADMIN_ROLES = {"Administrator", "Super Administrator"}

STAFF_ROLES = {
    "Customer Support",
    "Administrator",
    "Super Administrator",
}

TICKET_TYPES = {"PRODUCT", "CART", "ORDER", "PROFILE", "OTHER"}

TICKET_STATUSES = {"assigned", "in_progress", "resolved", "closed"}


def generate_ticket_id(db: Session) -> int:
    ticket_id = db.execute(
        text("""
            SELECT NEXT_ID
            FROM TICKET_ID_SEQUENCE
            WHERE SEQUENCE_NAME = 'TICKET'
            FOR UPDATE
        """)
    ).scalar_one_or_none()

    if ticket_id is None:
        raise RuntimeError("Ticket ID sequence is not initialized")

    db.execute(
        text("""
            UPDATE TICKET_ID_SEQUENCE
            SET NEXT_ID = NEXT_ID + 1
            WHERE SEQUENCE_NAME = 'TICKET'
        """)
    )

    return ticket_id


def create_ticket(
    db: Session,
    user_id: int,
    designation: str,
    ticket_type: str,
    title: str,
    problem_description: str,
):
    if ticket_type not in TICKET_TYPES:
        raise HTTPException(422, "Invalid ticket type")

    try:
        ticket = Ticket(
            ticket_id=generate_ticket_id(db),
            type=ticket_type,
            date_of_creation=date.today(),
            user_id=user_id,
            creater=designation,
            title=title.strip(),
            problem_description=problem_description.strip(),
            ticket_status="assigned",
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise


def get_customer_tickets(
    db: Session,
    user_id: int,
    designation: str,
):
    return (
        db.query(Ticket)
        .filter(
            Ticket.user_id == user_id,
            Ticket.creater == designation,
        )
        .order_by(Ticket.date_of_creation.desc(), Ticket.ticket_id.desc())
        .all()
    )


def get_customer_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
    designation: str,
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.ticket_id == ticket_id,
            Ticket.user_id == user_id,
            Ticket.creater == designation,
        )
        .first()
    )

    if ticket is None:
        raise HTTPException(404, "Ticket not found")

    return ticket


def get_all_tickets(db: Session):
    return (
        db.query(Ticket)
        .order_by(Ticket.date_of_creation.desc(), Ticket.ticket_id.desc())
        .all()
    )


def get_ticket_by_id(db: Session, ticket_id: int):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.ticket_id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(404, "Ticket not found")

    return ticket


def get_verified_employee(
    db: Session,
    employee_id: int,
    allowed_roles: set[str] | None = None,
):
    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(404, "Employee not found")

    if allowed_roles is not None and employee.designation not in allowed_roles:
        raise HTTPException(422, "Employee designation is not eligible")

    return employee


def assign_ticket(
    db: Session,
    ticket_id: int,
    assigned_by_id: int,
    assigned_to_id: int,
):
    get_ticket_by_id(db, ticket_id)

    assigned_by = get_verified_employee(
        db, assigned_by_id, ADMIN_ROLES
    )
    assigned_to = get_verified_employee(
        db, assigned_to_id, STAFF_ROLES
    )

    try:
        flow = (
            db.query(TicketFlow)
            .filter(TicketFlow.ticket_id == ticket_id)
            .with_for_update()
            .first()
        )

        if flow is None:
            flow = TicketFlow(
                ticket_id=ticket_id,
                assigned_by=assigned_by.designation,
                assigned_to=assigned_to.designation,
                assigned_by_id=assigned_by.employee_id,
                assigned_to_id=assigned_to.employee_id,
            )
            db.add(flow)
        else:
            flow.assigned_by = assigned_by.designation
            flow.assigned_to = assigned_to.designation
            flow.assigned_by_id = assigned_by.employee_id
            flow.assigned_to_id = assigned_to.employee_id

        ticket = (
            db.query(Ticket)
            .filter(Ticket.ticket_id == ticket_id)
            .with_for_update()
            .first()
        )

        ticket.ticket_status = "assigned"

        db.commit()
        db.refresh(flow)
        return flow

    except Exception:
        db.rollback()
        raise


def update_ticket_status(
    db: Session,
    ticket_id: int,
    status: str,
):
    if status not in TICKET_STATUSES:
        raise HTTPException(422, "Invalid ticket status")

    ticket = (
        db.query(Ticket)
        .filter(Ticket.ticket_id == ticket_id)
        .with_for_update()
        .first()
    )

    if ticket is None:
        raise HTTPException(404, "Ticket not found")

    if ticket.ticket_status == "closed":
        raise HTTPException(409, "Closed tickets cannot be modified")

    if status == "resolved":
        raise HTTPException(
            422,
            "Use the resolve endpoint to provide a solution",
        )

    try:
        ticket.ticket_status = status

        if status == "assigned":
            ticket.completion_date = None
            ticket.solution_description = None

        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise


def resolve_ticket(
    db: Session,
    ticket_id: int,
    solution_description: str,
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.ticket_id == ticket_id)
        .with_for_update()
        .first()
    )

    if ticket is None:
        raise HTTPException(404, "Ticket not found")

    if ticket.ticket_status == "closed":
        raise HTTPException(409, "Closed tickets cannot be resolved")

    try:
        ticket.solution_description = solution_description.strip()
        ticket.ticket_status = "resolved"
        ticket.completion_date = date.today()

        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise


def get_ticket_statistics(db: Session):
    total = db.query(func.count(Ticket.ticket_id)).scalar() or 0

    rows = (
        db.query(
            Ticket.ticket_status,
            func.count(Ticket.ticket_id),
        )
        .group_by(Ticket.ticket_status)
        .all()
    )

    status_counts = {
        status if status is not None else "unknown": count
        for status, count in rows
    }

    return {
        "total_tickets": total,
        "status_counts": status_counts,
    }


def get_ticket_assignments(db: Session):
    return (
        db.query(Ticket, TicketFlow)
        .join(
            TicketFlow,
            TicketFlow.ticket_id == Ticket.ticket_id,
        )
        .order_by(Ticket.ticket_id.desc())
        .all()
    )


def get_eligible_employees(db: Session):
    return (
        db.query(Employee)
        .filter(Employee.designation.in_(STAFF_ROLES))
        .order_by(Employee.designation, Employee.employee_id)
        .all()
    )