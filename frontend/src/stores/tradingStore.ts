import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tradingService } from '@/services/tradingService'
import type { Trade, Position, PaginationParams } from '@/types'

export const useTradingStore = defineStore('trading', () => {
  // State
  const trades = ref<Trade[]>([])
  const positions = ref<Position[]>([])
  const currentTrade = ref<Trade | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Pagination state
  const currentPage = ref(1)
  const pageSize = ref(10)
  const totalTrades = ref(0)

  // Computed
  const totalPages = computed(() => Math.ceil(totalTrades.value / pageSize.value))
  const hasPositions = computed(() => positions.value.length > 0)
  const totalUnrealizedPnL = computed(() =>
    positions.value.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
  )

  // Actions
  const fetchTrades = async (params?: PaginationParams) => {
    loading.value = true
    error.value = null
    try {
      const paginationParams = params || {
        page: currentPage.value,
        limit: pageSize.value,
      }
      const response = await tradingService.getTrades(paginationParams)
      trades.value = response.items
      totalTrades.value = response.total
      currentPage.value = response.page
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch trades'
      console.error('Error fetching trades:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchTrade = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      currentTrade.value = await tradingService.getTrade(id)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch trade'
      console.error('Error fetching trade:', err)
    } finally {
      loading.value = false
    }
  }

  const createTrade = async (trade: Partial<Trade>) => {
    loading.value = true
    error.value = null
    try {
      const newTrade = await tradingService.createTrade(trade)
      trades.value.unshift(newTrade)
      return newTrade
    } catch (err: any) {
      error.value = err.message || 'Failed to create trade'
      console.error('Error creating trade:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const cancelTrade = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const cancelledTrade = await tradingService.cancelTrade(id)
      const index = trades.value.findIndex(t => t.id === id)
      if (index !== -1) {
        trades.value[index] = cancelledTrade
      }
      return cancelledTrade
    } catch (err: any) {
      error.value = err.message || 'Failed to cancel trade'
      console.error('Error cancelling trade:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchPositions = async () => {
    loading.value = true
    error.value = null
    try {
      positions.value = await tradingService.getPositions()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch positions'
      console.error('Error fetching positions:', err)
    } finally {
      loading.value = false
    }
  }

  const closePosition = async (symbol: string) => {
    loading.value = true
    error.value = null
    try {
      const closedPosition = await tradingService.closePosition(symbol)
      positions.value = positions.value.filter(p => p.symbol !== symbol)
      return closedPosition
    } catch (err: any) {
      error.value = err.message || 'Failed to close position'
      console.error('Error closing position:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const setPage = (page: number) => {
    currentPage.value = page
    fetchTrades()
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    trades,
    positions,
    currentTrade,
    loading,
    error,
    currentPage,
    pageSize,
    totalTrades,

    // Computed
    totalPages,
    hasPositions,
    totalUnrealizedPnL,

    // Actions
    fetchTrades,
    fetchTrade,
    createTrade,
    cancelTrade,
    fetchPositions,
    closePosition,
    setPage,
    clearError,
  }
})
