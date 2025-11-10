from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math
import uuid
from datetime import datetime

from app.models.trade import Trade, TradeCreate, PaginatedTradesResponse
from app.utils.mock_data import mock_trades, generate_trade

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("", response_model=PaginatedTradesResponse)
async def get_trades(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sortBy: Optional[str] = Query(None),
    sortOrder: Optional[str] = Query("desc")
):
    """Get paginated list of trades"""
    # Sort trades by timestamp (most recent first by default)
    sorted_trades = sorted(
        mock_trades,
        key=lambda t: t.timestamp,
        reverse=(sortOrder == "desc")
    )

    # Calculate pagination
    total = len(sorted_trades)
    total_pages = math.ceil(total / limit)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit

    # Get paginated items
    items = sorted_trades[start_idx:end_idx]

    return PaginatedTradesResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        totalPages=total_pages
    )


@router.get("/{trade_id}", response_model=Trade)
async def get_trade(trade_id: str):
    """Get a single trade by ID"""
    trade = next((t for t in mock_trades if t.id == trade_id), None)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("", response_model=Trade, status_code=201)
async def create_trade(trade_data: TradeCreate):
    """Create a new trade"""
    new_trade = Trade(
        id=str(uuid.uuid4()),
        symbol=trade_data.symbol,
        side=trade_data.side,
        price=trade_data.price,
        quantity=trade_data.quantity,
        status="pending",
        timestamp=datetime.now().isoformat()
    )
    mock_trades.insert(0, new_trade)
    return new_trade


@router.patch("/{trade_id}/cancel", response_model=Trade)
async def cancel_trade(trade_id: str):
    """Cancel a trade"""
    trade = next((t for t in mock_trades if t.id == trade_id), None)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status == "executed":
        raise HTTPException(status_code=400, detail="Cannot cancel executed trade")

    if trade.status == "cancelled":
        raise HTTPException(status_code=400, detail="Trade is already cancelled")

    # Update trade status
    trade.status = "cancelled"
    return trade
