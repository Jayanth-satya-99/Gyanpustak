from datetime import date

from pydantic import BaseModel, ConfigDict


class BookResponse(BaseModel):
    isbn: str
    type: str | None
    price_r: int | None
    price_b: int | None
    quantity: int | None
    title: str | None
    publisher: str | None
    publication_date: date | None
    edition_number: int | None
    language: str | None
    format: str | None
    average_rating: float | None = None
    total_reviews: int = 0

    model_config = ConfigDict(from_attributes=True)


class BookListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[BookResponse]