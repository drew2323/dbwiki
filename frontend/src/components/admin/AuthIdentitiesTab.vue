<template>
  <div class="grid grid-cols-12 gap-4">
    <!-- Left Panel: User List -->
    <div class="col-span-4">
      <Card>
        <template #title>
          <div class="flex justify-between items-center">
            <span>Users</span>
            <Badge :value="userStore.userCount" />
          </div>
        </template>
        <template #content>
          <div class="mb-3">
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText v-model="userSearch" placeholder="Search users..." class="w-full" />
            </IconField>
          </div>

          <DataTable
            :value="filteredUsers"
            selectionMode="single"
            v-model:selection="selectedUser"
            @row-select="onUserSelect"
            dataKey="id"
            :rows="10"
            :paginator="true"
            scrollable
            scrollHeight="500px"
            class="compact-table"
          >
            <Column field="name" header="User">
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <Avatar v-if="data.picture" :image="data.picture" shape="circle" size="small" />
                  <Avatar v-else :label="(data.name || data.email)[0].toUpperCase()" shape="circle" size="small" />
                  <div class="text-sm">
                    <div class="font-medium">{{ data.name || data.username }}</div>
                    <div class="text-xs text-surface-500">{{ data.email }}</div>
                  </div>
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </div>

    <!-- Right Panel: Identity Details -->
    <div class="col-span-8">
      <Card v-if="selectedUser">
        <template #title>
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
              <Avatar v-if="selectedUser.picture" :image="selectedUser.picture" shape="circle" />
              <Avatar v-else :label="(selectedUser.name || selectedUser.email)[0].toUpperCase()" shape="circle" />
              <div>
                <div class="text-lg font-semibold">{{ selectedUser.name || selectedUser.username }}</div>
                <div class="text-sm text-surface-500">{{ selectedUser.email }}</div>
              </div>
            </div>
            <Button label="Add Identity" icon="pi pi-plus" @click="openAddIdentityDialog" size="small" />
          </div>
        </template>
        <template #content>
          <DataTable
            :value="authIdentityStore.identities"
            dataKey="id"
            :loading="authIdentityStore.loading"
          >
            <template #header>
              <div class="flex justify-between">
                <h4 class="m-0">Authentication Identities</h4>
                <Badge :value="authIdentityStore.identityCount" />
              </div>
            </template>

            <Column field="provider" header="Provider" style="width: 15%">
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <i :class="`pi ${getProviderIcon(data.provider)} text-lg`"></i>
                  <span class="font-medium">{{ getProviderLabel(data.provider) }}</span>
                </div>
              </template>
            </Column>

            <Column field="provider_subject" header="Subject" style="width: 30%">
              <template #body="{ data }">
                <span class="text-sm">{{ data.provider_subject }}</span>
              </template>
            </Column>

            <Column field="provider_metadata" header="Metadata" style="width: 35%">
              <template #body="{ data }">
                <div class="text-xs text-surface-600">
                  <Chip v-for="(value, key) in getMetadataDisplay(data.provider_metadata)" :key="key" :label="`${key}: ${value}`" class="mr-1 mb-1" />
                </div>
              </template>
            </Column>

            <Column field="created_at" header="Created" style="width: 15%">
              <template #body="{ data }">
                <span class="text-sm">{{ formatDate(data.created_at) }}</span>
              </template>
            </Column>

            <Column :exportable="false" style="width: 5%">
              <template #body="{ data }">
                <Button icon="pi pi-trash" outlined rounded severity="danger" size="small" @click="confirmDeleteIdentity(data)" v-tooltip.top="'Delete'" />
              </template>
            </Column>

            <template #empty>
              <div class="text-center py-4 text-surface-500">
                No authentication identities found for this user.
              </div>
            </template>
          </DataTable>
        </template>
      </Card>

      <Card v-else>
        <template #content>
          <div class="text-center py-8 text-surface-500">
            <i class="pi pi-users text-4xl mb-3"></i>
            <p>Select a user from the left panel to view their authentication identities</p>
          </div>
        </template>
      </Card>
    </div>

    <!-- Add Identity Dialog -->
    <Dialog v-model:visible="addIdentityDialog" :style="{ width: '550px' }" header="Add Authentication Identity" :modal="true" class="p-fluid">
      <div class="flex flex-col gap-4">
        <FloatLabel>
          <Select id="provider" v-model="newIdentity.provider" :options="authIdentityStore.availableProviders" optionLabel="label" optionValue="name" class="w-full" :invalid="!newIdentity.provider">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex items-center gap-2">
                <i :class="`pi ${authIdentityStore.availableProviders.find(p => p.name === slotProps.value)?.icon}`"></i>
                <span>{{ authIdentityStore.availableProviders.find(p => p.name === slotProps.value)?.label }}</span>
              </div>
            </template>
            <template #option="{ option }">
              <div class="flex items-center gap-2">
                <i :class="`pi ${option.icon}`"></i>
                <span>{{ option.label }}</span>
              </div>
            </template>
          </Select>
          <label for="provider">Provider *</label>
        </FloatLabel>

        <FloatLabel>
          <IconField>
            <InputIcon class="pi pi-id-card" />
            <InputText id="subject" v-model="newIdentity.provider_subject" class="w-full" :invalid="!newIdentity.provider_subject" />
          </IconField>
          <label for="subject">Provider Subject *</label>
        </FloatLabel>
        <small class="text-surface-500 -mt-3">The unique identifier for this user in the provider system (e.g., email for password, sub for OAuth)</small>

        <FloatLabel>
          <Textarea id="metadata" v-model="newIdentity.metadataJson" rows="5" class="w-full" />
          <label for="metadata">Metadata (JSON)</label>
        </FloatLabel>
        <small class="text-surface-500 -mt-3">Optional additional data (excluding sensitive info like passwords or tokens)</small>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="closeAddIdentityDialog" />
        <Button label="Add" icon="pi pi-check" @click="addIdentity" :loading="authIdentityStore.loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteIdentityDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl" />
        <span v-if="currentIdentity">
          Are you sure you want to delete the <b>{{ getProviderLabel(currentIdentity.provider) }}</b> identity?
          <br /><small class="text-surface-500">Subject: {{ currentIdentity.provider_subject }}</small>
        </span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteIdentityDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteIdentity" :loading="authIdentityStore.loading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useAuthIdentityStore } from '@/stores/authIdentityStore'
import { useToast } from 'primevue/usetoast'
import type { User, AuthIdentity } from '@/types/admin'

// PrimeVue Components
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import FloatLabel from 'primevue/floatlabel'
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import Chip from 'primevue/chip'
import Tooltip from 'primevue/tooltip'

const userStore = useUserStore()
const authIdentityStore = useAuthIdentityStore()
const toast = useToast()

const selectedUser = ref<User | null>(null)
const userSearch = ref('')
const addIdentityDialog = ref(false)
const deleteIdentityDialog = ref(false)
const currentIdentity = ref<AuthIdentity | null>(null)
const newIdentity = ref({
  provider: '',
  provider_subject: '',
  metadataJson: '{}'
})

const filteredUsers = computed(() => {
  if (!userSearch.value) return userStore.users
  const search = userSearch.value.toLowerCase()
  return userStore.users.filter(
    u => u.name?.toLowerCase().includes(search) || u.email.toLowerCase().includes(search) || u.username.toLowerCase().includes(search)
  )
})

onMounted(async () => {
  try {
    await Promise.all([userStore.fetchUsers(), authIdentityStore.fetchProviders()])
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load data', life: 3000 })
  }
})

async function onUserSelect(event: any) {
  if (!event.data) return
  try {
    await authIdentityStore.fetchUserIdentities(event.data.id)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load identities', life: 3000 })
  }
}

function openAddIdentityDialog() {
  newIdentity.value = { provider: '', provider_subject: '', metadataJson: '{}' }
  addIdentityDialog.value = true
}

function closeAddIdentityDialog() {
  addIdentityDialog.value = false
}

async function addIdentity() {
  if (!selectedUser.value || !newIdentity.value.provider || !newIdentity.value.provider_subject) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill required fields', life: 3000 })
    return
  }

  try {
    let metadata = {}
    if (newIdentity.value.metadataJson.trim() !== '{}') {
      metadata = JSON.parse(newIdentity.value.metadataJson)
    }

    await authIdentityStore.createIdentity(selectedUser.value.id, {
      provider: newIdentity.value.provider,
      provider_subject: newIdentity.value.provider_subject,
      metadata
    })

    toast.add({ severity: 'success', summary: 'Success', detail: 'Identity added successfully', life: 3000 })
    closeAddIdentityDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message || 'Failed to add identity', life: 3000 })
  }
}

function confirmDeleteIdentity(identity: AuthIdentity) {
  currentIdentity.value = identity
  deleteIdentityDialog.value = true
}

async function deleteIdentity() {
  if (!currentIdentity.value) return

  try {
    await authIdentityStore.deleteIdentity(currentIdentity.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Identity deleted successfully', life: 3000 })
    deleteIdentityDialog.value = false
    currentIdentity.value = null
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete identity', life: 3000 })
  }
}

function getProviderIcon(provider: string) {
  const icons: Record<string, string> = {
    password: 'pi-key',
    google: 'pi-google',
    github: 'pi-github',
    oidc: 'pi-id-card'
  }
  return icons[provider] || 'pi-shield'
}

function getProviderLabel(provider: string) {
  const labels: Record<string, string> = {
    password: 'Password',
    google: 'Google',
    github: 'GitHub',
    oidc: 'OpenID Connect'
  }
  return labels[provider] || provider.charAt(0).toUpperCase() + provider.slice(1)
}

function getMetadataDisplay(metadata: Record<string, any>) {
  // Filter out sensitive keys
  const filtered: Record<string, any> = {}
  Object.keys(metadata).forEach(key => {
    if (key !== 'password_hash' && key !== 'access_token' && key !== 'refresh_token') {
      filtered[key] = typeof metadata[key] === 'string' ? metadata[key] : JSON.stringify(metadata[key])
    }
  })
  return filtered
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.compact-table ::v-deep(.p-datatable-tbody > tr > td) {
  padding: 0.5rem;
}
</style>
