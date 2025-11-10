# LightweightChart Component Documentation

The `LightweightChart` component is a Vue 3 wrapper around the [TradingView Lightweight Charts](https://github.com/tradingview/lightweight-charts) library, providing financial charting capabilities with series management, pane organization, and marker support.

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `width` | Number | 400 | Chart container width in pixels |
| `height` | Number | 300 | Chart container height in pixels |
| `chartOptions` | Object | {} | Additional options to pass to the chart |
| `series` | Array | [] | Array of chart series to display |
| `title` | String | '' | Chart title text |
| `showSeriesManager` | Boolean | false | Show/hide the series manager panel |
| `showLegend` | Boolean | false | Show/hide the interactive legend |
| `showLegendControls` | Boolean | false | Show/hide legend control buttons |
| `panes` | Array | [] | Initial pane configuration |
| `showPaneControls` | Boolean | false | Show/hide pane management controls |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `series-removed` | `seriesId: string` | Emitted when a series is removed |
| `pane-created` | `pane: ChartPane` | Emitted when a new pane is created |
| `pane-removed` | `paneIndex: number` | Emitted when a pane is removed |
| `series-moved` | `seriesId: string, paneIndex: number` | Emitted when a series is moved between panes |
| `marker-added` | `seriesId: string, markers: ChartMarker[]` | Emitted when markers are added to a series |
| `markers-cleared` | `seriesId: string` | Emitted when markers are cleared from a series |
| `show-marker-modal` | `seriesId: string, seriesName: string, seriesData: unknown[]` | Emitted when marker modal should be shown |

## Data Structures

### ChartSeries

```typescript
interface ChartSeries {
  type: 'Line' | 'Area' | 'Bar' | 'Candlestick' | 'Histogram' | 'Baseline'
  data: unknown[]
  options?: SeriesOptions
  id: string
  name: string
  paneIndex?: number
  markers?: ChartMarker[]
}
```

### ChartPane

```typescript
interface ChartPane {
  index: number
  name: string
  height?: number
}
```

### ChartMarker

```typescript
interface ChartMarker {
  time: number
  position: 'aboveBar' | 'belowBar' | 'inBar'
  color: string
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown'
  text?: string
  details?: string
}
```

## Methods

The component exposes the following methods via `defineExpose`:

| Method | Parameters | Description |
|--------|------------|-------------|
| `chart()` | - | Returns the underlying chart instance |
| `fitContent()` | - | Fits chart content to available space |
| `updateSeries(seriesId, data)` | `seriesId: string, data: unknown[]` | Updates series data |
| `createPane(name, height)` | `name: string, height?: number` | Creates a new pane |
| `removePane(paneIndex)` | `paneIndex: number` | Removes a pane |
| `moveSeriesTo(seriesId, paneIndex)` | `seriesId: string, paneIndex: number` | Moves a series to a different pane |
| `availablePanes()` | - | Returns available panes |
| `addMarkers(seriesId, markers)` | `seriesId: string, markers: ChartMarker[]` | Adds markers to a series |
| `clearMarkers(seriesId)` | `seriesId: string` | Clears markers from a series |
| `getSeriesMarkers(seriesId)` | `seriesId: string` | Gets markers for a series |

## Basic Usage

```vue
<template>
  <LightweightChart
    :width="600"
    :height="400"
    :series="chartSeries"
    :show-legend="true"
    :show-series-manager="true"
  />
</template>

<script setup>
import LightweightChart from '@/components/LightweightChart.vue'
import { ref } from 'vue'

const chartSeries = ref([
  {
    type: 'Line',
    data: [
      { time: '2024-01-01', value: 100 },
      { time: '2024-01-02', value: 105 },
      { time: '2024-01-03', value: 102 }
    ],
    options: { color: '#2563eb' },
    id: 'series-1',
    name: 'Price'
  }
])
</script>
```

## Advanced Usage with Panes

```vue
<template>
  <LightweightChart
    ref="chartRef"
    :width="800"
    :height="500"
    :series="multiPaneSeries"
    :show-legend="true"
    :show-legend-controls="true"
    :show-pane-controls="true"
    @pane-created="handlePaneCreated"
    @series-moved="handleSeriesMoved"
  />
</template>

<script setup>
import LightweightChart from '@/components/LightweightChart.vue'
import { ref } from 'vue'

const chartRef = ref()

const multiPaneSeries = ref([
  {
    type: 'Candlestick',
    data: candlestickData,
    options: { upColor: '#26a69a', downColor: '#ef5350' },
    id: 'price-series',
    name: 'Stock Price'
  },
  {
    type: 'Histogram',
    data: volumeData,
    options: { color: '#2196f3' },
    id: 'volume-series',
    name: 'Volume',
    paneIndex: 1
  }
])

const handlePaneCreated = (pane) => {
  console.log('New pane created:', pane)
}

const handleSeriesMoved = (seriesId, paneIndex) => {
  console.log(`Series ${seriesId} moved to pane ${paneIndex}`)
}
</script>
```

## Series Types

The component supports all Lightweight Charts series types:

1. **Line** - Simple line chart
2. **Area** - Area chart with gradient fill
3. **Bar** - Bar chart
4. **Candlestick** - Candlestick chart for OHLC data
5. **Histogram** - Histogram for volume and other data
6. **Baseline** - Baseline chart showing deviation from a base value

Each series type accepts specific options according to the Lightweight Charts documentation.