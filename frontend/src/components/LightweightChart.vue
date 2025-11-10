<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, shallowRef, computed } from 'vue'
import { useLayoutStore } from '@/stores/layoutStore'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineSeriesPartialOptions,
  type AreaSeriesPartialOptions,
  type BarSeriesPartialOptions,
  type CandlestickSeriesPartialOptions,
  type HistogramSeriesPartialOptions,
  type BaselineSeriesPartialOptions,
  type SeriesMarker,
  createSeriesMarkers,
  LineSeries,
  AreaSeries,
  BarSeries,
  CandlestickSeries,
  HistogramSeries,
  BaselineSeries,
} from 'lightweight-charts'

const layoutStore = useLayoutStore()

export interface ChartMarker {
  time: number
  position: 'aboveBar' | 'belowBar' | 'inBar'
  color: string
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown'
  text?: string
  details?: string
}

export interface ChartSeries {
  type: 'Line' | 'Area' | 'Bar' | 'Candlestick' | 'Histogram' | 'Baseline'
  data: unknown[]
  options?: LineSeriesPartialOptions | AreaSeriesPartialOptions | BarSeriesPartialOptions | CandlestickSeriesPartialOptions | HistogramSeriesPartialOptions | BaselineSeriesPartialOptions
  id: string
  name: string
  paneIndex?: number
  markers?: ChartMarker[]
}

export interface ChartPane {
  index: number
  name: string
  height?: number
}

interface Props {
  width?: number
  height?: number
  chartOptions?: Record<string, unknown>
  series?: ChartSeries[]
  title?: string
  showSeriesManager?: boolean
  showLegend?: boolean
  showLegendControls?: boolean
  panes?: ChartPane[]
  showPaneControls?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: undefined,
  height: 300,
  chartOptions: () => ({}),
  series: () => [],
  title: '',
  showSeriesManager: false,
  showLegend: false,
  showLegendControls: false,
  panes: () => [],
  showPaneControls: false
})

const chartContainer = ref<HTMLElement>()
const chart = shallowRef<IChartApi | null>(null)
const seriesMap = new Map<string, any>()
const seriesVisibility = ref<{ [key: string]: boolean }>({})
const resizeObserver = ref<ResizeObserver | null>(null)

interface PaneLegend {
  data: { [key: string]: any };
  top: number;
  name: string;
  index: number;
}
const paneLegends = ref<{ [key: number]: PaneLegend }>({})

const availablePanes = ref<ChartPane[]>([{ index: 0, name: 'Main Chart' }])
const nextPaneIndex = ref(1)
const seriesMarkers = ref<{ [key: string]: ChartMarker[] }>({})
const seriesMarkerInstances = new Map<string, any>()
const markerOverlay = ref<{ visible: boolean; marker: ChartMarker | null; x: number; y: number }>({
  visible: false,
  marker: null,
  x: 0,
  y: 0
})

const emit = defineEmits<{
  (e: 'series-removed', id: string): void
  (e: 'pane-created', pane: ChartPane): void
  (e: 'pane-removed', paneIndex: number): void
  (e: 'series-moved', seriesId: string, paneIndex: number): void
  (e: 'marker-added', seriesId: string, markers: ChartMarker[]): void
  (e: 'markers-cleared', seriesId: string): void
  (e: 'show-marker-modal', seriesId: string, seriesName: string, seriesData: unknown[]): void
}>()

const defaultChartOptions = computed(() => {
  const dark = layoutStore.isDarkTheme
  return {
    layout: {
      background: { color: dark ? '#1e293b' : '#ffffff' },
      textColor: dark ? '#e2e8f0' : '#333',
    },
    grid: {
      vertLines: { color: dark ? '#334155' : '#f0f0f0' },
      horzLines: { color: dark ? '#334155' : '#f0f0f0' },
    },
    crosshair: {
      mode: 0,
    },
    rightPriceScale: {
      borderColor: dark ? '#475569' : '#cccccc',
    },
    timeScale: {
      borderColor: dark ? '#475569' : '#cccccc',
      timeVisible: true,
      secondsVisible: false,
    },
    handleScroll: true,
    handleScale: true,
  }
})

const addSeries = (seriesConfig: ChartSeries) => {
  if (!chart.value) return
  
  const seriesTypeMap = {
    'Line': LineSeries,
    'Area': AreaSeries,
    'Bar': BarSeries,
    'Candlestick': CandlestickSeries,
    'Histogram': HistogramSeries,
    'Baseline': BaselineSeries,
  }

  const paneIndex = seriesConfig.paneIndex ?? 0
  const seriesApi = chart.value.addSeries(
    seriesTypeMap[seriesConfig.type], 
    seriesConfig.options,
    paneIndex
  );
  
  if (seriesApi) {
    seriesApi.setData(seriesConfig.data as any)
    seriesMap.set(seriesConfig.id, seriesApi)
    seriesVisibility.value[seriesConfig.id] = true
    
    if (seriesConfig.markers && seriesConfig.markers.length > 0) {
      const convertedMarkers = seriesConfig.markers.map(marker => ({
        time: marker.time as any,
        position: marker.position,
        color: marker.color,
        shape: marker.shape,
        text: marker.text
      }))
      const markerInstance = createSeriesMarkers(seriesApi, convertedMarkers)
      seriesMarkerInstances.set(seriesConfig.id, markerInstance)
      seriesMarkers.value[seriesConfig.id] = seriesConfig.markers
    }
  }
}

const updatePaneLegendPositions = () => {
  if (!chart.value) return;

  const panes = chart.value.panes();
  let cumulativeTop = 0;
  const newPaneLegends: { [key: number]: PaneLegend } = {};

  panes.forEach((pane) => {
    const paneIndex = pane.paneIndex();
    const paneInfo = availablePanes.value.find(p => p.index === paneIndex) || { name: `Pane ${paneIndex}`, index: paneIndex };
    
    const existingData = paneLegends.value[paneIndex]?.data || {};

    newPaneLegends[paneIndex] = {
      data: existingData,
      top: cumulativeTop + 12,
      name: paneInfo.name,
      index: paneIndex,
    };
    
    cumulativeTop += pane.getHeight();
  });

  paneLegends.value = newPaneLegends;
};

const initChart = () => {
  if (!chartContainer.value) return

  // Use container width if width prop is undefined
  const chartWidth = props.width ?? chartContainer.value.clientWidth
  const mergedOptions = { ...defaultChartOptions.value, ...props.chartOptions, width: chartWidth, height: props.height }
  chart.value = createChart(chartContainer.value, mergedOptions)
  
  initializePanes()
  
  props.series.forEach(addSeries)
  chart.value.timeScale().fitContent();
  
  if (props.showLegend) {
    nextTick(() => {
      updatePaneLegendPositions();
      setupLegend();
    })
  }
  
  setupMarkerEvents()
  
  // Set up resize observer for responsive charts
  if (!props.width) {
    resizeObserver.value = new ResizeObserver(() => {
      if (chart.value && chartContainer.value) {
        chart.value.resize(chartContainer.value.clientWidth, props.height)
      }
    })
    resizeObserver.value.observe(chartContainer.value)
  }
}

watch(() => props.series, (newSeries) => {
  if (!chart.value) return;

  seriesMap.forEach(seriesApi => {
    chart.value?.removeSeries(seriesApi);
  });
  seriesMap.clear();
  
  seriesMarkerInstances.clear();
  seriesMarkers.value = {};

  newSeries.forEach(addSeries);
  
  chart.value.timeScale().fitContent();
  
  if (props.showLegend) {
    nextTick(() => {
      updatePaneLegendPositions();
      setupLegend();
    })
  }
  
  setupMarkerEvents()
}, { deep: true });

watch(() => [props.width, props.height], ([newWidth, newHeight]) => {
  if (chart.value && chartContainer.value) {
    // Use container width if width prop is undefined
    const chartWidth = newWidth ?? chartContainer.value.clientWidth
    chart.value.resize(chartWidth, newHeight)
  }
})

// Watch for dark mode changes and update chart appearance
watch(() => layoutStore.isDarkTheme, () => {
  if (chart.value) {
    chart.value.applyOptions(defaultChartOptions.value)
  }
})

onMounted(() => {
  nextTick(initChart)
})

onUnmounted(() => {
  if (chart.value) {
    chart.value.remove()
    chart.value = null
  }
  seriesMap.clear()
  seriesMarkerInstances.clear()

  // Clean up resize observer
  if (resizeObserver.value && chartContainer.value) {
    resizeObserver.value.unobserve(chartContainer.value)
    resizeObserver.value = null
  }
})

const getSeriesColor = (seriesItem: ChartSeries): string => {
  if (seriesItem.options) {
    const options = seriesItem.options as any
    if (options.color) return options.color
    if (options.lineColor) return options.lineColor
    if (options.upColor) return options.upColor
    if (options.topLineColor) return options.topLineColor
  }
  const defaultColors = { Line: '#2563eb', Area: '#10b981', Bar: '#f59e0b', Candlestick: '#ef4444', Histogram: '#8b5cf6', Baseline: '#06b6d4' }
  return defaultColors[seriesItem.type] || '#6b7280'
}

const handleRemoveSeries = (seriesId: string) => {
  emit('series-removed', seriesId)
}

const handleShowMarkerModal = (seriesId: string) => {
  const series = props.series.find(s => s.id === seriesId)
  if (series) {
    emit('show-marker-modal', seriesId, series.name, series.data)
  }
}

const toggleSeriesVisibility = (seriesId: string) => {
  const isVisible = !seriesVisibility.value[seriesId]
  seriesVisibility.value[seriesId] = isVisible
  const seriesApi = seriesMap.get(seriesId)
  if (seriesApi) {
    seriesApi.applyOptions({ visible: isVisible })
  }
}

const setupLegend = () => {
  if (!chart.value) return;

  chart.value.subscribeCrosshairMove((param) => {
    for (const paneIdx in paneLegends.value) {
      paneLegends.value[paneIdx].data = {};
    }

    if (!param.time || !param.seriesData) {
      return;
    }

    const seriesByPane: { [key: number]: ChartSeries[] } = {};
    props.series.forEach(s => {
      const paneIndex = s.paneIndex ?? 0;
      if (!seriesByPane[paneIndex]) {
        seriesByPane[paneIndex] = [];
      }
      seriesByPane[paneIndex].push(s);
    });

    for (const paneIndexStr in seriesByPane) {
      const paneIndex = Number(paneIndexStr);
      const paneSeries = seriesByPane[paneIndex];
      const newPaneLegendData: { [key: string]: any } = {};

      paneSeries.forEach((seriesConfig) => {
        const seriesApi = seriesMap.get(seriesConfig.id);
        if (seriesApi && seriesVisibility.value[seriesConfig.id]) {
          const seriesValue = param.seriesData.get(seriesApi as any);
          if (seriesValue !== undefined) {
            newPaneLegendData[seriesConfig.id] = {
              name: seriesConfig.name,
              type: seriesConfig.type,
              value: seriesValue,
              color: getSeriesColor(seriesConfig),
            };
          }
        }
      });
      
      if (paneLegends.value[paneIndex]) {
        paneLegends.value[paneIndex].data = newPaneLegendData;
      }
    }
  });
};

const formatLegendValue = (value: any, seriesType: string): string => {
  if (value === null || value === undefined) return 'N/A'
  
  if (seriesType === 'Candlestick' || seriesType === 'Bar') {
    if (typeof value === 'object' && value !== null) {
      const data = value as any
      const o = data.open !== undefined ? data.open.toFixed(2) : 'N/A'
      const h = data.high !== undefined ? data.high.toFixed(2) : 'N/A'
      const l = data.low !== undefined ? data.low.toFixed(2) : 'N/A'
      const c = data.close !== undefined ? data.close.toFixed(2) : 'N/A'
      return `O: ${o} H: ${h} L: ${l} C: ${c}`
    }
  }
  
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  
  if (typeof value === 'object' && value !== null) {
    const data = value as any
    if (data.value !== undefined) {
      return data.value.toFixed(2)
    }
  }
  
  return String(value)
}

// Pane management functions
const initializePanes = () => {
  if (!chart.value) return
  
  const initialPanes: ChartPane[] = [{ index: 0, name: 'Main Chart' }]
  
  props.panes.forEach((paneConfig, idx) => {
    initialPanes.push({ index: idx + 1, name: paneConfig.name, height: paneConfig.height })
  })
  
  availablePanes.value = initialPanes
  nextPaneIndex.value = initialPanes.length
}

const createPane = (name: string, height: number = 200) => {
  if (!chart.value) return
  
  const paneIndex = nextPaneIndex.value
  const newPane: ChartPane = { 
    index: paneIndex, 
    name: name || `Pane ${paneIndex}`, 
    height 
  }
  
  try {
    const placeholderSeries = chart.value.addSeries(LineSeries, {
      color: 'transparent',
      lineWidth: 0 as any,
      visible: false,
      priceLineVisible: false,
      lastValueVisible: false
    }, paneIndex)
    
    placeholderSeries.setData([{
      time: Math.floor(Date.now() / 1000) as any,
      value: 0
    }])
  } catch (error) {
    console.error('Error creating placeholder series for new pane:', error)
  }
  
  availablePanes.value.push(newPane)
  nextPaneIndex.value++
  
  emit('pane-created', newPane)
  return paneIndex
}

const removePane = (paneIndex: number) => {
  if (!chart.value || paneIndex === 0) return // Can't remove main pane
  
  try {
    const seriesToRemove = props.series.filter(s => s.paneIndex === paneIndex)
    seriesToRemove.forEach(series => {
      seriesMap.delete(series.id)
      delete seriesVisibility.value[series.id]
    })
    
    chart.value.removePane(paneIndex)
    
    availablePanes.value = availablePanes.value.filter(p => p.index !== paneIndex)
    emit('pane-removed', paneIndex)
  } catch (error) {
    console.error('Error removing pane:', error)
  }
}

const moveSeriesTo = (seriesId: string, targetPaneIndex: number) => {
  const seriesApi = seriesMap.get(seriesId)
  if (!seriesApi || !chart.value) return
  
  try {
    seriesApi.moveToPane(targetPaneIndex)
    emit('series-moved', seriesId, targetPaneIndex)
  } catch (error) {
    console.error('Error moving series to pane:', error)
  }
}

const getPaneNameByIndex = (paneIndex?: number) => {
  if (paneIndex === undefined || paneIndex === 0) return 'Main Chart'
  const pane = availablePanes.value.find(p => p.index === paneIndex)
  return pane?.name || `Pane ${paneIndex}`
}

// Marker management functions
const addMarkers = (seriesId: string, markers: ChartMarker[]) => {
  const seriesApi = seriesMap.get(seriesId)
  if (!seriesApi) return
  
  const existingMarkers = seriesMarkers.value[seriesId] || []
  const allMarkers = [...existingMarkers, ...markers]
  
  const convertedMarkers = allMarkers.map(marker => ({
    time: marker.time as any,
    position: marker.position,
    color: marker.color,
    shape: marker.shape,
    text: marker.text
  }))
  
  const existingMarkerInstance = seriesMarkerInstances.get(seriesId)
  if (existingMarkerInstance) {
    existingMarkerInstance.setMarkers(convertedMarkers)
  } else {
    const markerInstance = createSeriesMarkers(seriesApi, convertedMarkers)
    seriesMarkerInstances.set(seriesId, markerInstance)
  }
  
  seriesMarkers.value[seriesId] = allMarkers
  emit('marker-added', seriesId, allMarkers)
}

const clearMarkers = (seriesId: string) => {
  const markerInstance = seriesMarkerInstances.get(seriesId)
  if (markerInstance) {
    markerInstance.setMarkers([])
    seriesMarkerInstances.delete(seriesId)
  }
  
  delete seriesMarkers.value[seriesId]
  emit('markers-cleared', seriesId)
}

const getSeriesMarkers = (seriesId: string): ChartMarker[] => {
  return seriesMarkers.value[seriesId] || []
}

const setupMarkerEvents = () => {
  if (!chart.value || !chartContainer.value) return
  
  chartContainer.value.addEventListener('click', (event) => {
    const rect = chartContainer.value!.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    
    const clickedMarker = findMarkerAtPosition(x, y)
    if (clickedMarker) {
      showMarkerOverlay(clickedMarker, event.clientX, event.clientY)
    } else {
      hideMarkerOverlay()
    }
  })
  
  document.addEventListener('click', (event) => {
    if (markerOverlay.value.visible && 
        !chartContainer.value?.contains(event.target as Node) &&
        !(event.target as HTMLElement).closest('.marker-overlay')) {
      hideMarkerOverlay()
    }
  })
}

const findMarkerAtPosition = (x: number, y: number): ChartMarker | null => {
  for (const [seriesId, markers] of Object.entries(seriesMarkers.value)) {
    for (const marker of markers) {
      if (marker.details) {
        return marker
      }
    }
  }
  return null
}

const showMarkerOverlay = (marker: ChartMarker, x: number, y: number) => {
  if (!marker.details) return
  
  markerOverlay.value = {
    visible: true,
    marker,
    x,
    y
  }
}

const hideMarkerOverlay = () => {
  markerOverlay.value.visible = false
}

defineExpose({
  chart: () => chart.value,
  fitContent: () => chart.value?.timeScale().fitContent(),
  updateSeries: (seriesId: string, data: unknown[]) => {
    const series = seriesMap.get(seriesId)
    if (series) series.setData(data)
  },
  createPane,
  removePane,
  moveSeriesTo,
  availablePanes: () => availablePanes.value,
  addMarkers,
  clearMarkers,
  getSeriesMarkers
})
</script>

<template>
  <div class="chart-component">
    <div v-if="title" class="chart-title">{{ title }}</div>
    <div class="chart-content">
      <div ref="chartContainer" class="chart-container" :style="{ width: width ? width + 'px' : '100%', height: height + 'px' }"></div>
      
      <template v-if="showLegend">
        <div
          v-for="legend in Object.values(paneLegends).filter(l => Object.keys(l.data).length > 0)"
          :key="legend.index"
          class="legend"
          :style="{ top: legend.top + 'px' }"
        >
          <div class="legend-pane-title">{{ legend.name }}</div>
          <div v-for="(data, seriesId) in legend.data" :key="seriesId" class="legend-item">
            <div class="legend-info">
              <div class="legend-color" :style="{ backgroundColor: data.color }"></div>
              <span class="legend-name">{{ data.name }}</span>
              <span class="legend-value">{{ formatLegendValue(data.value, data.type) }}</span>
            </div>
            <div v-if="showLegendControls" class="legend-controls">
              <Button
                @click="toggleSeriesVisibility(String(seriesId))"
                :icon="seriesVisibility[String(seriesId)] ? 'pi pi-eye' : 'pi pi-eye-slash'"
                :title="seriesVisibility[String(seriesId)] ? 'Hide series' : 'Show series'"
                text
                rounded
                size="small"
                :class="{ 'opacity-50': !seriesVisibility[String(seriesId)] }"
              />
              <Button
                @click="handleRemoveSeries(String(seriesId))"
                icon="pi pi-times"
                title="Remove series"
                text
                rounded
                size="small"
                severity="danger"
              />
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <div v-if="showSeriesManager && series.length > 0" class="series-manager">
      <h4 class="series-title">Active Series</h4>
      <ul class="series-list">
        <li v-for="s in series" :key="s.id" class="series-item">
          <div class="series-info">
            <div class="series-color-indicator" :style="{ backgroundColor: getSeriesColor(s) }"></div>
            <span class="series-name">{{ s.name }}</span>
            <span class="series-type">{{ s.type }}</span>
            <span class="series-pane" v-if="showPaneControls">{{ getPaneNameByIndex(s.paneIndex) }}</span>
          </div>
          <div class="series-actions">
            <div v-if="showPaneControls && availablePanes.length > 1" class="pane-controls">
              <Dropdown
                :modelValue="s.paneIndex ?? 0"
                @update:modelValue="moveSeriesTo(s.id, $event)"
                :options="availablePanes"
                optionLabel="name"
                optionValue="index"
                placeholder="Move to pane"
                class="pane-dropdown"
              />
            </div>
            <Button
              @click="toggleSeriesVisibility(s.id)"
              :icon="seriesVisibility[s.id] ? 'pi pi-eye' : 'pi pi-eye-slash'"
              :title="seriesVisibility[s.id] ? 'Hide' : 'Show'"
              text
              rounded
              size="small"
            />
            <Button
              @click="handleShowMarkerModal(s.id)"
              icon="pi pi-map-marker"
              title="Add Markers"
              text
              rounded
              size="small"
              severity="info"
            />
            <Button
              v-if="getSeriesMarkers(s.id).length > 0"
              @click="clearMarkers(s.id)"
              icon="pi pi-trash"
              title="Clear Markers"
              text
              rounded
              size="small"
              severity="warning"
            />
            <Button
              @click="handleRemoveSeries(s.id)"
              icon="pi pi-times"
              title="Remove"
              text
              rounded
              size="small"
              severity="danger"
            />
          </div>
        </li>
      </ul>
    </div>
    
    <!-- Marker Overlay -->
    <div
      v-if="markerOverlay.visible && markerOverlay.marker"
      class="marker-overlay"
      :style="{ left: markerOverlay.x + 'px', top: markerOverlay.y + 'px' }"
    >
      <div class="marker-overlay-content">
        <div class="marker-overlay-header">
          <span class="marker-text">{{ markerOverlay.marker?.text || '' }}</span>
          <Button
            @click="hideMarkerOverlay"
            icon="pi pi-times"
            text
            rounded
            size="small"
          />
        </div>
        <div class="marker-overlay-details">
          {{ markerOverlay.marker?.details || '' }}
        </div>
      </div>
    </div>
    
    <div v-if="showPaneControls" class="pane-manager">
      <h4 class="pane-title">Pane Management</h4>
      <div class="pane-controls-section">
        <div class="pane-actions">
          <Button
            @click="createPane('New Pane')"
            icon="pi pi-plus"
            label="Add Pane"
            title="Add New Pane"
            size="small"
          />
        </div>
        <ul class="pane-list" v-if="availablePanes.length > 1">
          <li v-for="pane in availablePanes.filter(p => p.index !== 0)" :key="pane.index" class="pane-item">
            <span class="pane-name">{{ pane.name }}</span>
            <Button
              @click="removePane(pane.index)"
              icon="pi pi-times"
              title="Remove Pane"
              text
              rounded
              size="small"
              severity="danger"
            />
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-component {
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 1rem;
  text-align: left;
}

.chart-content {
  position: relative;
}

.chart-container {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  width: 100%;
}

.legend {
  position: absolute;
  left: 12px;
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  padding: 8px 12px;
  box-shadow: var(--card-shadow);
  backdrop-filter: blur(8px);
  z-index: 1000;
  pointer-events: auto;
  max-width: 350px;
  min-width: 200px;
  transition: top 0.2s ease-in-out;
}

.legend-pane-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--surface-border);
}

.legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 0.8rem;
  padding: 2px 0;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.legend-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-name {
  font-weight: 500;
  color: var(--text-color);
  min-width: 0;
  flex-shrink: 0;
}

.legend-value {
  font-weight: 400;
  color: var(--text-color-secondary);
  font-family: 'SF Mono', 'Monaco', 'Consolas', 'Roboto Mono', monospace;
  font-size: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.legend-controls {
  display: flex;
  gap: 4px;
  opacity: 0.3;
  transition: opacity 0.2s ease;
  pointer-events: auto;
}

.legend-item:hover .legend-controls {
  opacity: 1;
}

.series-manager {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.series-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.series-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.series-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 1rem;
  background: var(--surface-50);
  border-radius: var(--border-radius);
  border: 1px solid var(--surface-border);
  transition: all 0.2s ease-in-out;
  flex-grow: 1;
}

.series-item:hover {
  background: var(--surface-100);
  transform: translateY(-2px);
  box-shadow: var(--card-shadow);
}

.series-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.series-color-indicator {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.series-name {
  font-weight: 500;
  color: var(--text-color);
}

.series-type {
  color: var(--text-color-secondary);
  background: var(--surface-100);
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-weight: 500;
}

.series-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.series-pane {
  color: var(--text-color-secondary);
  background: var(--surface-100);
  padding: 0.1rem 0.4rem;
  border-radius: var(--border-radius);
  font-weight: 500;
}

.pane-controls {
  margin-right: 0.5rem;
}

.pane-dropdown {
  min-width: 120px;
}

.pane-manager {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.pane-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.pane-controls-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.pane-actions {
  display: flex;
  gap: 0.5rem;
}

.pane-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pane-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--surface-50);
  border-radius: var(--border-radius);
  border: 1px solid var(--surface-border);
  transition: all 0.2s;
}

.pane-item:hover {
  background: var(--surface-100);
}

.pane-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color);
}

.marker-overlay {
  position: fixed;
  z-index: 10000;
  pointer-events: auto;
  transform: translate(-50%, -100%);
  margin-top: -10px;
}

.marker-overlay-content {
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
  padding: 12px;
  min-width: 200px;
  max-width: 300px;
}

.marker-overlay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.marker-text {
  font-weight: 600;
  color: var(--text-color);
  font-size: 0.875rem;
}

.marker-overlay-details {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
  line-height: 1.4;
  white-space: pre-wrap;
}
</style>