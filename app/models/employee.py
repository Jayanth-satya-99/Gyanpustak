from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Employee(Base):
    __tablename__ = "EMPLOYEE"

    employee_id: Mapped[int] = mapped_column(
        "EMPLOYEE_ID",
        Integer,
        primary_key=True,
        nullable=False,
    )

    first_name: Mapped[str | None] = mapped_column(
        "FIRST_NAME",
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        "LAST_NAME",
        String(100),
        nullable=True,
    )

    gender: Mapped[str | None] = mapped_column(
        "GENDER",
        String(100),
        nullable=True,
    )

    salary: Mapped[int | None] = mapped_column(
        "SALARY",
        Integer,
        nullable=True,
    )

    aadhar_number: Mapped[str | None] = mapped_column(
        "AADHAR_NUMBER",
        String(100),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        "EMAIL",
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        "ADDRESS",
        String(100),
        nullable=True,
    )

    telephone_number: Mapped[str | None] = mapped_column(
        "TELEPHONE_NUMBER",
        String(20),
        nullable=True,
    )

    designation: Mapped[str | None] = mapped_column(
        "DESIGNATION",
        String(100),
        nullable=True,
    )