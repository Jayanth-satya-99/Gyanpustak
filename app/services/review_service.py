from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.review_rating import ReviewRating
from app.models.book import Book


def create_review(
    db: Session,
    isbn: str,
    student_id: int,
    review: str | None,
    rating: int,
):
    book = db.query(Book).filter(Book.isbn == isbn).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = (
        db.query(ReviewRating)
        .filter(
            ReviewRating.isbn == isbn,
            ReviewRating.student_id == student_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this book",
        )

    new_review = ReviewRating(
        isbn=isbn,
        student_id=student_id,
        review=review,
        rating=rating,
    )

    try:
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        return new_review
    except Exception:
        db.rollback()
        raise


def get_book_reviews(db: Session, isbn: str):
    book = db.query(Book).filter(Book.isbn == isbn).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return (
        db.query(ReviewRating)
        .filter(ReviewRating.isbn == isbn)
        .order_by(ReviewRating.student_id)
        .all()
    )


def update_review(
    db: Session,
    isbn: str,
    student_id: int,
    review: str | None,
    rating: int,
):
    existing = (
        db.query(ReviewRating)
        .filter(
            ReviewRating.isbn == isbn,
            ReviewRating.student_id == student_id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")

    existing.review = review
    existing.rating = rating

    try:
        db.commit()
        db.refresh(existing)
        return existing
    except Exception:
        db.rollback()
        raise


def delete_review(db: Session, isbn: str, student_id: int):
    existing = (
        db.query(ReviewRating)
        .filter(
            ReviewRating.isbn == isbn,
            ReviewRating.student_id == student_id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")

    try:
        db.delete(existing)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_book_rating(db: Session, isbn: str):
    from sqlalchemy import func

    book = db.query(Book).filter(Book.isbn == isbn).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    average, total = (
        db.query(
            func.avg(ReviewRating.rating),
            func.count(ReviewRating.rating),
        )
        .filter(
            ReviewRating.isbn == isbn,
            ReviewRating.rating.isnot(None),
        )
        .first()
    )

    return {
        "isbn": isbn,
        "average_rating": round(float(average), 2) if average is not None else None,
        "total_reviews": total,
    }