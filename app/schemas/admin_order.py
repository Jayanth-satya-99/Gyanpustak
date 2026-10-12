from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AdminOrderItemResponse(BaseModel):
    isbn: str
    title: str | None = None
    purchase_option: str
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class AdminOrderSummary(BaseModel):
    order_id: int
    student_id: int
    date_created: datetime
    order_status: str
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class AdminOrderDetail(AdminOrderSummary):
    items: list[AdminOrderItemResponse]


class OrderStatusStatistics(BaseModel):
    order_status: str
    count: int


class OrderStatisticsResponse(BaseModel):
    total_orders: int
    total_revenue: Decimal
    orders_by_status: list[OrderStatusStatistics]