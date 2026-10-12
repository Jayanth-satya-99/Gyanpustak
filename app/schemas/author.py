from pydantic import BaseModel


class AuthorResponse(BaseModel):
    author: str
    book_count: int


class AuthorBookResponse(BaseModel):
    isbn: str
    title: str
    publisher: str | None = None
    price_b: int | None = None
    average_rating: float | None = None
    total_reviews: int = 0