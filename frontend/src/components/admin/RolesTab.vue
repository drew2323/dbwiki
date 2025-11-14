<template>
  <div>
    <Toolbar class="mb-4">
      <template #start>
        <Button label="New Role" icon="pi pi-plus" severity="secondary" @click="openNew" class="mr-2" />
        <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedRoles || !selectedRoles.length" />
      </template>
      <template #end>
        <Select v-model="selectedTenantFilter" :options="tenantOptions" optionLabel="name" optionValue="id" placeholder="Filter by Tenant" class="mr-2" @change="onTenantFilterChange" showClear />
        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      v-model:selection="selectedRoles"
      :value="roleStore.roles"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      :loading="roleStore.loading"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} roles"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">Manage Roles</h4>
          <span class="text-sm text-surface-500">Total: {{ roleStore.roleCount }}</span>
        </div>
      </template>

      <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>

      <Column field="name" header="Role Name" sortable style="min-width: 12rem">
        <template #body="{ data }">
          <div class="font-medium">{{ data.name }}</div>
        </template>
      </Column>

      <Column field="tenant_id" header="Tenant" sortable style="min-width: 12rem">
        <template #body="{ data }">
          <span>{{ getTenantName(data.tenant_id) }}</span>
        </template>
      </Column>

      <Column field="permissions" header="Permissions" style="min-width: 20rem">
        <template #body="{ data }">
          <div class="flex flex-wrap gap-1">
            <Chip v-for="(value, key) in getPermissionChips(data.permissions)" :key="key" :label="key" class="text-xs" />
            <span v-if="Object.keys(data.permissions).length === 0" class="text-surface-500 text-sm">No permissions</span>
          </div>
        </template>
      </Column>

      <Column field="created_at" header="Created" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-sm">{{ formatDate(data.created_at) }}</span>
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 10rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editRole(data)" v-tooltip.top="'Edit'" />
          <Button icon="pi pi-copy" outlined rounded severity="info" class="mr-2" @click="duplicateRole(data)" v-tooltip.top="'Duplicate'" />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteRole(data)" v-tooltip.top="'Delete'" />
        </template>
      </Column>
    </DataTable>

    <!-- Role Dialog -->
    <Dialog v-model:visible="roleDialog" :style="{ width: '600px' }" :header="isEditMode ? 'Edit Role' : 'New Role'" :modal="true" class="p-fluid">
      <div class="flex flex-col gap-6">
        <FloatLabel class="mt-6">
          <InputText id="name" v-model="currentRole.name" required class="w-full" :invalid="!currentRole.name" />
          <label for="name">Role Name *</label>
        </FloatLabel>

        <FloatLabel>
          <Select id="tenant" v-model="currentRole.tenant_id" :options="tenantOptions" optionLabel="name" optionValue="id" :disabled="isEditMode" class="w-full" :invalid="!currentRole.tenant_id" />
          <label for="tenant">Tenant *</label>
        </FloatLabel>

        <FloatLabel>
          <Textarea id="permissions" v-model="currentRole.permissionsJson" rows="8" class="w-full" />
          <label for="permissions">Permissions (JSON)</label>
        </FloatLabel>
        <small class="text-surface-500 -mt-4">JSON format: key-value pairs of permission names and boolean values (e.g., {"read": true, "write": true})</small>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveRole" :loading="roleStore.loading" />
      </template>
    </Dialog>

    <!-- Delete Role Dialog -->
    <Dialog v-model:visible="deleteRoleDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="currentRole">
          Are you sure you want to delete role <b>{{ currentRole.name }}</b>?
        </span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteRoleDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteRole" :loading="roleStore.loading" />
      </template>
    </Dialog>

    <!-- Delete Selected Dialog -->
    <Dialog v-model:visible="deleteRolesDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span>Are you sure you want to delete the selected roles?</span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteRolesDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteSelectedRoles" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoleStore } from '@/stores/roleStore'
import { useTenantStore } from '@/stores/tenantStore'
import { useToast } from 'primevue/usetoast'
import type { Role } from '@/types/admin'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import FloatLabel from 'primevue/floatlabel'
import Chip from 'primevue/chip'
import Tooltip from 'primevue/tooltip'

const roleStore = useRoleStore()
const tenantStore = useTenantStore()
const toast = useToast()

const dt = ref()
const selectedRoles = ref()
const roleDialog = ref(false)
const deleteRoleDialog = ref(false)
const deleteRolesDialog = ref(false)
const isEditMode = ref(false)
const selectedTenantFilter = ref<string | null>(null)
const currentRole = ref<Partial<Role> & { permissionsJson?: string }>({})

const tenantOptions = computed(() => {
  return tenantStore.userTenants.map(ut => ut.tenant)
})

onMounted(async () => {
  try {
    await Promise.all([roleStore.fetchRoles(), tenantStore.fetchUserTenants()])
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load roles', life: 3000 })
  }
})

async function onTenantFilterChange() {
  try {
    await roleStore.fetchRoles(selectedTenantFilter.value || undefined)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to filter roles', life: 3000 })
  }
}

function openNew() {
  currentRole.value = { permissionsJson: '{}' }
  isEditMode.value = false
  roleDialog.value = true
}

function editRole(role: Role) {
  currentRole.value = {
    ...role,
    permissionsJson: JSON.stringify(role.permissions, null, 2)
  }
  isEditMode.value = true
  roleDialog.value = true
}

function duplicateRole(role: Role) {
  currentRole.value = {
    name: `${role.name} (Copy)`,
    tenant_id: role.tenant_id,
    permissionsJson: JSON.stringify(role.permissions, null, 2)
  }
  isEditMode.value = false
  roleDialog.value = true
}

function hideDialog() {
  roleDialog.value = false
  currentRole.value = {}
}

async function saveRole() {
  if (!currentRole.value.name || !currentRole.value.tenant_id) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill required fields', life: 3000 })
    return
  }

  try {
    let permissions = {}
    if (currentRole.value.permissionsJson) {
      permissions = JSON.parse(currentRole.value.permissionsJson)
    }

    if (isEditMode.value && currentRole.value.id) {
      await roleStore.updateRole(currentRole.value.id, {
        name: currentRole.value.name,
        permissions
      })
      toast.add({ severity: 'success', summary: 'Success', detail: 'Role updated successfully', life: 3000 })
    } else {
      await roleStore.createRole({
        name: currentRole.value.name,
        tenant_id: currentRole.value.tenant_id,
        permissions
      })
      toast.add({ severity: 'success', summary: 'Success', detail: 'Role created successfully', life: 3000 })
    }

    hideDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message || 'Failed to save role', life: 3000 })
  }
}

function confirmDeleteRole(role: Role) {
  currentRole.value = role
  deleteRoleDialog.value = true
}

async function deleteRole() {
  if (!currentRole.value.id) return

  try {
    await roleStore.deleteRole(currentRole.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Role deleted successfully', life: 3000 })
    deleteRoleDialog.value = false
    currentRole.value = {}
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete role', life: 3000 })
  }
}

function confirmDeleteSelected() {
  deleteRolesDialog.value = true
}

async function deleteSelectedRoles() {
  try {
    for (const role of selectedRoles.value) {
      await roleStore.deleteRole(role.id)
    }
    toast.add({ severity: 'success', summary: 'Success', detail: 'Roles deleted successfully', life: 3000 })
    deleteRolesDialog.value = false
    selectedRoles.value = null
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some roles', life: 3000 })
  }
}

function getTenantName(tenantId: string) {
  const tenant = tenantStore.userTenants.find(ut => ut.tenant.id === tenantId)
  return tenant?.tenant.name || 'Unknown'
}

function getPermissionChips(permissions: Record<string, any>) {
  // Only show permissions that are set to true
  const active: Record<string, any> = {}
  Object.keys(permissions).forEach(key => {
    if (permissions[key] === true || permissions[key] === 'true') {
      active[key] = permissions[key]
    }
  })
  return active
}

function exportCSV() {
  dt.value.exportCSV()
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
