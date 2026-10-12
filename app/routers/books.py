from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.book import Book
from app.models.review_rating import ReviewRating
from app.schemas.book import BookResponse, BookListResponse

router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"],
)


# Calculate average rating and review count for each ISBN.
def get_rating_query(db: Session):
    return (
        db.query(
            ReviewRating.isbn.label("isbn"),
            func.avg(ReviewRating.rating).label("average_rating"),
            func.count(ReviewRating.rating).label("total_reviews"),
        )
        .filter(ReviewRating.rating.isnot(None))
        .group_by(ReviewRating.isbn)
        .subquery()
    )


def format_book(book, average_rating, total_reviews):
    result = BookResponse.model_validate(book).model_dump()

    result["average_rating"] = (
        round(float(average_rating), 2)
        if average_rating is not None
        else None
    )
    result["total_reviews"] = total_reviews or 0

    return result


@router.get("", response_model=BookListResponse)
def get_books(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    q: str | None = None,
    book_type: str | None = None,
    publisher: str | None = None,
    language: str | None = None,
    book_format: str | None = None,
    min_buy_price: int | None = Query(default=None, ge=0),
    max_buy_price: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    if (
        min_buy_price is not None
        and max_buy_price is not None
        and min_buy_price > max_buy_price
    ):
        raise HTTPException(
            status_code=422,
            detail="min_buy_price cannot exceed max_buy_price",
        )

    query = db.query(Book)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Book.isbn.ilike(pattern),
                Book.title.ilike(pattern),
                Book.publisher.ilike(pattern),
                Book.language.ilike(pattern),
                Book.format.ilike(pattern),
                Book.type.ilike(pattern),
            )
        )

    if book_type:
        query = query.filter(Book.type == book_type)

    if publisher:
        query = query.filter(
            Book.publisher.ilike(f"%{publisher.strip()}%")
        )

    if language:
        query = query.filter(
            Book.language.ilike(f"%{language.strip()}%")
        )

    if book_format:
        query = query.filter(
            Book.format.ilike(f"%{book_format.strip()}%")
        )

    if min_buy_price is not None:
        query = query.filter(Book.price_b >= min_buy_price)

    if max_buy_price is not None:
        query = query.filter(Book.price_b <= max_buy_price)

    total = query.with_entities(func.count(Book.isbn)).scalar() or 0

    rating_query = get_rating_query(db)

    rows = (
        query.outerjoin(
            rating_query,
            Book.isbn == rating_query.c.isbn,
        )
        .with_entities(
            Book,
            rating_query.c.average_rating,
            func.coalesce(rating_query.c.total_reviews, 0),
        )
        .order_by(Book.title.asc(), Book.isbn.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        format_book(book, average, count)
        for book, average, count in rows
    ]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items,
    }


@router.get("/search", response_model=BookListResponse)
def search_books(
    q: Annotated[str, Query(min_length=1)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    pattern = f"%{q.strip()}%"

    query = db.query(Book).filter(
        or_(
            Book.isbn.ilike(pattern),
            Book.title.ilike(pattern),
            Book.publisher.ilike(pattern),
            Book.language.ilike(pattern),
            Book.format.ilike(pattern),
            Book.type.ilike(pattern),
        )
    )

    total = query.with_entities(func.count(Book.isbn)).scalar() or 0

    rating_query = get_rating_query(db)

    rows = (
        query.outerjoin(
            rating_query,
            Book.isbn == rating_query.c.isbn,
        )
        .with_entities(
            Book,
            rating_query.c.average_rating,
            func.coalesce(rating_query.c.total_reviews, 0),
        )
        .order_by(Book.title.asc(), Book.isbn.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        format_book(book, average, count)
        for book, average, count in rows
    ]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items,
    }


@router.get("/{isbn}", response_model=BookResponse)
def get_book(
    isbn: str,
    db: Session = Depends(get_db),
):
    book = db.query(Book).filter(Book.isbn == isbn).first()

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    rating_query = get_rating_query(db)

    rating = (
        db.query(
            rating_query.c.average_rating,
            func.coalesce(rating_query.c.total_reviews, 0),
        )
        .filter(rating_query.c.isbn == isbn)
        .first()
    )

    if rating is None:
        average_rating = None
        total_reviews = 0
    else:
        average_rating, total_reviews = rating

    return format_book(book, average_rating, total_reviews)