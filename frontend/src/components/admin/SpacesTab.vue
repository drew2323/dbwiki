<template>
  <div>
    <Toolbar class="mb-4">
      <template #start>
        <Button label="New Space" icon="pi pi-plus" severity="secondary" @click="openNew" class="mr-2" />
      </template>
      <template #end>
        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="spaces"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      :loading="loading"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} spaces"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">Manage Spaces</h4>
        </div>
      </template>

      <Column field="key" header="Key" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <span class="font-mono text-sm">{{ data.key }}</span>
        </template>
      </Column>

      <Column field="name" header="Name" sortable style="min-width: 14rem">
        <template #body="{ data }">
          <div class="font-medium">{{ data.name }}</div>
        </template>
      </Column>

      <Column field="description" header="Description" style="min-width: 16rem">
        <template #body="{ data }">
          <span class="text-sm text-500">{{ data.description || '-' }}</span>
        </template>
      </Column>

      <Column field="visibility" header="Visibility" sortable style="min-width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.visibility" :severity="data.visibility === 'public' ? 'info' : 'secondary'" />
        </template>
      </Column>

      <Column field="created_at" header="Created" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-sm">{{ formatDate(data.created_at) }}</span>
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editSpace(data)" v-tooltip.top="'Edit'" />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteSpace(data)" v-tooltip.top="'Delete'" />
        </template>
      </Column>
    </DataTable>

    <!-- Space Dialog -->
    <Dialog v-model:visible="spaceDialog" :style="{ width: '600px' }" :header="isEditMode ? 'Edit Space' : 'New Space'" :modal="true" class="p-fluid">
      <div class="flex flex-col gap-6">
        <FloatLabel class="mt-6">
          <InputText id="key" v-model="currentSpace.key" required class="w-full" :invalid="!currentSpace.key" :disabled="isEditMode" />
          <label for="key">Key (URL-safe identifier) *</label>
        </FloatLabel>

        <FloatLabel>
          <InputText id="name" v-model="currentSpace.name" required class="w-full" :invalid="!currentSpace.name" />
          <label for="name">Space Name *</label>
        </FloatLabel>

        <FloatLabel>
          <Textarea id="description" v-model="currentSpace.description" rows="3" class="w-full" />
          <label for="description">Description</label>
        </FloatLabel>

        <div class="flex flex-col gap-2">
          <label for="visibility">Visibility</label>
          <SelectButton id="visibility" v-model="currentSpace.visibility" :options="visibilityOptions" optionLabel="label" optionValue="value" />
          <small class="text-500">Public spaces may be viewable without login when accessed via mapped domain</small>
        </div>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveSpace" :loading="loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex align-items-center gap-4">
        <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
        <span v-if="currentSpace">
          Are you sure you want to delete the space <b>{{ currentSpace.name }}</b>?
          <br />
          <span class="text-sm text-500">This action cannot be undone.</span>
        </span>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="deleteDialog = false" />
        <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteSpace" :loading="loading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { spaceService } from '@/services/spaceService'
import type { Space } from '@/types/admin'
import { useToast } from 'primevue/usetoast'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Tag from 'primevue/tag'
import SelectButton from 'primevue/selectbutton'
import Tooltip from 'primevue/tooltip'

const toast = useToast()

const dt = ref()
const spaces = ref<Space[]>([])
const spaceDialog = ref(false)
const deleteDialog = ref(false)
const isEditMode = ref(false)
const loading = ref(false)
const currentSpace = ref<Partial<Space>>({})

const visibilityOptions = [
  { label: 'Private', value: 'private' },
  { label: 'Public', value: 'public' }
]

onMounted(async () => {
  await fetchSpaces()
})

async function fetchSpaces() {
  loading.value = true
  try {
    spaces.value = await spaceService.getAllSpaces()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load spaces', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openNew() {
  currentSpace.value = { visibility: 'private' }
  isEditMode.value = false
  spaceDialog.value = true
}

function editSpace(space: Space) {
  currentSpace.value = { ...space }
  isEditMode.value = true
  spaceDialog.value = true
}

function hideDialog() {
  spaceDialog.value = false
  currentSpace.value = {}
}

function confirmDeleteSpace(space: Space) {
  currentSpace.value = { ...space }
  deleteDialog.value = true
}

async function saveSpace() {
  if (!currentSpace.value.name || !currentSpace.value.key) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill in required fields', life: 3000 })
    return
  }

  loading.value = true
  try {
    if (isEditMode.value && currentSpace.value.id) {
      await spaceService.updateSpace(currentSpace.value.id, {
        name: currentSpace.value.name,
        description: currentSpace.value.description,
        visibility: currentSpace.value.visibility as 'private' | 'public'
      })
      toast.add({ severity: 'success', summary: 'Success', detail: 'Space updated successfully', life: 3000 })
    } else {
      await spaceService.createSpace(
        currentSpace.value.key!,
        currentSpace.value.name!,
        currentSpace.value.description,
        currentSpace.value.visibility as 'private' | 'public'
      )
      toast.add({ severity: 'success', summary: 'Success', detail: 'Space created successfully', life: 3000 })
    }

    await fetchSpaces()
    hideDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to save space', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function deleteSpace() {
  if (!currentSpace.value.id) return

  loading.value = true
  try {
    await spaceService.deleteSpace(currentSpace.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Space deleted successfully', life: 3000 })
    await fetchSpaces()
    deleteDialog.value = false
    currentSpace.value = {}
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to delete space', life: 3000 })
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  dt.value.exportCSV()
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
