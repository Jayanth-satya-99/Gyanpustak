from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    review: str | None = Field(default=None, max_length=300)
    rating: int = Field(ge=1, le=5)


class ReviewUpdate(BaseModel):
    review: str | None = Field(default=None, max_length=300)
    rating: int = Field(ge=1, le=5)


class ReviewResponse(BaseModel):
    isbn: str
    student_id: int
    review: str | None
    rating: int | None

    model_config = ConfigDict(from_attributes=True)


class BookRatingResponse(BaseModel):
    isbn: str
    average_rating: float | None
    total_reviews: int