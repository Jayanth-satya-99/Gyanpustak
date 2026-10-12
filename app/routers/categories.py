from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.book_category import BookCategory
from app.models.book import Book
from app.models.category import Category, Subcategory
from app.schemas.category import (
    CategoryResponse,
    SubcategoryResponse,
    CategoryBookResponse,
)
from app.routers.books import get_rating_query, format_book


router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Categories"],
)


# --------------------------------------------------
# LIST ALL CATEGORIES
# GET /api/v1/categories
# --------------------------------------------------

@router.get("", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
):
    categories = (
        db.query(Category)
        .order_by(Category.category_name.asc())
        .all()
    )

    return [
        {"category": category.category_name}
        for category in categories
    ]


# --------------------------------------------------
# LIST SUBCATEGORIES
# GET /api/v1/categories/{category_name}/subcategories
# --------------------------------------------------

@router.get(
    "/{category_name}/subcategories",
    response_model=list[SubcategoryResponse],
)
def get_subcategories(
    category_name: str,
    db: Session = Depends(get_db),
):
    category = db.get(Category, category_name)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    subcategories = (
        db.query(Subcategory)
        .filter(Subcategory.category_name == category_name)
        .order_by(Subcategory.subcategory_name.asc())
        .all()
    )

    return [
        {
            "category": subcategory.category_name,
            "subcategory": subcategory.subcategory_name,
        }
        for subcategory in subcategories
    ]


# --------------------------------------------------
# GET BOOKS BY CATEGORY
# GET /api/v1/categories/{category_name}/books
# --------------------------------------------------

@router.get(
    "/{category_name}/books",
    response_model=list[CategoryBookResponse],
)
def get_books_by_category(
    category_name: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    rating_query = get_rating_query(db)

    rows = (
        db.query(
            Book,
            rating_query.c.average_rating,
            rating_query.c.total_reviews,
        )
        .join(BookCategory, BookCategory.isbn == Book.isbn)
        .outerjoin(rating_query, Book.isbn == rating_query.c.isbn)
        .filter(BookCategory.category == category_name)
        .order_by(Book.title.asc(), Book.isbn.asc())
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        format_book(book, average_rating, total_reviews)
        for book, average_rating, total_reviews in rows
    ]


# --------------------------------------------------
# GET BOOKS BY SUBCATEGORY
# GET /api/v1/categories/{category_name}/subcategories/{subcategory_name}/books
# --------------------------------------------------

@router.get(
    "/{category_name}/subcategories/{subcategory_name}/books",
    response_model=list[CategoryBookResponse],
)
def get_books_by_subcategory(
    category_name: str,
    subcategory_name: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    rating_query = get_rating_query(db)

    rows = (
        db.query(
            Book,
            rating_query.c.average_rating,
            rating_query.c.total_reviews,
        )
        .join(BookCategory, BookCategory.isbn == Book.isbn)
        .outerjoin(rating_query, Book.isbn == rating_query.c.isbn)
        .filter(
            BookCategory.category == category_name,
            BookCategory.subcategory == subcategory_name,
        )
        .order_by(Book.title.asc(), Book.isbn.asc())
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        format_book(book, average_rating, total_reviews)
        for book, average_rating, total_reviews in rows
    ]