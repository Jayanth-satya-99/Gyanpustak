from typing import Literal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    isbn: str = Field(min_length=1, max_length=100)
    purchase_option: Literal["Buy", "Rent"]
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    purchase_option: Literal["Buy", "Rent"] | None = None
    quantity: int | None = Field(default=None, gt=0)


class CartItemResponse(BaseModel):
    isbn: str
    title: str | None
    purchase_option: str
    quantity: int
    unit_price: int | None
    subtotal: int | None


class CartResponse(BaseModel):
    cart_id: int
    items: list[CartItemResponse]
    total: int