from pydantic import BaseModel


class CategoryResponse(BaseModel):
    category: str


class SubcategoryResponse(BaseModel):
    category: str
    subcategory: str


class CategoryBookResponse(BaseModel):
    isbn: str
    title: str
    publisher: str | None = None
    price_b: int | None = None
    average_rating: float | None = None
    total_reviews: int = 0