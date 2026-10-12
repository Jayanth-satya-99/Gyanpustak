from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApiOrderItem(Base):
    __tablename__ = "API_ORDER_ITEMS"

    order_id: Mapped[int] = mapped_column(
        "ORDER_ID",
        Integer,
        ForeignKey("API_ORDERS.ORDER_ID"),
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
    )

    unit_price: Mapped[Decimal] = mapped_column(
        "UNIT_PRICE",
        Numeric(10, 2),
        nullable=False,
    )