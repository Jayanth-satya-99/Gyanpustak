from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.book import Book
from app.models.api_cart import ApiCart
from app.models.api_cart_item import ApiCartItem


def get_or_create_cart(
    db: Session,
    student_id: int,
) -> ApiCart:
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=403,
            detail="Student account not found",
        )

    cart = db.scalar(
        select(ApiCart).where(
            ApiCart.student_id == student_id
        )
    )

    if cart is not None:
        return cart

    cart = ApiCart(student_id=student_id)
    db.add(cart)

    try:
        db.commit()
        db.refresh(cart)
        return cart
    except Exception:
        db.rollback()

        # Another concurrent request may have created the cart.
        cart = db.scalar(
            select(ApiCart).where(
                ApiCart.student_id == student_id
            )
        )

        if cart is not None:
            return cart

        raise


def get_cart(
    db: Session,
    student_id: int,
) -> dict:
    cart = get_or_create_cart(db, student_id)

    rows = db.execute(
        select(ApiCartItem, Book)
        .join(Book, Book.isbn == ApiCartItem.isbn)
        .where(ApiCartItem.cart_id == cart.cart_id)
        .order_by(ApiCartItem.isbn)
    ).all()

    items = []
    total = 0

    for item, book in rows:
        unit_price = (
            book.price_b
            if item.purchase_option == "Buy"
            else book.price_r
        )

        subtotal = (
            unit_price * item.quantity
            if unit_price is not None
            else None
        )

        if subtotal is not None:
            total += subtotal

        items.append(
            {
                "isbn": item.isbn,
                "title": book.title,
                "purchase_option": item.purchase_option,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    return {
        "cart_id": cart.cart_id,
        "items": items,
        "total": total,
    }


def add_item(
    db: Session,
    student_id: int,
    isbn: str,
    purchase_option: str,
    quantity: int,
) -> dict:
    if quantity <= 0:
        raise HTTPException(
            status_code=422,
            detail="Quantity must be positive",
        )

    cart = get_or_create_cart(db, student_id)

    book = db.get(Book, isbn)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    price = (
        book.price_b
        if purchase_option == "Buy"
        else book.price_r
    )

    if price is None:
        raise HTTPException(
            status_code=409,
            detail="Price unavailable for the selected option",
        )

    key = (cart.cart_id, isbn, purchase_option)
    item = db.get(ApiCartItem, key)

    try:
        if item is None:
            item = ApiCartItem(
                cart_id=cart.cart_id,
                isbn=isbn,
                purchase_option=purchase_option,
                quantity=quantity,
            )
            db.add(item)
        else:
            item.quantity += quantity

        db.commit()

        return {
            "message": "Cart updated successfully",
            "cart_id": cart.cart_id,
            "isbn": isbn,
            "purchase_option": purchase_option,
            "quantity": item.quantity,
        }

    except Exception:
        db.rollback()
        raise


def update_item(
    db: Session,
    student_id: int,
    isbn: str,
    quantity: int | None,
    purchase_option: str | None,
) -> dict:
    cart = get_or_create_cart(db, student_id)

    if quantity is not None and quantity <= 0:
        raise HTTPException(
            status_code=422,
            detail="Quantity must be positive",
        )

    if quantity is None and purchase_option is None:
        raise HTTPException(
            status_code=422,
            detail="Provide quantity or purchase_option",
        )

    try:
        if purchase_option is None:
            item = db.scalar(
                select(ApiCartItem).where(
                    ApiCartItem.cart_id == cart.cart_id,
                    ApiCartItem.isbn == isbn,
                )
            )

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cart item not found",
                )

            if quantity is not None:
                item.quantity = quantity

        else:
            item = db.scalar(
                select(ApiCartItem).where(
                    ApiCartItem.cart_id == cart.cart_id,
                    ApiCartItem.isbn == isbn,
                    ApiCartItem.purchase_option == purchase_option,
                )
            )

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cart item not found for that option",
                )

            if quantity is not None:
                item.quantity = quantity

        db.commit()

        return {"message": "Cart item updated successfully"}

    except Exception:
        db.rollback()
        raise


def remove_item(
    db: Session,
    student_id: int,
    isbn: str,
) -> dict:
    cart = get_or_create_cart(db, student_id)

    items = db.scalars(
        select(ApiCartItem).where(
            ApiCartItem.cart_id == cart.cart_id,
            ApiCartItem.isbn == isbn,
        )
    ).all()

    if not items:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    try:
        for item in items:
            db.delete(item)

        db.commit()

        return {"message": "Cart item removed successfully"}

    except Exception:
        db.rollback()
        raise