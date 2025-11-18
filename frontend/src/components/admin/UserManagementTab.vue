<template>
  <div class="user-management-container">
    <!-- Mobile Header -->
    <div class="lg:hidden mb-4">
      <Card>
        <template #content>
          <div class="flex flex-col gap-3">
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="filters.global.value" placeholder="Search users..." class="w-full" />
            </IconField>
            <div class="flex justify-between items-center">
              <Badge :value="`${userStore.userCount} users`" size="large" />
              <Button label="Export" icon="pi pi-upload" severity="secondary" size="small" @click="exportCSV" />
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Desktop/Tablet: Splitter Layout -->
    <div class="hidden lg:block">
      <Splitter style="height: calc(100vh - 12rem)">
        <SplitterPanel :size="30" :minSize="20" class="overflow-hidden">
          <div class="h-full flex flex-col">
            <!-- Left Panel: User List -->
            <div class="p-3 border-b border-surface">
              <IconField>
                <InputIcon>
                  <i class="pi pi-search" />
                </InputIcon>
                <InputText v-model="filters.global.value" placeholder="Search users..." class="w-full" />
              </IconField>
              <div class="flex justify-between items-center mt-3">
                <span class="text-sm font-medium">Users</span>
                <Badge :value="userStore.userCount" />
              </div>
            </div>

            <div class="flex-1 overflow-auto">
              <DataTable
                v-model:selection="selectedUser"
                :value="filteredUsers"
                dataKey="id"
                selectionMode="single"
                :loading="userStore.loading"
                @row-select="onUserSelect"
                scrollable
                scrollHeight="flex"
                class="user-list-table"
              >
                <Column field="name" style="min-width: 100%">
                  <template #body="{ data }">
                    <div
                      class="flex items-center gap-3 p-2 cursor-pointer transition-colors border-b border-surface"
                      :class="selectedUser?.id === data.id ? 'bg-primary-100 dark:bg-primary-900/20' : 'hover:bg-surface-100 dark:hover:bg-surface-800'"
                    >
                      <Avatar v-if="data.picture" :image="data.picture" shape="circle" size="normal" />
                      <Avatar v-else :label="(data.name || data.email)[0].toUpperCase()" shape="circle" size="normal" />
                      <div class="flex-1 overflow-hidden">
                        <div class="font-medium truncate">{{ data.name || data.username }}</div>
                        <div class="text-xs text-surface-500 dark:text-surface-400 truncate">{{ data.email }}</div>
                        <div class="flex gap-1 mt-1">
                          <Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'danger'" class="text-xs" />
                          <Tag v-if="data.is_superuser" value="Superuser" severity="warn" icon="pi pi-shield" class="text-xs" />
                        </div>
                      </div>
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>

            <div class="p-3 border-t border-surface">
              <Button label="Export All" icon="pi pi-upload" outlined class="w-full" size="small" @click="exportCSV" />
            </div>
          </div>
        </SplitterPanel>

        <SplitterPanel :size="70" class="overflow-hidden">
          <div class="h-full overflow-auto p-4">
            <!-- Right Panel: User Details -->
            <div v-if="selectedUser">
              <TabView>
                <TabPanel header="Profile">
                  <UserProfileTab :user="selectedUser" @toggle-status="toggleUserStatus" @delete-user="confirmDeleteUser" @user-updated="refreshUsers" />
                </TabPanel>
                <TabPanel header="Auth Identities">
                  <UserAuthIdentitiesTab :user="selectedUser" />
                </TabPanel>
                <TabPanel header="Space Memberships">
                  <UserSpaceMembershipsTab :user="selectedUser" />
                </TabPanel>
              </TabView>
            </div>
            <div v-else class="flex items-center justify-center h-full">
              <div class="text-center text-surface-500 dark:text-surface-400">
                <i class="pi pi-users text-6xl mb-4 block"></i>
                <p class="text-xl">Select a user from the list to view details</p>
              </div>
            </div>
          </div>
        </SplitterPanel>
      </Splitter>
    </div>

    <!-- Mobile: Card List View -->
    <div class="lg:hidden">
      <div v-if="!selectedUser" class="grid grid-cols-1 gap-3">
        <Card
          v-for="user in filteredUsers"
          :key="user.id"
          class="cursor-pointer transition-all hover:shadow-md hover:scale-[1.01]"
          @click="selectUser(user)"
        >
          <template #content>
            <div class="flex items-center gap-3">
              <Avatar v-if="user.picture" :image="user.picture" shape="circle" size="large" />
              <Avatar v-else :label="(user.name || user.email)[0].toUpperCase()" shape="circle" size="large" />
              <div class="flex-1">
                <div class="font-semibold">{{ user.name || user.username }}</div>
                <div class="text-sm text-surface-500">{{ user.email }}</div>
                <div class="flex gap-2 mt-2 flex-wrap">
                  <Tag :value="user.is_active ? 'Active' : 'Inactive'" :severity="user.is_active ? 'success' : 'danger'" />
                  <Tag :value="user.is_verified ? 'Verified' : 'Not Verified'" :severity="user.is_verified ? 'success' : 'warn'" />
                  <Tag v-if="user.is_superuser" value="Superuser" severity="warn" icon="pi pi-shield" />
                </div>
              </div>
              <i class="pi pi-chevron-right text-surface-400"></i>
            </div>
          </template>
        </Card>
      </div>

      <!-- Mobile: User Detail View -->
      <div v-else>
        <Button label="Back to List" icon="pi pi-arrow-left" outlined class="mb-4 w-full" @click="selectedUser = null" />
        <TabView>
          <TabPanel header="Profile">
            <UserProfileTab :user="selectedUser" @toggle-status="toggleUserStatus" @delete-user="confirmDeleteUser" @user-updated="refreshUsers" />
          </TabPanel>
          <TabPanel header="Identities">
            <UserAuthIdentitiesTab :user="selectedUser" />
          </TabPanel>
          <TabPanel header="Memberships">
            <UserSpaceMembershipsTab :user="selectedUser" />
          </TabPanel>
        </TabView>
      </div>
    </div>

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
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useToast } from 'primevue/usetoast'
import { FilterMatchMode } from '@primevue/core/api'
import type { User } from '@/types/admin'

// PrimeVue Components
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import Tag from 'primevue/tag'
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'

// Child Components
import UserProfileTab from './UserProfileTab.vue'
import UserAuthIdentitiesTab from './UserAuthIdentitiesTab.vue'
import UserSpaceMembershipsTab from './UserSpaceMembershipsTab.vue'

const userStore = useUserStore()
const toast = useToast()

const dt = ref()
const selectedUser = ref<User | null>(null)
const deleteUserDialog = ref(false)
const currentUser = ref<Partial<User>>({})
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

const filteredUsers = computed(() => {
  if (!filters.value.global.value) return userStore.users

  const searchTerm = filters.value.global.value.toLowerCase()
  return userStore.users.filter(user =>
    user.name?.toLowerCase().includes(searchTerm) ||
    user.email.toLowerCase().includes(searchTerm) ||
    user.username.toLowerCase().includes(searchTerm)
  )
})

onMounted(async () => {
  try {
    await userStore.fetchUsers()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 })
  }
})

function onUserSelect(event: any) {
  selectedUser.value = event.data
}

function selectUser(user: User) {
  selectedUser.value = user
}

async function refreshUsers() {
  try {
    await userStore.fetchUsers()
    // Refresh the selected user data
    if (selectedUser.value) {
      const updatedUser = userStore.users.find(u => u.id === selectedUser.value!.id)
      if (updatedUser) {
        selectedUser.value = updatedUser
      }
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to refresh users', life: 3000 })
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
    await refreshUsers()
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
    selectedUser.value = null
    currentUser.value = {}
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete user', life: 3000 })
  }
}

function exportCSV() {
  // Export filtered users
  const dataToExport = filteredUsers.value.map(user => ({
    Name: user.name || '',
    Username: user.username,
    Email: user.email,
    Status: user.is_active ? 'Active' : 'Inactive',
    Verified: user.is_verified ? 'Yes' : 'No',
    Created: new Date(user.created_at).toLocaleDateString(),
    LastLogin: user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'
  }))

  const csv = [
    Object.keys(dataToExport[0]).join(','),
    ...dataToExport.map(row => Object.values(row).join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `users-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}
</script>

<style scoped>
.user-list-table ::v-deep(.p-datatable-tbody > tr) {
  cursor: pointer;
}

.user-list-table ::v-deep(.p-datatable-tbody > tr > td) {
  padding: 0;
  border: none;
}

.user-list-table ::v-deep(.p-datatable-thead) {
  display: none;
}
</style>
