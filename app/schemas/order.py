from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

class OrderItemResponse(BaseModel):
    isbn:str
    purchase_option:str
    quantity: int
    unit_price: Decimal
    model_config=ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    order_id:int
    date_created: datetime
    order_status: str
    total_amount: Decimal
    items: list[OrderItemResponse]
    model_config=ConfigDict(from_attributes=True)

