from fastapi import APIRouter, HTTPException

from app.models.position import Position
from app.utils.mock_data import mock_positions

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=list[Position])
async def get_positions():
    """Get all positions"""
    return mock_positions


@router.get("/{symbol}", response_model=Position)
async def get_position(symbol: str):
    """Get a single position by symbol"""
    position = next((p for p in mock_positions if p.symbol == symbol), None)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/{symbol}/close", response_model=Position)
async def close_position(symbol: str):
    """Close a position"""
    position = next((p for p in mock_positions if p.symbol == symbol), None)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Remove position from list (simulating closing)
    mock_positions.remove(position)

    # Return the closed position
    return position
