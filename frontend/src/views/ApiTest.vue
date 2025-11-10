<template>
  <div class="api-test">
    <h1>API Integration Test</h1>

    <!-- Error Display -->
    <div v-if="store.error" class="error">
      {{ store.error }}
      <button @click="store.clearError">Clear</button>
    </div>

    <!-- Loading Indicator -->
    <div v-if="store.loading" class="loading">Loading...</div>

    <!-- Trades Section -->
    <section class="section">
      <h2>Trades ({{ store.totalTrades }})</h2>
      <div class="actions">
        <button @click="store.fetchTrades()" :disabled="store.loading">
          Refresh Trades
        </button>
        <button @click="createSampleTrade" :disabled="store.loading">
          Create Sample Trade
        </button>
        <button @click="cancelFirstPendingTrade" :disabled="store.loading">
          Cancel First Pending
        </button>
      </div>

      <div class="pagination">
        <button
          @click="store.setPage(store.currentPage - 1)"
          :disabled="store.currentPage === 1 || store.loading"
        >
          Previous
        </button>
        <span>Page {{ store.currentPage }} of {{ store.totalPages }}</span>
        <button
          @click="store.setPage(store.currentPage + 1)"
          :disabled="store.currentPage === store.totalPages || store.loading"
        >
          Next
        </button>
      </div>

      <div class="data-grid">
        <div v-for="trade in store.trades" :key="trade.id" class="data-item">
          <strong>{{ trade.symbol }}</strong> - {{ trade.side.toUpperCase() }}
          <br>
          <small>
            Qty: {{ trade.quantity }} @ ${{ trade.price }}
            <span :class="`status-${trade.status}`">[{{ trade.status }}]</span>
          </small>
          <br>
          <small>{{ new Date(trade.timestamp).toLocaleString() }}</small>
        </div>
      </div>
    </section>

    <!-- Positions Section -->
    <section class="section">
      <h2>Positions ({{ store.positions.length }})</h2>
      <div class="actions">
        <button @click="store.fetchPositions()" :disabled="store.loading">
          Refresh Positions
        </button>
        <button @click="closeFirstPosition" :disabled="store.loading || !store.hasPositions">
          Close First Position
        </button>
      </div>

      <div class="summary">
        <strong>Total Unrealized P&L:
          <span :class="store.totalUnrealizedPnL >= 0 ? 'profit' : 'loss'">
            ${{ store.totalUnrealizedPnL.toFixed(2) }}
          </span>
        </strong>
      </div>

      <div class="data-grid">
        <div v-for="position in store.positions" :key="position.id" class="data-item">
          <strong>{{ position.symbol }}</strong>
          <br>
          <small>
            Qty: {{ position.quantity }} @ ${{ position.averagePrice.toFixed(2) }}
            (Current: ${{ position.currentPrice.toFixed(2) }})
          </small>
          <br>
          <small>
            Unrealized:
            <span :class="position.unrealizedPnL >= 0 ? 'profit' : 'loss'">
              ${{ position.unrealizedPnL.toFixed(2) }}
            </span>
            | Realized: ${{ position.realizedPnL.toFixed(2) }}
          </small>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useTradingStore } from '@/stores/tradingStore'

const store = useTradingStore()

onMounted(() => {
  store.fetchTrades()
  store.fetchPositions()
})

const createSampleTrade = async () => {
  try {
    await store.createTrade({
      symbol: 'AAPL',
      side: 'buy',
      price: 175.50,
      quantity: 10
    })
  } catch (error) {
    console.error('Failed to create trade:', error)
  }
}

const cancelFirstPendingTrade = async () => {
  const pendingTrade = store.trades.find(t => t.status === 'pending')
  if (pendingTrade) {
    try {
      await store.cancelTrade(pendingTrade.id)
    } catch (error) {
      console.error('Failed to cancel trade:', error)
    }
  }
}

const closeFirstPosition = async () => {
  if (store.positions.length > 0) {
    try {
      await store.closePosition(store.positions[0].symbol)
    } catch (error) {
      console.error('Failed to close position:', error)
    }
  }
}
</script>

<style scoped>
.api-test {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  color: #2c3e50;
  margin-bottom: 30px;
}

h2 {
  color: #42b983;
  margin-bottom: 15px;
}

.error {
  background: #fee;
  border: 1px solid #fcc;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  color: #c33;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading {
  background: #e3f2fd;
  border: 1px solid #90caf9;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  color: #1976d2;
  text-align: center;
}

.section {
  margin-bottom: 40px;
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.pagination {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 15px;
}

.summary {
  margin-bottom: 15px;
  padding: 10px;
  background: white;
  border-radius: 4px;
}

button {
  background: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:hover:not(:disabled) {
  background: #369970;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.data-item {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.status-pending {
  color: #ff9800;
  font-weight: bold;
}

.status-executed {
  color: #4caf50;
  font-weight: bold;
}

.status-cancelled {
  color: #f44336;
  font-weight: bold;
}

.profit {
  color: #4caf50;
  font-weight: bold;
}

.loss {
  color: #f44336;
  font-weight: bold;
}
</style>
