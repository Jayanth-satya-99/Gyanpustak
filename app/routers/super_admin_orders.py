from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.api_order import ApiOrder
from app.models.api_order_item import ApiOrderItem
from app.models.book import Book
from app.services.cancellation_service import cancel_order
from app.schemas.admin_order import (
    AdminOrderDetail,
    AdminOrderSummary,
    OrderStatisticsResponse,
)


router = APIRouter(
    prefix="/api/v1/super-admin/orders",
    tags=["Super Administrator - Orders"],
)


def require_super_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=403,
            detail="Super Administrator access required.",
        )

    return current_user


# --------------------------------------------------
# LIST ORDERS
# GET /api/v1/super-admin/orders
# --------------------------------------------------

@router.get("", response_model=list[AdminOrderSummary])
def list_orders(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    student_id: int | None = Query(default=None, gt=0),
    order_status: str | None = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    query = db.query(ApiOrder)

    if student_id is not None:
        query = query.filter(
            ApiOrder.student_id == student_id,
        )

    if order_status:
        query = query.filter(
            ApiOrder.order_status == order_status,
        )

    return (
        query.order_by(ApiOrder.order_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------
# ORDER STATISTICS
# GET /api/v1/super-admin/orders/statistics
# --------------------------------------------------

@router.get(
    "/statistics",
    response_model=OrderStatisticsResponse,
)
def get_order_statistics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    total_orders = (
        db.query(func.count(ApiOrder.order_id))
        .scalar()
        or 0
    )

    # Exclude cancelled orders from revenue.
    total_revenue = (
        db.query(func.coalesce(func.sum(ApiOrder.total_amount), 0))
        .filter(ApiOrder.order_status != "Cancelled")
        .scalar()
    )

    status_rows = (
        db.query(
            ApiOrder.order_status,
            func.count(ApiOrder.order_id),
        )
        .group_by(ApiOrder.order_status)
        .order_by(ApiOrder.order_status)
        .all()
    )

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "orders_by_status": [
            {
                "order_status": order_status,
                "count": count,
            }
            for order_status, count in status_rows
        ],
    }


# --------------------------------------------------
# ORDER DETAILS
# GET /api/v1/super-admin/orders/{order_id}
# --------------------------------------------------

@router.get(
    "/{order_id}",
    response_model=AdminOrderDetail,
)
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    order = db.get(ApiOrder, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found.",
        )

    rows = (
        db.query(
            ApiOrderItem,
            Book.title,
        )
        .join(
            Book,
            Book.isbn == ApiOrderItem.isbn,
        )
        .filter(
            ApiOrderItem.order_id == order_id,
        )
        .order_by(
            ApiOrderItem.isbn,
            ApiOrderItem.purchase_option,
        )
        .all()
    )

    items = [
        {
            "isbn": item.isbn,
            "title": title,
            "purchase_option": item.purchase_option,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
        }
        for item, title in rows
    ]

    return {
        "order_id": order.order_id,
        "student_id": order.student_id,
        "date_created": order.date_created,
        "order_status": order.order_status,
        "total_amount": order.total_amount,
        "items": items,
    }


# --------------------------------------------------
# CANCEL ORDER
# POST /api/v1/super-admin/orders/{order_id}/cancel
# --------------------------------------------------

@router.post("/{order_id}/cancel")
def cancel_order_as_admin(
    order_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    order = db.get(ApiOrder, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found.",
        )

    # Reuse the existing service to restore inventory
    # and cancel active rentals consistently.
    return cancel_order(
        db=db,
        student_id=order.student_id,
        order_id=order_id,
    )