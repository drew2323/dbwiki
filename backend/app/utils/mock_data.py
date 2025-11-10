import random
import uuid
from datetime import datetime, timedelta
from typing import Literal
from app.models.trade import Trade
from app.models.position import Position


# Mock data storage
mock_trades: list[Trade] = []
mock_positions: list[Position] = []

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "BTC", "ETH", "SPY"]


def generate_trade(
    symbol: str | None = None,
    side: Literal["buy", "sell"] | None = None,
    status: Literal["pending", "executed", "cancelled"] | None = None
) -> Trade:
    """Generate a mock trade"""
    return Trade(
        id=str(uuid.uuid4()),
        symbol=symbol or random.choice(SYMBOLS),
        side=side or random.choice(["buy", "sell"]),
        price=round(random.uniform(50, 500), 2),
        quantity=round(random.uniform(1, 100), 2),
        status=status or random.choice(["pending", "executed", "cancelled"]),
        timestamp=(datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat()
    )


def generate_position(symbol: str | None = None) -> Position:
    """Generate a mock position"""
    avg_price = round(random.uniform(50, 500), 2)
    current_price = avg_price * random.uniform(0.85, 1.15)
    quantity = round(random.uniform(10, 500), 2)

    unrealized_pnl = (current_price - avg_price) * quantity
    realized_pnl = round(random.uniform(-1000, 2000), 2)

    return Position(
        id=str(uuid.uuid4()),
        symbol=symbol or random.choice(SYMBOLS),
        quantity=quantity,
        averagePrice=avg_price,
        currentPrice=round(current_price, 2),
        unrealizedPnL=round(unrealized_pnl, 2),
        realizedPnL=realized_pnl
    )


def initialize_mock_data():
    """Initialize mock data storage with sample data"""
    global mock_trades, mock_positions

    # Generate 20 mock trades
    mock_trades = [generate_trade() for _ in range(20)]

    # Generate 5 mock positions (one for each unique symbol)
    used_symbols = set()
    mock_positions = []
    for _ in range(5):
        symbol = random.choice([s for s in SYMBOLS if s not in used_symbols])
        used_symbols.add(symbol)
        mock_positions.append(generate_position(symbol=symbol))


# Initialize on module load
initialize_mock_data()
