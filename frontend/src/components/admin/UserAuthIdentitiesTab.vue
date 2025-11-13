<template>
  <div v-if="user">
    <Toolbar class="mb-4">
      <template #start>
        <Button label="Add Identity" icon="pi pi-plus" severity="secondary" @click="openAddDialog" size="small" />
      </template>
      <template #end>
        <Badge :value="authIdentityStore.identityCount" severity="info" />
      </template>
    </Toolbar>

    <DataTable
      :value="authIdentityStore.identities"
      dataKey="id"
      :loading="authIdentityStore.loading"
      responsive-layout="scroll"
      breakpoint="768px"
    >
      <template #empty>
        <div class="text-center py-8 text-surface-500 dark:text-surface-400">
          <i class="pi pi-shield text-4xl mb-3 block"></i>
          <p>No authentication identities found</p>
          <Button label="Add First Identity" icon="pi pi-plus" class="mt-3" @click="openAddDialog" size="small" />
        </div>
      </template>

      <Column field="provider" header="Provider" style="min-width: 12rem">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <i :class="`pi ${getProviderIcon(data.provider)} text-lg`"></i>
            <span class="font-medium">{{ getProviderLabel(data.provider) }}</span>
          </div>
        </template>
      </Column>

      <Column field="provider_subject" header="Subject" style="min-width: 15rem">
        <template #body="{ data }">
          <span class="text-sm">{{ data.provider_subject }}</span>
        </template>
      </Column>

      <Column field="provider_metadata" header="Metadata" style="min-width: 20rem">
        <template #body="{ data }">
          <div class="flex flex-wrap gap-1">
            <Chip
              v-for="(value, key) in getMetadataDisplay(data.provider_metadata)"
              :key="key"
              :label="`${key}: ${value}`"
              class="text-xs"
            />
          </div>
        </template>
      </Column>

      <Column field="created_at" header="Created" style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-sm">{{ formatDate(data.created_at) }}</span>
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 5rem">
        <template #body="{ data }">
          <Button icon="pi pi-trash" outlined rounded size="small" severity="danger" @click="confirmDelete(data)" v-tooltip.top="'Delete'" />
        </template>
      </Column>
    </DataTable>

    <!-- Add Identity Dialog -->
    <Dialog v-model:visible="addDialog" :style="{ width: '550px' }" header="Add Authentication Identity" :modal="true" class="p-fluid">
      <div class="flex flex-col gap-4">
        <FloatLabel>
          <Select
            id="provider"
            v-model="newIdentity.provider"
            :options="authIdentityStore.availableProviders"
            optionLabel="label"
            optionValue="name"
            class="w-full"
            :invalid="!newIdentity.provider"
          >
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
        <small class="text-surface-500 -mt-3">The unique identifier for this user in the provider system</small>

        <FloatLabel>
          <Textarea id="metadata" v-model="newIdentity.metadataJson" rows="5" class="w-full" />
          <label for="metadata">Metadata (JSON)</label>
        </FloatLabel>
        <small class="text-surface-500 -mt-3">Optional additional data (excluding sensitive info)</small>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="closeAddDialog" />
        <Button label="Add" icon="pi pi-check" @click="addIdentity" :loading="authIdentityStore.loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl"></i>
        <span v-if="currentIdentity">
          Are you sure you want to delete the <b>{{ getProviderLabel(currentIdentity.provider) }}</b> identity?
        </span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteIdentity" :loading="authIdentityStore.loading" />
      </template>
    </Dialog>
  </div>
  <div v-else class="text-center py-8 text-surface-500 dark:text-surface-400">
    <i class="pi pi-shield text-6xl mb-4 block"></i>
    <p class="text-xl">Select a user to view authentication identities</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useAuthIdentityStore } from '@/stores/authIdentityStore'
import { useToast } from 'primevue/usetoast'
import type { User, AuthIdentity } from '@/types/admin'

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
import Badge from 'primevue/badge'
import Tooltip from 'primevue/tooltip'

interface Props {
  user: User | null
}

const props = defineProps<Props>()

const authIdentityStore = useAuthIdentityStore()
const toast = useToast()

const addDialog = ref(false)
const deleteDialog = ref(false)
const currentIdentity = ref<AuthIdentity | null>(null)
const newIdentity = ref({
  provider: '',
  provider_subject: '',
  metadataJson: '{}'
})

watch(() => props.user, async (newUser) => {
  if (newUser) {
    await authIdentityStore.fetchUserIdentities(newUser.id)
  }
}, { immediate: true })

onMounted(async () => {
  await authIdentityStore.fetchProviders()
})

function openAddDialog() {
  newIdentity.value = { provider: '', provider_subject: '', metadataJson: '{}' }
  addDialog.value = true
}

function closeAddDialog() {
  addDialog.value = false
}

async function addIdentity() {
  if (!props.user || !newIdentity.value.provider || !newIdentity.value.provider_subject) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill required fields', life: 3000 })
    return
  }

  try {
    let metadata = {}
    if (newIdentity.value.metadataJson.trim() !== '{}') {
      metadata = JSON.parse(newIdentity.value.metadataJson)
    }

    await authIdentityStore.createIdentity(props.user.id, {
      provider: newIdentity.value.provider,
      provider_subject: newIdentity.value.provider_subject,
      metadata
    })

    toast.add({ severity: 'success', summary: 'Success', detail: 'Identity added successfully', life: 3000 })
    closeAddDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message || 'Failed to add identity', life: 3000 })
  }
}

function confirmDelete(identity: AuthIdentity) {
  currentIdentity.value = identity
  deleteDialog.value = true
}

async function deleteIdentity() {
  if (!currentIdentity.value) return

  try {
    await authIdentityStore.deleteIdentity(currentIdentity.value.id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Identity deleted successfully', life: 3000 })
    deleteDialog.value = false
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
