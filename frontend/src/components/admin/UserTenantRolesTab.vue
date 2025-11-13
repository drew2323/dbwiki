<template>
  <div>
    <Toolbar class="mb-4">
      <template #start>
        <Button label="Add Association" icon="pi pi-plus" severity="secondary" @click="openNew" />
      </template>
      <template #end>
        <Select v-model="selectedTenantFilter" :options="tenantOptions" optionLabel="name" optionValue="id" placeholder="Filter by Tenant" class="mr-2" @change="fetchAssociations" showClear />
        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="associations"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      :loading="loading"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} associations"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">User-Tenant-Role Associations</h4>
        </div>
      </template>

      <Column field="user_name" header="User" sortable style="min-width: 14rem">
        <template #body="{ data }">
          <div class="text-sm">
            <div class="font-medium">{{ data.name || data.username }}</div>
            <div class="text-xs text-surface-500">{{ data.email }}</div>
          </div>
        </template>
      </Column>

      <Column field="tenant" header="Tenant" sortable style="min-width: 12rem"></Column>

      <Column field="role" header="Role" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <Chip :label="data.role.name" />
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

      <Column :exportable="false" style="min-width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editAssociation(data)" v-tooltip.top="'Edit Role'" />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDelete(data)" v-tooltip.top="'Remove'" />
        </template>
      </Column>
    </DataTable>

    <!-- Association Dialog -->
    <Dialog v-model:visible="associationDialog" :style="{ width: '500px' }" :header="isEditMode ? 'Edit Association' : 'New Association'" :modal="true" class="p-fluid">
      <div class="field">
        <label for="user" class="font-medium">User *</label>
        <Select id="user" v-model="currentAssociation.user_id" :options="userStore.users" optionLabel="email" optionValue="id" placeholder="Select a user" filter :disabled="isEditMode" />
      </div>
      <div class="field">
        <label for="tenant" class="font-medium">Tenant *</label>
        <Select id="tenant" v-model="currentAssociation.tenant_id" :options="tenantOptions" optionLabel="name" optionValue="id" placeholder="Select a tenant" :disabled="isEditMode" @change="onTenantChange" />
      </div>
      <div class="field">
        <label for="role" class="font-medium">Role *</label>
        <Select id="role" v-model="currentAssociation.role_id" :options="filteredRoles" optionLabel="name" optionValue="id" placeholder="Select a role" :disabled="!currentAssociation.tenant_id" />
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveAssociation" :loading="loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span>Are you sure you want to remove this user-tenant association?</span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteAssociation" :loading="loading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useRoleStore } from '@/stores/roleStore'
import { useTenantStore } from '@/stores/tenantStore'
import { tenantService } from '@/services/tenantService'
import { useToast } from 'primevue/usetoast'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Chip from 'primevue/chip'
import Tooltip from 'primevue/tooltip'

const userStore = useUserStore()
const roleStore = useRoleStore()
const tenantStore = useTenantStore()
const toast = useToast()

const dt = ref()
const associations = ref<any[]>([])
const associationDialog = ref(false)
const deleteDialog = ref(false)
const isEditMode = ref(false)
const loading = ref(false)
const selectedTenantFilter = ref<string | null>(null)
const currentAssociation = ref<any>({})

const tenantOptions = computed(() => {
  return tenantStore.userTenants.map(ut => ut.tenant)
})

const filteredRoles = computed(() => {
  if (!currentAssociation.value.tenant_id) return []
  return roleStore.roles.filter(r => r.tenant_id === currentAssociation.value.tenant_id)
})

onMounted(async () => {
  try {
    await Promise.all([
      userStore.fetchUsers(),
      roleStore.fetchRoles(),
      tenantStore.fetchUserTenants(),
      fetchAssociations()
    ])
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load data', life: 3000 })
  }
})

async function fetchAssociations() {
  loading.value = true
  try {
    if (selectedTenantFilter.value) {
      const data = await tenantService.getTenantUsers(selectedTenantFilter.value)
      const tenantName = tenantOptions.value.find(t => t.id === selectedTenantFilter.value)?.name
      associations.value = data.map((item: any) => ({
        ...item,
        tenant: tenantName,
        tenant_id: selectedTenantFilter.value
      }))
    } else {
      // Fetch all associations across all tenants
      associations.value = []
      for (const ut of tenantStore.userTenants) {
        try {
          const data = await tenantService.getTenantUsers(ut.tenant.id)
          associations.value.push(
            ...data.map((item: any) => ({
              ...item,
              tenant: ut.tenant.name,
              tenant_id: ut.tenant.id
            }))
          )
        } catch (err) {
          console.warn(`Failed to fetch users for tenant ${ut.tenant.name}:`, err)
        }
      }
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load associations', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openNew() {
  currentAssociation.value = {}
  isEditMode.value = false
  associationDialog.value = true
}

function editAssociation(data: any) {
  currentAssociation.value = {
    user_id: data.id,
    tenant_id: data.tenant_id,
    role_id: data.role.id
  }
  isEditMode.value = true
  associationDialog.value = true
}

function onTenantChange() {
  currentAssociation.value.role_id = null
}

function hideDialog() {
  associationDialog.value = false
  currentAssociation.value = {}
}

async function saveAssociation() {
  if (!currentAssociation.value.user_id || !currentAssociation.value.tenant_id || !currentAssociation.value.role_id) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill all required fields', life: 3000 })
    return
  }

  loading.value = true
  try {
    if (isEditMode.value) {
      await tenantStore.updateUserRoleInTenant(
        currentAssociation.value.user_id,
        currentAssociation.value.tenant_id,
        currentAssociation.value.role_id
      )
      toast.add({ severity: 'success', summary: 'Success', detail: 'Role updated successfully', life: 3000 })
    } else {
      await tenantStore.addUserToTenant(
        currentAssociation.value.user_id,
        currentAssociation.value.tenant_id,
        currentAssociation.value.role_id
      )
      toast.add({ severity: 'success', summary: 'Success', detail: 'Association created successfully', life: 3000 })
    }

    await fetchAssociations()
    hideDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to save association', life: 3000 })
  } finally {
    loading.value = false
  }
}

function confirmDelete(data: any) {
  currentAssociation.value = {
    user_id: data.id,
    tenant_id: data.tenant_id
  }
  deleteDialog.value = true
}

async function deleteAssociation() {
  if (!currentAssociation.value.user_id || !currentAssociation.value.tenant_id) return

  loading.value = true
  try {
    await tenantStore.removeUserFromTenant(currentAssociation.value.user_id, currentAssociation.value.tenant_id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Association removed successfully', life: 3000 })
    deleteDialog.value = false
    currentAssociation.value = {}
    await fetchAssociations()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to remove association', life: 3000 })
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
