from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from app.services import cart_service


router = APIRouter(
    prefix="/api/v1/cart",
    tags=["Cart"],
)


def get_student_id(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> int:
    if current_user["designation"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access carts",
        )

    return current_user["user_id"]


@router.get("", response_model=CartResponse)
def view_cart(
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return cart_service.get_cart(db, student_id)


@router.post("/items", status_code=201)
def add_cart_item(
    item: CartItemCreate,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return cart_service.add_item(
        db=db,
        student_id=student_id,
        isbn=item.isbn,
        purchase_option=item.purchase_option,
        quantity=item.quantity,
    )


@router.patch("/items/{isbn}")
def update_cart_item(
    isbn: str,
    item: CartItemUpdate,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return cart_service.update_item(
        db=db,
        student_id=student_id,
        isbn=isbn,
        quantity=item.quantity,
        purchase_option=item.purchase_option,
    )


@router.delete("/items/{isbn}")
def delete_cart_item(
    isbn: str,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return cart_service.remove_item(
        db=db,
        student_id=student_id,
        isbn=isbn,
    )