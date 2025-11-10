// Common API response types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  message: string
  code?: string
  details?: any
}

// Pagination types
export interface PaginationParams {
  page: number
  limit: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// Example domain types (adjust based on your backend models)
export interface User {
  id: string
  username: string
  email: string
  createdAt: string
  updatedAt: string
}

export interface Trade {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  price: number
  quantity: number
  timestamp: string
  status: 'pending' | 'executed' | 'cancelled'
}

export interface Position {
  id: string
  symbol: string
  quantity: number
  averagePrice: number
  currentPrice: number
  unrealizedPnL: number
  realizedPnL: number
}

// WebSocket message types
export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp: string
}
