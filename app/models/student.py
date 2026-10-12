from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Student(Base):
    __tablename__ = "STUDENTS"

    student_id: Mapped[int] = mapped_column(
        "STUDENT_ID",
        Integer,
        primary_key=True,
        autoincrement=False,
    )

    name: Mapped[str | None] = mapped_column(
        "NAME", String(100), nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        "EMAIL", String(100), nullable=True
    )

    phone_number: Mapped[str | None] = mapped_column(
    "PHONE_NUMBER", String(20), nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        "ADDRESS", String(100), nullable=True
    )

    dob: Mapped[date | None] = mapped_column(
        "DOB", Date, nullable=True
    )

    university_id: Mapped[int | None] = mapped_column(
        "UNIVERSITY_ID", Integer, nullable=True
    )

    major_field: Mapped[str | None] = mapped_column(
        "MAJOR_FIELD", String(100), nullable=True
    )

    status: Mapped[str | None] = mapped_column(
        "STATUS", String(100), nullable=True
    )

    current_yearofstudy: Mapped[int | None] = mapped_column(
        "CURRENT_YEAROFSTUDY", Integer, nullable=True
    )

    approval_status: Mapped[str] = mapped_column(
        "APPROVAL_STATUS",
        String(20),
        nullable=False,
        default="PENDING",
    )