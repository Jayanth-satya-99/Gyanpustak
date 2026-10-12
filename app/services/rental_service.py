from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_rental import ApiRental
from app.models.api_order import ApiOrder
from app.models.book import Book


def list_rentals(db: Session, student_id: int) -> list[dict]:
    rows = db.execute(
        select(ApiRental, ApiOrder)
        .join(
            ApiOrder,
            ApiOrder.order_id == ApiRental.order_id,
        )
        .where(ApiOrder.student_id == student_id)
        .order_by(ApiRental.rental_id.desc())
    ).all()

    result = []

    for rental, order in rows:
        result.append({
            "rental_id": rental.rental_id,
            "order_id": rental.order_id,
            "isbn": rental.isbn,
            "quantity": rental.quantity,
            "rental_start": rental.rental_start,
            "due_date": rental.due_date,
            "returned_at": rental.returned_at,
            "status": rental.status,
            "overdue": (
                rental.status == "Active"
                and rental.due_date < date.today()
            ),
        })

    return result


def get_rental(
    db: Session,
    student_id: int,
    rental_id: int,
) -> dict:
    rental = db.scalar(
        select(ApiRental)
        .join(
            ApiOrder,
            ApiOrder.order_id == ApiRental.order_id,
        )
        .where(
            ApiRental.rental_id == rental_id,
            ApiOrder.student_id == student_id,
        )
    )

    if rental is None:
        raise HTTPException(
            status_code=404,
            detail="Rental not found",
        )

    return {
        "rental_id": rental.rental_id,
        "order_id": rental.order_id,
        "isbn": rental.isbn,
        "quantity": rental.quantity,
        "rental_start": rental.rental_start,
        "due_date": rental.due_date,
        "returned_at": rental.returned_at,
        "status": rental.status,
        "overdue": (
            rental.status == "Active"
            and rental.due_date < date.today()
        ),
    }


def return_rental(
    db: Session,
    student_id: int,
    rental_id: int,
) -> dict:
    try:
        # 1. Find the rental's order ID.
        # This initial read does not lock the rental.
        order_id = db.scalar(
            select(ApiRental.order_id)
            .join(
                ApiOrder,
                ApiOrder.order_id == ApiRental.order_id,
            )
            .where(
                ApiRental.rental_id == rental_id,
                ApiOrder.student_id == student_id,
            )
        )

        if order_id is None:
            raise HTTPException(
                status_code=404,
                detail="Rental not found",
            )

        # 2. Lock the order first.
        order = db.scalar(
            select(ApiOrder)
            .where(
                ApiOrder.order_id == order_id,
                ApiOrder.student_id == student_id,
            )
            .with_for_update()
        )

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        # 3. Lock the rental after the order.
        rental = db.scalar(
            select(ApiRental)
            .where(
                ApiRental.rental_id == rental_id,
                ApiRental.order_id == order.order_id,
            )
            .with_for_update()
        )

        if rental is None:
            raise HTTPException(
                status_code=404,
                detail="Rental not found",
            )

        if rental.status != "Active":
            raise HTTPException(
                status_code=409,
                detail="Rental is not active",
            )

        if order.order_status == "Cancelled":
            raise HTTPException(
                status_code=409,
                detail="Cannot return a rental belonging to a cancelled order",
            )

        # 4. Lock the book inventory row.
        book = db.scalar(
            select(Book)
            .where(Book.isbn == rental.isbn)
            .with_for_update()
        )

        if book is None or book.quantity is None:
            raise HTTPException(
                status_code=409,
                detail="Book inventory is unavailable",
            )

        # 5. Restore inventory and update rental status.
        book.quantity += rental.quantity

        rental.status = "Returned"
        rental.returned_at = datetime.now()

        db.commit()

        return {
            "message": "Rental returned successfully",
            "rental_id": rental.rental_id,
            "isbn": rental.isbn,
            "quantity_returned": rental.quantity,
            "status": rental.status,
            "returned_at": rental.returned_at,
        }

    except Exception:
        db.rollback()
        raise