from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApiCart(Base):
    __tablename__ = "API_CARTS"

    cart_id: Mapped[int] = mapped_column(
        "CART_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    student_id: Mapped[int] = mapped_column(
        "STUDENT_ID",
        ForeignKey("STUDENTS.STUDENT_ID"),
        unique=True,
        nullable=False,
    )

    date_create: Mapped[datetime] = mapped_column(
        "DATE_CREATE",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    date_last_update: Mapped[datetime] = mapped_column(
        "DATE_LAST_UPDATE",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )