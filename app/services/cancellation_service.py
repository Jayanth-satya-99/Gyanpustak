from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_order import ApiOrder
from app.models.api_order_item import ApiOrderItem
from app.models.api_rental import ApiRental
from app.models.book import Book


def cancel_order(
    db: Session,
    student_id: int,
    order_id: int,
) -> dict:
    try:
        # 1. Lock the order and verify ownership.
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

        if order.order_status == "Cancelled":
            raise HTTPException(
                status_code=409,
                detail="Order has already been cancelled",
            )

        if order.order_status != "Processed":
            raise HTTPException(
                status_code=409,
                detail="Only processed, unfulfilled orders can be cancelled",
            )

        # 2. Lock order items.
        items = db.scalars(
            select(ApiOrderItem)
            .where(ApiOrderItem.order_id == order_id)
            .order_by(
                ApiOrderItem.isbn,
                ApiOrderItem.purchase_option,
            )
            .with_for_update()
        ).all()

        if not items:
            raise HTTPException(
                status_code=409,
                detail="Order contains no items",
            )

        # 3. Lock every rental associated with the order.
        rentals = db.scalars(
            select(ApiRental)
            .where(ApiRental.order_id == order_id)
            .order_by(ApiRental.rental_id)
            .with_for_update()
        ).all()

        # Reject cancellation if any rental has already been returned.
        if any(rental.status == "Returned" for rental in rentals):
            raise HTTPException(
                status_code=409,
                detail="Order cannot be cancelled because a rental has already been returned",
            )

        # A processed order must not contain previously cancelled rentals.
        if any(rental.status == "Cancelled" for rental in rentals):
            raise HTTPException(
                status_code=409,
                detail="Order contains an already-cancelled rental",
            )

        # 4. Build the inventory restoration quantities.
        quantities = {}

        for item in items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid quantity for {item.isbn}",
                )

            if item.purchase_option == "Buy":
                quantities[item.isbn] = (
                    quantities.get(item.isbn, 0) + item.quantity
                )

            elif item.purchase_option != "Rent":
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid purchase option for {item.isbn}",
                )

        # Every rental order item must have exactly one matching
        # active rental record with the same quantity.
        rental_map = {
            (rental.isbn, rental.purchase_option): rental
            for rental in rentals
        }

        for item in items:
            if item.purchase_option != "Rent":
                continue

            rental = rental_map.get((item.isbn, "Rent"))

            if rental is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Rental record missing for {item.isbn}",
                )

            if rental.quantity != item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Rental quantity mismatch for {item.isbn}",
                )

            if rental.status != "Active":
                raise HTTPException(
                    status_code=409,
                    detail=f"Rental is not active for {item.isbn}",
                )

            quantities[item.isbn] = (
                quantities.get(item.isbn, 0) + rental.quantity
            )

        # 5. Lock inventory rows in ascending ISBN order.
        books = {}

        for isbn in sorted(quantities):
            book = db.scalar(
                select(Book)
                .where(Book.isbn == isbn)
                .with_for_update()
            )

            if book is None or book.quantity is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Inventory unavailable for {isbn}",
                )

            books[isbn] = book

        # 6. Restore inventory.
        for isbn, quantity in quantities.items():
            books[isbn].quantity += quantity

        # 7. Cancel associated rentals.
        for rental in rentals:
            rental.status = "Cancelled"
            rental.returned_at = None

        # 8. Cancel the order.
        order.order_status = "Cancelled"

        # 9. Commit all changes atomically.
        db.commit()

        return {
            "message": "Order cancelled successfully",
            "order_id": order_id,
            "order_status": "Cancelled",
        }

    except Exception:
        db.rollback()
        raise