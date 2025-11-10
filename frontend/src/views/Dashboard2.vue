<script setup lang="ts">
import { ref, onMounted, shallowRef, type Ref } from 'vue'
import LightweightChart from '@/components/LightweightChart.vue'
import type { ChartSeries, ChartPane, ChartMarker } from '@/components/LightweightChart.vue'
import MarkerModal from '@/components/MarkerModal.vue'
import Button from 'primevue/button'
import Menu from 'primevue/menu'

// Random data generators (same as legacyLWView)
const generateRandomData = (count: number, startValue: number = 100) => {
  const data = []
  let value = startValue
  const startTime = Math.floor(new Date('2024-01-01').getTime() / 1000)

  for (let i = 0; i < count; i++) {
    value += (Math.random() - 0.5) * 10
    data.push({
      time: startTime + i * 24 * 60 * 60,
      value: Math.max(0, Number(value.toFixed(2)))
    })
  }
  return data
}

const generateCandlestickData = (count: number) => {
  const data = []
  let price = 100
  const startTime = Math.floor(new Date('2024-01-01').getTime() / 1000)

  for (let i = 0; i < count; i++) {
    const change = (Math.random() - 0.5) * 8
    const open = price
    const close = Math.max(1, price + change)
    const high = Math.max(open, close) + Math.random() * 5
    const low = Math.min(open, close) - Math.random() * 5

    data.push({
      time: startTime + i * 24 * 60 * 60,
      open: Number(Math.max(1, open).toFixed(2)),
      high: Number(Math.max(1, high).toFixed(2)),
      low: Number(Math.max(1, low).toFixed(2)),
      close: Number(Math.max(1, close).toFixed(2))
    })

    price = close
  }
  return data
}

const generateVolumeData = (count: number) => {
  const data = []
  const startTime = Math.floor(new Date('2024-01-01').getTime() / 1000)

  for (let i = 0; i < count; i++) {
    data.push({
      time: startTime + i * 24 * 60 * 60,
      value: Number((Math.random() * 1000000 + 100000).toFixed(0)),
    })
  }
  return data
}

// Generic function to add a new series
const addNewSeries = (
  seriesRef: Ref<ChartSeries[]>,
  type: ChartSeries['type'],
) => {
  const newId = `${type.toLowerCase()}-series-${Date.now()}`
  const colors = ['#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#84cc16']
  const color = colors[seriesRef.value.length % colors.length]

  let newData: unknown[] = []
  let newOptions: ChartSeries['options'] = {}

  switch (type) {
    case 'Line':
      newData = generateRandomData(90, 100)
      newOptions = { color, lineWidth: 2 }
      break
    case 'Area':
      newData = generateRandomData(90, 50)
      newOptions = {
        topColor: 'rgba(59, 130, 246, 0.4)',
        bottomColor: 'rgba(59, 130, 246, 0.0)',
        lineColor: '#3b82f6',
        lineWidth: 2
      }
      break
    case 'Candlestick':
      newData = generateCandlestickData(60)
      newOptions = {
        upColor: '#4ade80',
        downColor: '#f87171',
        borderUpColor: '#22c55e',
        borderDownColor: '#ef4444',
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444'
      }
      break
    case 'Histogram':
      newData = generateVolumeData(60)
      newOptions = { color, priceFormat: { type: 'volume' } }
      break
    default:
      console.error(`Unsupported series type: ${type}`)
      return
  }

  if (!newData || !Array.isArray(newData)) {
    console.error('Invalid data generated for new series:', newData)
    return
  }

  const newSeries: ChartSeries = {
    type: type,
    data: newData,
    options: newOptions,
    id: newId,
    name: `Series ${seriesRef.value.length + 1}`
  }

  seriesRef.value.push(newSeries)
}

// Generic function to remove a series
const removeSeries = (seriesRef: Ref<ChartSeries[]>, seriesId: string) => {
  const index = seriesRef.value.findIndex((s) => s.id === seriesId)
  if (index > -1) {
    seriesRef.value.splice(index, 1)
  }
}

// Chart 1: Revenue Chart
const revenueChart = shallowRef<InstanceType<typeof LightweightChart>>()
const revenueChartSeries = ref<ChartSeries[]>([])
const addRevenueSeries = (type: ChartSeries['type']) => addNewSeries(revenueChartSeries, type)
const removeRevenueSeries = (id: string) => removeSeries(revenueChartSeries, id)

// Chart 2: Stock Chart
const stockChart = shallowRef<InstanceType<typeof LightweightChart>>()
const stockChartSeries = ref<ChartSeries[]>([])
const addStockSeries = (type: ChartSeries['type']) => addNewSeries(stockChartSeries, type)
const removeStockSeries = (id: string) => removeSeries(stockChartSeries, id)

// Chart 3: Volume Chart
const volumeChart = shallowRef<InstanceType<typeof LightweightChart>>()
const volumeChartSeries = ref<ChartSeries[]>([])
const addVolumeSeries = (type: ChartSeries['type']) => addNewSeries(volumeChartSeries, type)
const removeVolumeSeries = (id: string) => removeSeries(volumeChartSeries, id)

// Marker modal state
const markerModal = ref({
  visible: false,
  seriesId: '',
  seriesName: '',
  seriesData: [] as unknown[],
  chartRef: null as any
})

const showMarkerModal = (seriesId: string, seriesName: string, seriesData: unknown[], chartRef: any) => {
  markerModal.value = {
    visible: true,
    seriesId,
    seriesName,
    seriesData,
    chartRef
  }
}

const closeMarkerModal = () => {
  markerModal.value.visible = false
}

const handleAddMarkers = (markers: ChartMarker[]) => {
  if (markerModal.value.chartRef && markerModal.value.seriesId) {
    markerModal.value.chartRef.addMarkers(markerModal.value.seriesId, markers)
  }
}

// Initialize all chart data
const initializeAllSeriesData = () => {
  revenueChartSeries.value = [{
    type: 'Line',
    data: generateRandomData(90, 1000),
    options: { color: '#3b82f6', lineWidth: 3 },
    id: 'revenue-main',
    name: 'Main Revenue'
  }]

  stockChartSeries.value = [{
    type: 'Candlestick',
    data: generateCandlestickData(60),
    options: {
      upColor: '#4ade80',
      downColor: '#f87171',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444'
    },
    id: 'stock-price',
    name: 'Stock Price'
  }]

  volumeChartSeries.value = [{
    type: 'Histogram',
    data: generateVolumeData(60),
    options: { color: '#8b5cf6', priceFormat: { type: 'volume' } },
    id: 'trading-volume',
    name: 'Trading Volume'
  }]
}

const fitAllCharts = () => {
  [revenueChart, stockChart, volumeChart].forEach(chart => {
    if (chart.value) {
      chart.value.fitContent()
    }
  })
}

const menuItems = ref([
  { label: 'Line', value: 'Line', icon: 'pi pi-chart-line' },
  { label: 'Area', value: 'Area', icon: 'pi pi-chart-area' },
  { label: 'Candlestick', value: 'Candlestick', icon: 'pi pi-align-justify' },
  { label: 'Histogram', value: 'Histogram', icon: 'pi pi-chart-bar' },
])

const revenueMenu = ref()
const stockMenu = ref()
const volumeMenu = ref()

const handlePaneCreated = (pane: ChartPane) => {
  console.log('Pane created:', pane)
}

const handlePaneRemoved = (paneIndex: number) => {
  console.log('Pane removed:', paneIndex)

  // Remove all series that were in the removed pane from our data arrays
  const removeSeriesFromPane = (seriesArray: Ref<ChartSeries[]>) => {
    const originalLength = seriesArray.value.length
    seriesArray.value = seriesArray.value.filter(series => series.paneIndex !== paneIndex)
    const removedCount = originalLength - seriesArray.value.length
    if (removedCount > 0) {
      console.log(`Removed ${removedCount} series from pane ${paneIndex}`)
    }
  }

  // Remove series from all chart arrays
  removeSeriesFromPane(revenueChartSeries)
  removeSeriesFromPane(stockChartSeries)
  removeSeriesFromPane(volumeChartSeries)
}

const handleSeriesMoved = (seriesId: string, paneIndex: number) => {
  console.log('Series moved:', seriesId, 'to pane:', paneIndex)

  // Update the series paneIndex in the data
  const updateSeriesPane = (seriesArray: Ref<ChartSeries[]>) => {
    const series = seriesArray.value.find(s => s.id === seriesId)
    if (series) {
      series.paneIndex = paneIndex
    }
  }

  // Update across all chart series arrays
  updateSeriesPane(revenueChartSeries)
  updateSeriesPane(stockChartSeries)
  updateSeriesPane(volumeChartSeries)
}

onMounted(() => {
  initializeAllSeriesData()
})
</script>

<template>
  <div class="grid grid-cols-12 gap-6">
    <!-- Page Header -->
    <div class="col-span-12">
      <div class="card">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold">Dashboard 2</h2>
            <p class="text-surface-600 dark:text-surface-400 mt-2">Advanced charting with Lightweight Charts</p>
          </div>
          <Button
            label="Fit All Charts"
            icon="pi pi-refresh"
            @click="fitAllCharts"
            severity="secondary"
          />
        </div>
      </div>
    </div>

    <!-- Revenue Trend Chart -->
    <div class="col-span-12 xl:col-span-6">
      <div class="card">
        <div class="flex justify-between items-center font-semibold text-xl mb-4">
          <span>Revenue Trend</span>
          <Button
            icon="pi pi-plus"
            @click="revenueMenu.toggle($event)"
            aria-haspopup="true"
            aria-controls="revenue_menu"
            severity="success"
            size="small"
          />
          <Menu
            ref="revenueMenu"
            id="revenue_menu"
            :model="menuItems.map(item => ({ ...item, command: () => addRevenueSeries(item.value as ChartSeries['type']) }))"
            :popup="true"
          />
        </div>
        <LightweightChart
          ref="revenueChart"
          :height="400"
          :series="revenueChartSeries"
          :show-series-manager="true"
          :show-legend="true"
          :show-legend-controls="true"
          :show-pane-controls="true"
          @series-removed="removeRevenueSeries"
          @pane-created="handlePaneCreated"
          @pane-removed="handlePaneRemoved"
          @series-moved="handleSeriesMoved"
          @show-marker-modal="(seriesId, seriesName, seriesData) => showMarkerModal(seriesId, seriesName, seriesData, revenueChart)"
        />
      </div>
    </div>

    <!-- Stock Price Chart -->
    <div class="col-span-12 xl:col-span-6">
      <div class="card">
        <div class="flex justify-between items-center font-semibold text-xl mb-4">
          <span>Stock Price Analysis</span>
          <Button
            icon="pi pi-plus"
            @click="stockMenu.toggle($event)"
            aria-haspopup="true"
            aria-controls="stock_menu"
            severity="success"
            size="small"
          />
          <Menu
            ref="stockMenu"
            id="stock_menu"
            :model="menuItems.map(item => ({ ...item, command: () => addStockSeries(item.value as ChartSeries['type']) }))"
            :popup="true"
          />
        </div>
        <LightweightChart
          ref="stockChart"
          :height="400"
          :series="stockChartSeries"
          :show-series-manager="true"
          :show-legend="true"
          :show-legend-controls="true"
          :show-pane-controls="true"
          @series-removed="removeStockSeries"
          @pane-created="handlePaneCreated"
          @pane-removed="handlePaneRemoved"
          @series-moved="handleSeriesMoved"
          @show-marker-modal="(seriesId, seriesName, seriesData) => showMarkerModal(seriesId, seriesName, seriesData, stockChart)"
        />
      </div>
    </div>

    <!-- Volume Chart -->
    <div class="col-span-12">
      <div class="card">
        <div class="flex justify-between items-center font-semibold text-xl mb-4">
          <span>Trading Volume</span>
          <Button
            icon="pi pi-plus"
            @click="volumeMenu.toggle($event)"
            aria-haspopup="true"
            aria-controls="volume_menu"
            severity="success"
            size="small"
          />
          <Menu
            ref="volumeMenu"
            id="volume_menu"
            :model="menuItems.map(item => ({ ...item, command: () => addVolumeSeries(item.value as ChartSeries['type']) }))"
            :popup="true"
          />
        </div>
        <LightweightChart
          ref="volumeChart"
          :height="300"
          :series="volumeChartSeries"
          :show-series-manager="true"
          :show-legend="true"
          :show-legend-controls="true"
          :show-pane-controls="true"
          @series-removed="removeVolumeSeries"
          @pane-created="handlePaneCreated"
          @pane-removed="handlePaneRemoved"
          @series-moved="handleSeriesMoved"
          @show-marker-modal="(seriesId, seriesName, seriesData) => showMarkerModal(seriesId, seriesName, seriesData, volumeChart)"
        />
      </div>
    </div>

    <!-- Marker Modal -->
    <MarkerModal
      :visible="markerModal.visible"
      :series-name="markerModal.seriesName"
      :series-data="markerModal.seriesData"
      @close="closeMarkerModal"
      @add-markers="handleAddMarkers"
    />
  </div>
</template>
