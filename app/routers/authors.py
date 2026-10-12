from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.author import Author
from app.models.book import Book
from app.schemas.author import AuthorResponse, AuthorBookResponse
from app.routers.books import get_rating_query, format_book

router = APIRouter(
    prefix="/api/v1/authors",
    tags=["Authors"],
)


@router.get("", response_model=list[AuthorResponse])
def get_authors(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Author.author,
            func.count(Author.isbn).label("book_count"),
        )
        .group_by(Author.author)
        .order_by(Author.author.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "author": author,
            "book_count": book_count,
        }
        for author, book_count in rows
    ]


@router.get("/{author_name}/books", response_model=list[AuthorBookResponse])
def get_books_by_author(
    author_name: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    rating_query = get_rating_query(db)

    rows = (
        db.query(Book, rating_query.c.average_rating,
                 func.coalesce(rating_query.c.total_reviews, 0))
        .join(Author, Author.isbn == Book.isbn)
        .outerjoin(rating_query, Book.isbn == rating_query.c.isbn)
        .filter(Author.author == author_name)
        .order_by(Book.title.asc(), Book.isbn.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        format_book(book, average_rating, total_reviews)
        for book, average_rating, total_reviews in rows
    ]