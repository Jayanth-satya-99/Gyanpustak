from datetime import date

from pydantic import BaseModel, Field, field_validator


class BookCreate(BaseModel):
    isbn: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=100)

    type: str = Field(min_length=1, max_length=100)

    price_r: int | None = Field(default=None, ge=0)
    price_b: int | None = Field(default=None, ge=0)
    quantity: int = Field(ge=0)

    publisher: str | None = Field(default=None, max_length=100)
    publication_date: date | None = None
    edition_number: int | None = Field(default=None, ge=1)
    language: str | None = Field(default=None, max_length=100)
    format: str | None = Field(default=None, max_length=100)

    authors: list[str] = Field(min_length=1)
    category: str = Field(min_length=1, max_length=100)
    subcategories: list[str] = Field(default_factory=list)

    @field_validator("isbn", "title", "type", "category")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("authors", "subcategories")
    @classmethod
    def strip_list_values(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Duplicate values are not allowed.")

        return cleaned


class BookDeleteResponse(BaseModel):
    isbn: str
    message: str