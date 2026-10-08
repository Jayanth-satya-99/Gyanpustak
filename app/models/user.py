from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "USER"

    user_id: Mapped[int] = mapped_column(
        "USER_ID",
        Integer,
        primary_key=True,
    )

    designation: Mapped[str] = mapped_column(
        "DESIGNATION",
        String(100),
        primary_key=True,
    )

    password: Mapped[int] = mapped_column(
        "PASSWORD",
        Integer,
        nullable=True,
    )


class AuthCredential(Base):
    __tablename__ = "AUTH_CREDENTIALS"

    user_id: Mapped[int] = mapped_column(
        "USER_ID",
        Integer,
        primary_key=True,
    )

    designation: Mapped[str] = mapped_column(
        "DESIGNATION",
        String(100),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(
        "PASSWORD_HASH",
        String(255),
        nullable=False,
    )