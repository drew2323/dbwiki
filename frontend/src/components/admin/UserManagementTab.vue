<template>
  <div>
    <Toolbar class="mb-4">
      <template #start>
        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV" class="mr-2" />
      </template>
      <template #end>
        <IconField>
          <InputIcon>
            <i class="pi pi-search" />
          </InputIcon>
          <InputText v-model="filters.global.value" placeholder="Search users..." />
        </IconField>
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      v-model:selection="selectedUsers"
      :value="userStore.users"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      :filters="filters"
      :loading="userStore.loading"
      :globalFilterFields="['name', 'email', 'username']"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} users"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">Manage Users</h4>
          <span class="text-sm text-surface-500">Total: {{ userStore.userCount }}</span>
        </div>
      </template>

      <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>

      <Column field="name" header="Name" sortable style="min-width: 14rem">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <Avatar v-if="data.picture" :image="data.picture" shape="circle" size="normal" />
            <Avatar v-else :label="data.name ? data.name[0].toUpperCase() : data.email[0].toUpperCase()" shape="circle" size="normal" />
            <div>
              <div class="font-medium">{{ data.name || 'N/A' }}</div>
              <div class="text-xs text-surface-500">{{ data.username }}</div>
            </div>
          </div>
        </template>
      </Column>

      <Column field="email" header="Email" sortable style="min-width: 12rem"></Column>

      <Column field="is_active" header="Status" sortable style="min-width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'danger'" />
        </template>
      </Column>

      <Column field="is_verified" header="Verified" sortable style="min-width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.is_verified ? 'Yes' : 'No'" :severity="data.is_verified ? 'success' : 'warn'" />
        </template>
      </Column>

      <Column field="created_at" header="Created" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <div class="text-sm">
            {{ formatDate(data.created_at) }}
          </div>
        </template>
      </Column>

      <Column field="last_login" header="Last Login" sortable style="min-width: 10rem">
        <template #body="{ data }">
          <div class="text-sm text-surface-500">
            {{ data.last_login ? formatDate(data.last_login) : 'Never' }}
          </div>
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 12rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editUser(data)" v-tooltip.top="'Edit'" />
          <Button icon="pi pi-key" outlined rounded severity="info" class="mr-2" @click="manageIdentities(data)" v-tooltip.top="'Auth Identities'" />
          <Button
            :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check'"
            outlined
            rounded
            :severity="data.is_active ? 'warn' : 'success'"
            class="mr-2"
            @click="toggleUserStatus(data)"
            :v-tooltip.top="data.is_active ? 'Deactivate' : 'Activate'"
          />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteUser(data)" v-tooltip.top="'Delete'" />
        </template>
      </Column>
    </DataTable>

    <!-- User Edit Dialog -->
    <Dialog v-model:visible="userDialog" :style="{ width: '450px' }" header="User Details" :modal="true" class="p-fluid">
      <div class="field">
        <label for="name">Name</label>
        <InputText id="name" v-model="currentUser.name" />
      </div>
      <div class="field">
        <label for="email" class="font-medium">Email</label>
        <InputText id="email" v-model="currentUser.email" required />
      </div>
      <div class="field">
        <label for="username" class="font-medium">Username</label>
        <InputText id="username" v-model="currentUser.username" required />
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveUser" :loading="userStore.loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteUserDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="currentUser">
          Are you sure you want to delete user <b>{{ currentUser.name || currentUser.email }}</b>?
        </span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteUserDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteUser" :loading="userStore.loading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useTenantStore } from '@/stores/tenantStore'
import { useToast } from 'primevue/usetoast'
import { FilterMatchMode } from '@primevue/core/api'
import type { User } from '@/types/admin'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import Tag from 'primevue/tag'
import Avatar from 'primevue/avatar'
import Tooltip from 'primevue/tooltip'

const userStore = useUserStore()
const tenantStore = useTenantStore()
const toast = useToast()

const dt = ref()
const selectedUsers = ref()
const userDialog = ref(false)
const deleteUserDialog = ref(false)
const currentUser = ref<Partial<User>>({})
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

onMounted(async () => {
  try {
    await userStore.fetchUsers()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 })
  }
})

function editUser(user: User) {
  currentUser.value = { ...user }
  userDialog.value = true
}

function manageIdentities(user: User) {
  // Emit event or navigate to auth identities tab with user selected
  toast.add({ severity: 'info', summary: 'Info', detail: 'Switch to Auth Identities tab to manage', life: 3000 })
}

function hideDialog() {
  userDialog.value = false
  currentUser.value = {}
}

async function saveUser() {
  if (!currentUser.value.id || !currentUser.value.email || !currentUser.value.username) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill required fields', life: 3000 })
    return
  }

  try {
    await userStore.updateUser(currentUser.value.id, {
      name: currentUser.value.name,
      email: currentUser.value.email,
      username: currentUser.value.username
    })
    toast.add({ severity: 'success', summary: 'Success', detail: 'User updated successfully', life: 3000 })
    hideDialog()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update user', life: 3000 })
  }
}

async function toggleUserStatus(user: User) {
  try {
    if (user.is_active) {
      await userStore.deactivateUser(user.id)
      toast.add({ severity: 'info', summary: 'Success', detail: 'User deactivated', life: 3000 })
    } else {
      await userStore.activateUser(user.id)
      toast.add({ severity: 'success', summary: 'Success', detail: 'User activated', life: 3000 })
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update user status', life: 3000 })
  }
}

function confirmDeleteUser(user: User) {
  currentUser.value = user
  deleteUserDialog.value = true
}

async function deleteUser() {
  if (!currentUser.value.id) return

  try {
    await userStore.deleteUser(currentUser.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'User deleted successfully', life: 3000 })
    deleteUserDialog.value = false
    currentUser.value = {}
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete user', life: 3000 })
  }
}

function exportCSV() {
  dt.value.exportCSV()
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
