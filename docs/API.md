# API Documentation

## Trading API (Mock Data)

### Data Models

#### Trade
```typescript
{
  id: string
  symbol: string
  side: "buy" | "sell"
  price: number
  quantity: number
  status: "pending" | "executed" | "cancelled"
  timestamp: string (ISO format)
}
```

#### Position
```typescript
{
  id: string
  symbol: string
  quantity: number
  averagePrice: number
  currentPrice: number
  unrealizedPnL: number
  realizedPnL: number
}
```

### Endpoints

#### Trades (`/api/trades`)

**GET /api/trades** - List trades with pagination
- Query params: `page`, `limit`, `sortBy`, `sortOrder`
- Returns: `PaginatedResponse<Trade>`

**GET /api/trades/{id}** - Get single trade
- Params: `id` (trade ID)
- Returns: `Trade`

**POST /api/trades** - Create new trade
- Body: `CreateTradeRequest`
- Returns: `Trade`

**PATCH /api/trades/{id}/cancel** - Cancel trade
- Params: `id` (trade ID)
- Returns: `Trade`

#### Positions (`/api/positions`)

**GET /api/positions** - List all positions
- Returns: `Position[]`

**GET /api/positions/{symbol}** - Get single position
- Params: `symbol` (stock/crypto symbol)
- Returns: `Position`

**POST /api/positions/{symbol}/close** - Close position
- Params: `symbol` (stock/crypto symbol)
- Returns: `Position`

### Mock Data Configuration

- **Storage**: In-memory (resets on server restart)
- **Trades**: 20 pre-generated mock trades
- **Positions**: 5 pre-generated positions
- **Symbols**: AAPL, GOOGL, MSFT, TSLA, AMZN, NVDA, META, BTC, ETH, SPY

### API Response Examples

#### GET /api/trades
```json
{
  "items": [
    {
      "id": "uuid",
      "symbol": "AAPL",
      "side": "buy",
      "price": 175.50,
      "quantity": 10,
      "status": "executed",
      "timestamp": "2025-10-01T12:00:00"
    }
  ],
  "total": 20,
  "page": 1,
  "limit": 10,
  "totalPages": 2
}
```

#### GET /api/auth/me
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "google_id": "113705771254809700048"
}
```

## API Test Page

Location: `views/ApiTest.vue`

Features:
- Protected route (requires authentication)
- Tests all trading endpoints
- Trades list with pagination
- Create sample trade button
- Cancel pending trades
- Positions list with P&L
- Close positions
- Real-time total unrealized P&L
- Error and loading states

## Future Enhancements

- Real trading API integration (replace mock data)
- WebSocket for real-time price updates
- Order book visualization
- Advanced portfolio analytics
- Trade history charts and reporting
- API rate limiting improvements
