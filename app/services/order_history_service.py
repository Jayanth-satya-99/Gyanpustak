from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_order import ApiOrder
from app.models.api_order_item import ApiOrderItem

def list_orders(db:Session,student_id:int)->list[dict]:
    orders=db.scalars(
        select(ApiOrder)
        .where(ApiOrder.student_id==student_id)
        .order_by(ApiOrder.date_created.desc(),ApiOrder.order_id.desc())
    ).all()

    return [
        {
            "order_id": order.order_id,
            "date_created": order.date_created,
            "order_status": order.order_status,
            "total_amount": order.total_amount,
            "items": [],
        }
        for order in orders
    ]


def get_order(
    db: Session,
    student_id: int,
    order_id: int,
) -> dict:
    order = db.scalar(
        select(ApiOrder).where(
            ApiOrder.order_id == order_id,
            ApiOrder.student_id == student_id,
        )
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    items = db.scalars(
        select(ApiOrderItem).where(
            ApiOrderItem.order_id == order.order_id
        )
    ).all()

    return {
        "order_id": order.order_id,
        "date_created": order.date_created,
        "order_status": order.order_status,
        "total_amount": order.total_amount,
        "items": [
            {
                "isbn": item.isbn,
                "purchase_option": item.purchase_option,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in items
        ],
    }