from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.services.order_service import checkout
from app.services import order_history_service
from app.services.cancellation_service import cancel_order


router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
)


def get_student_id(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> int:
    if current_user["designation"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only students can place orders",
        )

    return current_user["user_id"]


@router.post("/checkout", status_code=201)
def checkout_cart(
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return checkout(db, student_id)

from app.services import order_history_service


@router.get("")
def list_student_orders(
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return order_history_service.list_orders(db, student_id)


@router.get("/{order_id}")
def get_student_order(
    order_id: int,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return order_history_service.get_order(
        db,
        student_id,
        order_id,
    )

@router.post("/{order_id}/cancel")
def cancel_student_order(
    order_id: int,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return cancel_order(
        db=db,
        student_id=student_id,
        order_id=order_id,
    )