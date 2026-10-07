from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.book import Book
from app.schemas.book import BookResponse


router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"],
)



@router.get(
    "/search",
    response_model=list[BookResponse],
)
def search_books(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    search_pattern = f"%{q}%"

    books = (
        db.query(Book)
        .filter(
            or_(
                Book.title.ilike(search_pattern),
                Book.publisher.ilike(search_pattern),
                Book.language.ilike(search_pattern),
                Book.format.ilike(search_pattern),
            )
        )
        .all()
    )

    return books


@router.get(
    "",
    response_model=list[BookResponse],
)
def get_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    books = (
        db.query(Book)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return books


@router.get(
    "/{isbn}",
    response_model=BookResponse,
)
def get_book(
    isbn: str,
    db: Session = Depends(get_db),
):
    book = (
        db.query(Book)
        .filter(Book.isbn == isbn)
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    return book

