from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "BOOK"

    isbn: Mapped[str] = mapped_column(
        "ISBN",#
        String(100),
        primary_key=True,
        nullable=False,
    )

    type: Mapped[str | None] = mapped_column(
        "TYPE",
        String(100),
        nullable=True,
    )

    price_r: Mapped[int | None] = mapped_column(
        "PRICE_R",
        Integer,
        nullable=True,
    )

    price_b: Mapped[int | None] = mapped_column(
        "PRICE_B",
        Integer,
        nullable=True,
    )

    quantity: Mapped[int | None] = mapped_column(
        "QUANTITY",
        Integer,
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(
        "TITLE",
        String(100),
        nullable=True,
    )

    publisher: Mapped[str | None] = mapped_column(
        "PUBLISHER",
        String(100),
        nullable=True,
    )

    publication_date: Mapped[date | None] = mapped_column(
        "PUBLICATION_DATE",
        Date,
        nullable=True,
    )

    edition_number: Mapped[int | None] = mapped_column(
        "EDITION_NUMBER",
        Integer,
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        "LANGUAGE",
        String(100),
        nullable=True,
    )

    format: Mapped[str | None] = mapped_column(
        "FORMAT",
        String(100),
        nullable=True,
    )