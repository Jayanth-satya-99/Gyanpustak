from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.base import Base


class ReviewRating(Base):
    __tablename__ = "REVIEW_RATING"

    isbn = Column(
        "ISBN",
        String(100),
        ForeignKey("BOOK.ISBN"),
        primary_key=True
    )

    student_id = Column(
        "STUDENT_ID",
        Integer,
        ForeignKey("STUDENTS.STUDENT_ID"),
        primary_key=True
    )

    review = Column("REVIEW", String(300), nullable=True)
    rating = Column("RATING", Integer, nullable=True)