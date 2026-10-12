from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Category(Base):
    __tablename__ = "CATEGORY"

    category_name: Mapped[str] = mapped_column(
        "CATEGORY_NAME",
        String(100),
        primary_key=True,
    )


class Subcategory(Base):
    __tablename__ = "SUBCATEGORY"

    category_name: Mapped[str] = mapped_column(
        "CATEGORY_NAME",
        String(100),
        ForeignKey("CATEGORY.CATEGORY_NAME"),
        primary_key=True,
    )

    subcategory_name: Mapped[str] = mapped_column(
        "SUBCATEGORY_NAME",
        String(100),
        primary_key=True,
    )