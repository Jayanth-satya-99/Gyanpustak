from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApiRental(Base):
    __tablename__ = "API_RENTALS"

    __table_args__ = (
        ForeignKeyConstraint(
            ["ORDER_ID", "ISBN", "PURCH_OPTION"],
            [
                "API_ORDER_ITEMS.ORDER_ID",
                "API_ORDER_ITEMS.ISBN",
                "API_ORDER_ITEMS.PURCH_OPTION",
            ],
            name="fk_api_rentals_order_item",
        ),
        CheckConstraint(
            "PURCH_OPTION = 'Rent'",
            name="chk_api_rentals_option",
        ),
        CheckConstraint(
            "QUANTITY > 0",
            name="chk_api_rentals_quantity",
        ),
        CheckConstraint(
            "DUE_DATE >= RENTAL_START",
            name="chk_api_rentals_dates",
        ),
        CheckConstraint(
            "STATUS IN ('Active', 'Returned', 'Cancelled')",
            name="chk_api_rentals_status",
        ),
    )

    rental_id: Mapped[int] = mapped_column(
        "RENTAL_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[int] = mapped_column(
        "ORDER_ID",
        Integer,
        nullable=False,
    )

    isbn: Mapped[str] = mapped_column(
        "ISBN",
        String(100),
        nullable=False,
    )

    purchase_option: Mapped[str] = mapped_column(
        "PURCH_OPTION",
        String(10),
        nullable=False,
        default="Rent",
    )

    quantity: Mapped[int] = mapped_column(
        "QUANTITY",
        Integer,
        nullable=False,
    )

    rental_start: Mapped[date] = mapped_column(
        "RENTAL_START",
        Date,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        "DUE_DATE",
        Date,
        nullable=False,
    )

    returned_at: Mapped[datetime | None] = mapped_column(
        "RETURNED_AT",
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        "STATUS",
        String(20),
        nullable=False,
        default="Active",
    )