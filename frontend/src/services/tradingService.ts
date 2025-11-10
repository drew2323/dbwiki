import { api } from './api'
import type { Trade, Position, PaginatedResponse, PaginationParams } from '@/types'

export const tradingService = {
  // Get all trades with pagination
  getTrades: async (params?: PaginationParams): Promise<PaginatedResponse<Trade>> => {
    const response = await api.get<PaginatedResponse<Trade>>('/trades', { params })
    return response.data
  },

  // Get a single trade by ID
  getTrade: async (id: string): Promise<Trade> => {
    const response = await api.get<Trade>(`/trades/${id}`)
    return response.data
  },

  // Create a new trade
  createTrade: async (trade: Partial<Trade>): Promise<Trade> => {
    const response = await api.post<Trade>('/trades', trade)
    return response.data
  },

  // Update a trade
  updateTrade: async (id: string, trade: Partial<Trade>): Promise<Trade> => {
    const response = await api.put<Trade>(`/trades/${id}`, trade)
    return response.data
  },

  // Cancel a trade
  cancelTrade: async (id: string): Promise<Trade> => {
    const response = await api.patch<Trade>(`/trades/${id}/cancel`)
    return response.data
  },

  // Get all positions
  getPositions: async (): Promise<Position[]> => {
    const response = await api.get<Position[]>('/positions')
    return response.data
  },

  // Get a single position by symbol
  getPosition: async (symbol: string): Promise<Position> => {
    const response = await api.get<Position>(`/positions/${symbol}`)
    return response.data
  },

  // Close a position
  closePosition: async (symbol: string): Promise<Position> => {
    const response = await api.post<Position>(`/positions/${symbol}/close`)
    return response.data
  },
}
