from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApiOrder(Base):
    __tablename__ = "API_ORDERS"

    order_id: Mapped[int] = mapped_column(
        "ORDER_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    student_id: Mapped[int] = mapped_column(
        "STUDENT_ID",
        ForeignKey("STUDENTS.STUDENT_ID"),
        nullable=False,
    )

    date_created: Mapped[datetime] = mapped_column(
        "DATE_CREATED",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    order_status: Mapped[str] = mapped_column(
        "ORDER_STATUS",
        String(30),
        nullable=False,
        server_default=text("'Pending'"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        "TOTAL_AMOUNT",
        Numeric(10, 2),
        nullable=False,
        server_default=text("0.00"),
    )