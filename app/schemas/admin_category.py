from pydantic import BaseModel, Field, field_validator


class CategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)

    @field_validator("category_name")
    @classmethod
    def validate_category_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Category name cannot be empty")

        return value


class SubcategoryCreate(BaseModel):
    subcategory_name: str = Field(min_length=1, max_length=100)

    @field_validator("subcategory_name")
    @classmethod
    def validate_subcategory_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Subcategory name cannot be empty")

        return value


class CategoryResponse(BaseModel):
    category_name: str


class SubcategoryResponse(BaseModel):
    category_name: str
    subcategory_name: str


class MessageResponse(BaseModel):
    message: str