from sqlalchemy import Column, String, ForeignKey
from app.database.base import Base


class BookCategory(Base):
    __tablename__ = "BOOK_CATEGORY"

    category = Column(
        "CATEGORY",
        String(100),
        primary_key=True,
    )

    isbn = Column(
        "ISBN",
        String(100),
        ForeignKey("BOOK.ISBN"),
        primary_key=True,
    )

    subcategory = Column(
        "SUBCATEGORY",
        String(100),
        primary_key=True,
    )