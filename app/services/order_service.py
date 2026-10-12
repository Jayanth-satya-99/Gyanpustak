from decimal import Decimal
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_cart import ApiCart
from app.models.api_cart_item import ApiCartItem
from app.models.api_order import ApiOrder
from app.models.api_order_item import ApiOrderItem
from app.models.book import Book
from app.models.api_rental import ApiRental


def checkout(db: Session, student_id: int) -> dict:
    try:
        # 1. Lock the student's cart.
        cart = db.scalar(
            select(ApiCart)
            .where(ApiCart.student_id == student_id)
            .with_for_update()
        )

        if cart is None:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty",
            )

        # 2. Read and lock the cart items.
        cart_items = db.scalars(
            select(ApiCartItem)
            .where(ApiCartItem.cart_id == cart.cart_id)
            .order_by(ApiCartItem.isbn, ApiCartItem.purchase_option)
            .with_for_update()
        ).all()

        if not cart_items:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty",
            )

        # 3. Lock all required book rows in a consistent order.
        isbns = sorted({item.isbn for item in cart_items})

        books = {}

        for isbn in isbns:
            book = db.scalar(
                select(Book)
                .where(Book.isbn == isbn)
                .with_for_update()
            )

            if book is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Book {isbn} no longer exists",
                )

            books[isbn] = book

        # 4. Validate inventory and calculate the order total.
        required_quantity = {}
        order_lines = []
        total_amount = Decimal("0.00")

        for item in cart_items:
            book = books[item.isbn]

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid quantity for {item.isbn}",
                )

            if item.purchase_option == "Buy":
                unit_price = book.price_b
            elif item.purchase_option == "Rent":
                unit_price = book.price_r
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid purchase option for {item.isbn}",
                )

            if unit_price is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Price unavailable for {item.isbn}",
                )

            if book.quantity is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Inventory unavailable for {item.isbn}",
                )

            required_quantity[item.isbn] = (
                required_quantity.get(item.isbn, 0)
                + item.quantity
            )

            unit_price = Decimal(str(unit_price))
            subtotal = unit_price * item.quantity
            total_amount += subtotal

            order_lines.append(
                {
                    "isbn": item.isbn,
                    "purchase_option": item.purchase_option,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                }
            )

        for isbn, quantity in required_quantity.items():
            if books[isbn].quantity < quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient stock for {isbn}",
                )

        # 5. Create the order.
        order = ApiOrder(
            student_id=student_id,
            order_status="Processed",
            total_amount=total_amount,
        )

        db.add(order)
        db.flush()  # Generate ORDER_ID.

        # 6. Create order items first.
        for line in order_lines:
            db.add(
                ApiOrderItem(
                    order_id=order.order_id,
                    isbn=line["isbn"],
                    purchase_option=line["purchase_option"],
                    quantity=line["quantity"],
                    unit_price=line["unit_price"],
                )
            )

        # Ensure the order items exist before creating rentals.
        db.flush()

        # 7. Create rental records for rented items.
        rental_start = date.today()
        due_date = rental_start + timedelta(days=14)

        for line in order_lines:
            if line["purchase_option"] == "Rent":
                db.add(
                    ApiRental(
                        order_id=order.order_id,
                        isbn=line["isbn"],
                        purchase_option="Rent",
                        quantity=line["quantity"],
                        rental_start=rental_start,
                        due_date=due_date,
                        status="Active",
                    )
                )

        # 8. Update inventory.
        for isbn, quantity in required_quantity.items():
            books[isbn].quantity -= quantity

        # 9. Clear the cart.
        for item in cart_items:
            db.delete(item)

        # 10. Commit all changes together.
        db.commit()
        return {
            "message": "Checkout successful",
            "order_id": order.order_id,
            "order_status": order.order_status,
            "total_amount": str(total_amount),
            "items": order_lines,
        }
    except Exception:
        db.rollback()
        raise