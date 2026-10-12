from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    BookRatingResponse,
)
from app.services.review_service import (
    create_review,
    get_book_reviews,
    update_review,
    delete_review,
    get_book_rating,
)

router = APIRouter(tags=["Reviews"])


def require_student(current_user: dict):
    if current_user.get("designation") != "Student":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Only students can perform this operation",
        )

    return current_user


@router.post(
    "/api/v1/books/{isbn}/reviews",
    response_model=ReviewResponse,
    status_code=201,
)
def add_review(
    isbn: str,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    return create_review(
        db=db,
        isbn=isbn,
        student_id=current_user["user_id"],
        review=data.review,
        rating=data.rating,
    )


@router.get(
    "/api/v1/books/{isbn}/reviews",
    response_model=list[ReviewResponse],
)
def list_reviews(
    isbn: str,
    db: Session = Depends(get_db),
):
    return get_book_reviews(db, isbn)


@router.patch(
    "/api/v1/books/{isbn}/reviews",
    response_model=ReviewResponse,
)
def edit_review(
    isbn: str,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    return update_review(
        db=db,
        isbn=isbn,
        student_id=current_user["user_id"],
        review=data.review,
        rating=data.rating,
    )


@router.delete("/api/v1/books/{isbn}/reviews", status_code=204)
def remove_review(
    isbn: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)

    delete_review(
        db=db,
        isbn=isbn,
        student_id=current_user["user_id"],
    )


@router.get(
    "/api/v1/books/{isbn}/rating",
    response_model=BookRatingResponse,
)
def book_rating(
    isbn: str,
    db: Session = Depends(get_db),
):
    return get_book_rating(db, isbn)