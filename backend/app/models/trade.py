from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class TradeBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    side: Literal["buy", "sell"]
    price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)


class TradeCreate(TradeBase):
    pass


class Trade(TradeBase):
    id: str
    status: Literal["pending", "executed", "cancelled"] = "pending"
    timestamp: str

    class Config:
        from_attributes = True


class PaginatedTradesResponse(BaseModel):
    items: list[Trade]
    total: int
    page: int
    limit: int
    totalPages: int
