from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApiCartItem(Base):
    __tablename__ = "API_CART_ITEMS"

    cart_id: Mapped[int] = mapped_column(
        "CART_ID",
        Integer,
        ForeignKey("API_CARTS.CART_ID"),
        primary_key=True,
    )

    isbn: Mapped[str] = mapped_column(
        "ISBN",
        String(100),
        ForeignKey("BOOK.ISBN"),
        primary_key=True,
    )

    purchase_option: Mapped[str] = mapped_column(
        "PURCH_OPTION",
        String(10),
        primary_key=True,
    )

    quantity: Mapped[int] = mapped_column(
        "QUANTITY",
        Integer,
        nullable=False,
        default=1,
    )