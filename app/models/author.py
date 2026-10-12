from sqlalchemy import Column, String, ForeignKey
from app.database.base import Base


class Author(Base):
    __tablename__ = "AUTHORS"

    isbn = Column(
        "ISBN",
        String(100),
        ForeignKey("BOOK.ISBN"),
        primary_key=True,
    )

    author = Column(
        "AUTHOR",
        String(100),
        primary_key=True,
    )