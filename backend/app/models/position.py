from pydantic import BaseModel, Field


class Position(BaseModel):
    id: str
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float
    averagePrice: float = Field(..., gt=0)
    currentPrice: float = Field(..., gt=0)
    unrealizedPnL: float
    realizedPnL: float

    class Config:
        from_attributes = True
