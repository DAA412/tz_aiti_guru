from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AddItemRequest(BaseModel):
    order_id: int = Field(..., description="ID заказа")
    product_id: int = Field(..., description="ID товара")
    quantity: int = Field(..., gt=0, description="Количество товара")


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    price: float

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    error_code: str


class SuccessResponse(BaseModel):
    message: str
    order_item: Optional[OrderItemResponse] = None
