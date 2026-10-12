from pydantic import BaseModel, Field


class InventoryUpdate(BaseModel):
    quantity_change: int = Field(
        ...,
        description="Positive to increase stock, negative to decrease it.",
    )


class InventoryItem(BaseModel):
    isbn: str
    title: str | None = None
    quantity: int | None = None


class InventoryUpdateResponse(BaseModel):
    isbn: str
    previous_quantity: int
    quantity_change: int
    current_quantity: int
    message: str