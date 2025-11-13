<template>
  <div>
    <Toolbar class="mb-4">
      <template #start>
        <Button label="New Tenant" icon="pi pi-plus" severity="secondary" @click="openNew" class="mr-2" />
      </template>
      <template #end>
        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="tenants"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      :loading="loading"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} tenants"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">Manage Tenants</h4>
        </div>
      </template>

      <Column field="name" header="Name" sortable style="min-width: 14rem">
        <template #body="{ data }">
          <div class="font-medium">{{ data.name }}</div>
        </template>
      </Column>

      <Column field="subdomain" header="Subdomain" sortable style="min-width: 12rem">
        <template #body="{ data }">
          <span class="text-sm">{{ data.subdomain || '-' }}</span>
        </template>
      </Column>

      <Column field="is_active" header="Status" sortable style="min-width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'danger'" />
        </template>
      </Column>

      <Column field="created_at" header="Created" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-sm">{{ formatDate(data.created_at) }}</span>
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 10rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editTenant(data)" v-tooltip.top="'Edit'" />
          <Button
            :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check'"
            outlined
            rounded
            :severity="data.is_active ? 'warn' : 'success'"
            class="mr-2"
            @click="toggleTenantStatus(data)"
            :v-tooltip.top="data.is_active ? 'Deactivate' : 'Activate'"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Tenant Dialog -->
    <Dialog v-model:visible="tenantDialog" :style="{ width: '450px' }" :header="isEditMode ? 'Edit Tenant' : 'New Tenant'" :modal="true" class="p-fluid">
      <div class="field">
        <label for="name" class="font-medium">Tenant Name *</label>
        <InputText id="name" v-model="currentTenant.name" required />
      </div>
      <div class="field">
        <label for="subdomain" class="font-medium">Subdomain</label>
        <InputText id="subdomain" v-model="currentTenant.subdomain" placeholder="Optional unique subdomain" />
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveTenant" :loading="loading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { tenantService, type Tenant } from '@/services/tenantService'
import { useToast } from 'primevue/usetoast'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import Tooltip from 'primevue/tooltip'

const toast = useToast()

const dt = ref()
const tenants = ref<Tenant[]>([])
const tenantDialog = ref(false)
const isEditMode = ref(false)
const loading = ref(false)
const currentTenant = ref<Partial<Tenant>>({})

onMounted(async () => {
  await fetchTenants()
})

async function fetchTenants() {
  loading.value = true
  try {
    tenants.value = await tenantService.getAllTenants()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load tenants', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openNew() {
  currentTenant.value = {}
  isEditMode.value = false
  tenantDialog.value = true
}

function editTenant(tenant: Tenant) {
  currentTenant.value = { ...tenant }
  isEditMode.value = true
  tenantDialog.value = true
}

function hideDialog() {
  tenantDialog.value = false
  currentTenant.value = {}
}

async function saveTenant() {
  if (!currentTenant.value.name) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please enter a tenant name', life: 3000 })
    return
  }

  loading.value = true
  try {
    if (isEditMode.value && currentTenant.value.id) {
      await tenantService.updateTenant(currentTenant.value.id, {
        name: currentTenant.value.name,
        subdomain: currentTenant.value.subdomain
      })
      toast.add({ severity: 'success', summary: 'Success', detail: 'Tenant updated successfully', life: 3000 })
    } else {
      await tenantService.createTenant(currentTenant.value.name, currentTenant.value.subdomain)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Tenant created successfully', life: 3000 })
    }

    await fetchTenants()
    hideDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to save tenant', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function toggleTenantStatus(tenant: Tenant) {
  loading.value = true
  try {
    if (tenant.is_active) {
      await tenantService.deactivateTenant(tenant.id)
      toast.add({ severity: 'info', summary: 'Success', detail: 'Tenant deactivated', life: 3000 })
    } else {
      await tenantService.activateTenant(tenant.id)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Tenant activated', life: 3000 })
    }
    await fetchTenants()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update tenant status', life: 3000 })
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
