from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.book import Book
from app.schemas.inventory import (
    InventoryItem,
    InventoryUpdate,
    InventoryUpdateResponse,
)


router = APIRouter(
    prefix="/api/v1/super-admin/inventory",
    tags=["Super Administrator - Inventory"],
)


def require_super_admin(
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=403,
            detail="Super Administrator access required.",
        )

    return current_user


# --------------------------------------------------
# LIST INVENTORY
# GET /api/v1/super-admin/inventory
# --------------------------------------------------

@router.get("", response_model=list[InventoryItem])
def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    query = db.query(Book)

    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Book.isbn.ilike(pattern),
                Book.title.ilike(pattern),
            )
        )

    books = (
        query.order_by(Book.title.asc(), Book.isbn.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "isbn": book.isbn,
            "title": book.title,
            "quantity": book.quantity,
        }
        for book in books
    ]


# --------------------------------------------------
# LOW-STOCK REPORT
# GET /api/v1/super-admin/inventory/low-stock
# --------------------------------------------------

@router.get("/low-stock", response_model=list[InventoryItem])
def get_low_stock(
    threshold: int = Query(5, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    books = (
        db.query(Book)
        .filter(
            Book.quantity.is_not(None),
            Book.quantity <= threshold,
        )
        .order_by(Book.quantity.asc(), Book.title.asc())
        .all()
    )

    return [
        {
            "isbn": book.isbn,
            "title": book.title,
            "quantity": book.quantity,
        }
        for book in books
    ]


# --------------------------------------------------
# UPDATE STOCK
# PATCH /api/v1/super-admin/inventory/{isbn}
# --------------------------------------------------

@router.patch(
    "/{isbn}",
    response_model=InventoryUpdateResponse,
)
def update_inventory(
    isbn: str,
    request: InventoryUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    try:
        book = db.scalar(
            select(Book)
            .where(Book.isbn == isbn)
            .with_for_update()
        )

        if book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found.",
            )

        if book.quantity is None:
            raise HTTPException(
                status_code=409,
                detail="Book quantity is not initialized.",
            )

        previous_quantity = book.quantity
        new_quantity = previous_quantity + request.quantity_change

        if new_quantity < 0:
            raise HTTPException(
                status_code=409,
                detail="Stock cannot become negative.",
            )

        book.quantity = new_quantity
        db.commit()

        return {
            "isbn": book.isbn,
            "previous_quantity": previous_quantity,
            "quantity_change": request.quantity_change,
            "current_quantity": new_quantity,
            "message": "Inventory updated successfully.",
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise