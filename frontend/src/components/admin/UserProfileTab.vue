<template>
  <div v-if="user" class="flex flex-col gap-4">
    <!-- User Header Card -->
    <Card>
      <template #content>
        <div class="flex flex-col md:flex-row items-center md:items-start gap-4">
          <Avatar v-if="user.picture" :image="user.picture" size="xlarge" shape="circle" />
          <Avatar v-else :label="(user.name || user.email)[0].toUpperCase()" size="xlarge" shape="circle" />

          <div class="flex-1 text-center md:text-left">
            <h2 class="text-2xl font-bold mb-1">{{ user.name || user.username }}</h2>
            <p class="text-surface-600 mb-3">{{ user.email }}</p>
            <div class="flex flex-wrap gap-2 justify-center md:justify-start">
              <Tag :value="user.is_active ? 'Active' : 'Inactive'" :severity="user.is_active ? 'success' : 'danger'" />
              <Tag :value="user.is_verified ? 'Verified' : 'Not Verified'" :severity="user.is_verified ? 'success' : 'warn'" />
              <Tag v-if="user.is_superuser" value="Superuser" severity="warn" icon="pi pi-shield" />
              <Chip v-if="user.last_login" :label="`Last login: ${formatDate(user.last_login)}`" icon="pi pi-clock" />
              <Chip v-else label="Never logged in" icon="pi pi-clock" />
            </div>
          </div>

          <div class="flex gap-2">
            <Button
              :icon="user.is_active ? 'pi pi-ban' : 'pi pi-check'"
              :label="user.is_active ? 'Deactivate' : 'Activate'"
              :severity="user.is_active ? 'warn' : 'success'"
              outlined
              @click="$emit('toggle-status', user)"
            />
            <Button
              icon="pi pi-trash"
              label="Delete"
              severity="danger"
              outlined
              @click="$emit('delete-user', user)"
            />
          </div>
        </div>
      </template>
    </Card>

    <!-- Superuser Management (only visible to superusers) -->
    <Card v-if="authStore.isSuperuser">
      <template #title>
        <div class="flex items-center gap-2">
          <i class="pi pi-shield text-orange-500"></i>
          <span>Superuser Management</span>
        </div>
      </template>
      <template #content>
        <div class="flex flex-col gap-4">
          <div v-if="user.is_superuser" class="flex items-center gap-3 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded">
            <i class="pi pi-shield text-orange-500 text-2xl"></i>
            <div class="flex-1">
              <p class="font-medium text-orange-900 dark:text-orange-200">This user has superuser privileges</p>
              <p class="text-sm text-orange-700 dark:text-orange-300 mt-1">
                Superusers have full access to all spaces and can manage other superusers
              </p>
            </div>
          </div>
          <div v-else class="flex items-center gap-3 p-4 bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded">
            <i class="pi pi-info-circle text-surface-500 text-2xl"></i>
            <div class="flex-1">
              <p class="font-medium">Regular user account</p>
              <p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
                Grant superuser status to give this user full system access
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <Button
              v-if="!user.is_superuser"
              label="Grant Superuser"
              icon="pi pi-shield"
              severity="warn"
              @click="confirmGrantSuperuser"
            />
            <Button
              v-else
              label="Revoke Superuser"
              icon="pi pi-shield"
              severity="danger"
              outlined
              @click="confirmRevokeSuperuser"
              :disabled="user.id === authStore.user?.id"
            />
            <small v-if="user.is_superuser && user.id === authStore.user?.id" class="text-surface-500 self-center ml-2">
              Cannot revoke your own superuser status
            </small>
          </div>
        </div>
      </template>
    </Card>

    <!-- Editable Profile Form -->
    <Card>
      <template #title>Profile Information</template>
      <template #content>
        <div class="flex flex-col gap-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <FloatLabel>
              <InputText id="name" v-model="editableUser.name" class="w-full" />
              <label for="name">Full Name</label>
            </FloatLabel>

            <FloatLabel>
              <InputText id="username" v-model="editableUser.username" class="w-full" required />
              <label for="username">Username *</label>
            </FloatLabel>
          </div>

          <FloatLabel>
            <InputText id="email" v-model="editableUser.email" class="w-full" required type="email" />
            <label for="email">Email *</label>
          </FloatLabel>

          <Divider />

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
              <label class="font-medium text-sm">Account Created</label>
              <div class="flex items-center gap-2 text-surface-600">
                <i class="pi pi-calendar"></i>
                <span>{{ formatDate(user.created_at) }}</span>
              </div>
            </div>

            <div class="flex flex-col gap-2">
              <label class="font-medium text-sm">Last Updated</label>
              <div class="flex items-center gap-2 text-surface-600">
                <i class="pi pi-calendar"></i>
                <span>{{ formatDate(user.updated_at) }}</span>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-2 mt-4">
            <Button label="Reset" icon="pi pi-refresh" outlined @click="resetForm" />
            <Button label="Save Changes" icon="pi pi-check" @click="saveChanges" :loading="loading" />
          </div>
        </div>
      </template>
    </Card>
  </div>
  <div v-else class="text-center py-8 text-surface-500 dark:text-surface-400">
    <i class="pi pi-user text-6xl mb-4 block"></i>
    <p class="text-xl">Select a user to view details</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { useUserStore } from '@/stores/userStore'
import { useAuthStore } from '@/stores/authStore'
import type { User } from '@/types/admin'

// PrimeVue Components
import Card from 'primevue/card'
import Avatar from 'primevue/avatar'
import Tag from 'primevue/tag'
import Chip from 'primevue/chip'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import FloatLabel from 'primevue/floatlabel'
import Divider from 'primevue/divider'

interface Props {
  user: User | null
}

const props = defineProps<Props>()
const emit = defineEmits(['toggle-status', 'delete-user', 'user-updated'])

const userStore = useUserStore()
const authStore = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const editableUser = ref<Partial<User>>({})
const loading = ref(false)

watch(() => props.user, (newUser) => {
  if (newUser) {
    resetForm()
  }
}, { immediate: true })

function resetForm() {
  if (props.user) {
    editableUser.value = {
      name: props.user.name,
      username: props.user.username,
      email: props.user.email
    }
  }
}

async function saveChanges() {
  if (!props.user || !editableUser.value.username || !editableUser.value.email) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill required fields', life: 3000 })
    return
  }

  loading.value = true
  try {
    await userStore.updateUser(props.user.id, {
      name: editableUser.value.name,
      username: editableUser.value.username,
      email: editableUser.value.email
    })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Profile updated successfully', life: 3000 })
    emit('user-updated')
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update profile', life: 3000 })
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function confirmGrantSuperuser() {
  confirm.require({
    message: `Are you sure you want to grant superuser privileges to ${props.user?.name || props.user?.username}? This will give them full access to all spaces and the ability to manage other users.`,
    header: 'Grant Superuser',
    icon: 'pi pi-shield',
    acceptClass: 'p-button-warning',
    accept: async () => {
      await grantSuperuser()
    }
  })
}

function confirmRevokeSuperuser() {
  confirm.require({
    message: `Are you sure you want to revoke superuser privileges from ${props.user?.name || props.user?.username}? They will lose access to spaces where they don't have explicit roles.`,
    header: 'Revoke Superuser',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      await revokeSuperuser()
    }
  })
}

async function grantSuperuser() {
  if (!props.user) return

  loading.value = true
  try {
    await userStore.grantSuperuser(props.user.id)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `${props.user.name || props.user.username} is now a superuser`,
      life: 3000
    })
    emit('user-updated')
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.detail || 'Failed to grant superuser privileges',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

async function revokeSuperuser() {
  if (!props.user) return

  loading.value = true
  try {
    await userStore.revokeSuperuser(props.user.id)
    toast.add({
      severity: 'info',
      summary: 'Success',
      detail: `Superuser privileges revoked from ${props.user.name || props.user.username}`,
      life: 3000
    })
    emit('user-updated')
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.detail || 'Failed to revoke superuser privileges',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}
</script>
