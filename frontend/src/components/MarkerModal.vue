<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Add Markers to {{ seriesName }}</h3>
        <button @click="close" class="close-btn">
          <i class="pi pi-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label>Position</label>
          <select v-model="markerConfig.position" class="form-select">
            <option value="aboveBar">Above Bar</option>
            <option value="belowBar">Below Bar</option>
            <option value="inBar">In Bar</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Color</label>
          <div class="color-options">
            <div
              v-for="color in colorOptions"
              :key="color"
              class="color-option"
              :class="{ selected: markerConfig.color === color }"
              :style="{ backgroundColor: color }"
              @click="markerConfig.color = color"
            ></div>
          </div>
        </div>
        
        <div class="form-group">
          <label>Shape</label>
          <div class="shape-options">
            <div
              v-for="shape in shapeOptions"
              :key="shape.value"
              class="shape-option"
              :class="{ selected: markerConfig.shape === shape.value }"
              @click="markerConfig.shape = shape.value as any"
            >
              <i :class="shape.icon"></i>
              <span>{{ shape.label }}</span>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>Text</label>
          <input 
            v-model="markerConfig.text" 
            type="text" 
            class="form-input"
            placeholder="Enter marker text"
          />
        </div>
        
        <div class="form-group">
          <label>Details (optional)</label>
          <textarea 
            v-model="markerConfig.details" 
            class="form-textarea"
            placeholder="Enter additional details to show on click"
            rows="3"
          ></textarea>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button @click="addMarkers" class="btn btn-primary">Add 5 Markers</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { ChartMarker } from './LightweightChart.vue'

interface Props {
  visible: boolean
  seriesName: string
  seriesData: unknown[]
}

interface Emits {
  (e: 'close'): void
  (e: 'add-markers', markers: ChartMarker[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const markerConfig = reactive({
  position: 'aboveBar' as const,
  color: '#ef4444',
  shape: 'circle' as const,
  text: '',
  details: ''
})

const colorOptions = [
  '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#000000'
]

const shapeOptions = [
  { value: 'circle', label: 'Circle', icon: 'pi pi-circle' },
  { value: 'square', label: 'Square', icon: 'pi pi-stop' },
  { value: 'arrowUp', label: 'Arrow Up', icon: 'pi pi-arrow-up' },
  { value: 'arrowDown', label: 'Arrow Down', icon: 'pi pi-arrow-down' }
]

const close = () => {
  emit('close')
}

const handleOverlayClick = () => {
  close()
}

const addMarkers = () => {
  if (!markerConfig.text.trim()) {
    alert('Please enter marker text')
    return
  }
  
  const markers: ChartMarker[] = []
  const dataLength = props.seriesData.length
  
  // Generate 5 random markers on existing timestamps
  for (let i = 0; i < 5; i++) {
    const randomIndex = Math.floor(Math.random() * dataLength)
    const dataPoint = props.seriesData[randomIndex] as any
    
    if (dataPoint && dataPoint.time) {
      const marker: ChartMarker = {
        time: dataPoint.time,
        position: markerConfig.position,
        color: markerConfig.color,
        shape: markerConfig.shape,
        text: markerConfig.text,
        ...(markerConfig.details.trim() && { details: markerConfig.details })
      }
      markers.push(marker)
    }
  }
  
  emit('add-markers', markers)
  close()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
}

.close-btn {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-select,
.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.color-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.selected {
  border-color: #1e293b;
  box-shadow: 0 0 0 2px rgba(30, 41, 59, 0.2);
}

.shape-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.shape-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.shape-option:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.shape-option.selected {
  border-color: #3b82f6;
  background: #dbeafe;
  color: #1e40af;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}
</style>