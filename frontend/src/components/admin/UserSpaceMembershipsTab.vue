<template>
  <div v-if="user">
    <Toolbar class="mb-4">
      <template #start>
        <Button label="Add Membership" icon="pi pi-plus" severity="secondary" @click="openNew" size="small" />
      </template>
      <template #end>
        <Badge :value="memberships.length" severity="info" />
      </template>
    </Toolbar>

    <DataTable
      :value="memberships"
      dataKey="space_id"
      :loading="loading"
      responsive-layout="scroll"
      breakpoint="768px"
    >
      <template #empty>
        <div class="text-center py-8 text-surface-500 dark:text-surface-400">
          <i class="pi pi-box text-4xl mb-3 block"></i>
          <p>No space memberships found</p>
          <Button label="Add First Membership" icon="pi pi-plus" class="mt-3" @click="openNew" size="small" />
        </div>
      </template>

      <Column field="space" header="Space" style="min-width: 12rem">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <i class="pi pi-box text-primary"></i>
            <span class="font-medium">{{ data.space }}</span>
          </div>
        </template>
      </Column>

      <Column field="role.name" header="Role" style="min-width: 10rem">
        <template #body="{ data }">
          <Chip :label="data.role.name" icon="pi pi-shield" />
        </template>
      </Column>

      <Column field="role.permissions" header="Permissions" style="min-width: 20rem">
        <template #body="{ data }">
          <div class="flex flex-wrap gap-1">
            <Chip
              v-for="(value, key) in getActivePermissions(data.role?.permissions)"
              :key="key"
              :label="key"
              class="text-xs"
            />
            <span v-if="!data.role?.permissions || Object.keys(getActivePermissions(data.role.permissions)).length === 0" class="text-surface-500 text-sm">
              No permissions
            </span>
          </div>
        </template>
      </Column>

      <Column field="is_active" header="Status" style="min-width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'danger'" />
        </template>
      </Column>

      <Column :exportable="false" style="min-width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded size="small" class="mr-2" @click="editMembership(data)" v-tooltip.top="'Change Role'" />
          <Button icon="pi pi-trash" outlined rounded size="small" severity="danger" @click="confirmDelete(data)" v-tooltip.top="'Remove'" />
        </template>
      </Column>
    </DataTable>

    <!-- Add/Edit Membership Dialog -->
    <Dialog v-model:visible="membershipDialog" :style="{ width: '550px' }" :header="isEditMode ? 'Edit Membership' : 'Add Membership'" :modal="true" class="p-fluid">
      <div class="flex flex-col gap-6">
        <FloatLabel class="mt-6">
          <Select
            id="space"
            v-model="currentMembership.space_id"
            :options="availableSpaces"
            optionLabel="name"
            optionValue="id"
            :disabled="isEditMode"
            class="w-full"
            :invalid="!currentMembership.space_id"
          >
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex items-center gap-2">
                <i class="pi pi-box"></i>
                <span>{{ availableSpaces.find(s => s.id === slotProps.value)?.name }}</span>
              </div>
            </template>
          </Select>
          <label for="space">Space *</label>
        </FloatLabel>

        <FloatLabel>
          <Select
            id="role"
            v-model="currentMembership.role_id"
            :options="filteredRoles"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            :invalid="!currentMembership.role_id"
          >
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex items-center gap-2">
                <i class="pi pi-shield"></i>
                <span>{{ filteredRoles.find(r => r.id === slotProps.value)?.name }}</span>
              </div>
            </template>
          </Select>
          <label for="role">Role *</label>
        </FloatLabel>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveMembership" :loading="loading" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="deleteDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle !text-3xl"></i>
        <span v-if="currentMembership.space">
          Are you sure you want to remove this user from <b>{{ currentMembership.space }}</b>?
        </span>
      </div>
      <template #footer>
        <Button label="No" icon="pi pi-times" text @click="deleteDialog = false" />
        <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteMembership" :loading="loading" />
      </template>
    </Dialog>
  </div>
  <div v-else class="text-center py-8 text-surface-500 dark:text-surface-400">
    <i class="pi pi-box text-6xl mb-4 block"></i>
    <p class="text-xl">Select a user to view space memberships</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useSpaceStore } from '@/stores/spaceStore'
import { useRoleStore } from '@/stores/roleStore'
import { useAuthStore } from '@/stores/authStore'
import { spaceService } from '@/services/spaceService'
import type { User } from '@/types/admin'

// PrimeVue Components
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import FloatLabel from 'primevue/floatlabel'
import Tag from 'primevue/tag'
import Chip from 'primevue/chip'
import Badge from 'primevue/badge'
import Tooltip from 'primevue/tooltip'

interface Props {
  user: User | null
}

const props = defineProps<Props>()

const spaceStore = useSpaceStore()
const roleStore = useRoleStore()
const authStore = useAuthStore()
const toast = useToast()

const memberships = ref<any[]>([])
const membershipDialog = ref(false)
const deleteDialog = ref(false)
const isEditMode = ref(false)
const loading = ref(false)
const currentMembership = ref<any>({})
const allSpaces = ref<any[]>([])

const availableSpaces = computed(() => {
  return allSpaces.value
})

const filteredRoles = computed(() => {
  // Roles are now global, return all roles (no space filtering needed)
  return roleStore.roles
})

watch(() => props.user, async (newUser) => {
  if (newUser) {
    await fetchMemberships()
  } else {
    memberships.value = []
  }
}, { immediate: true })

onMounted(async () => {
  await Promise.all([
    fetchAllSpaces(),
    roleStore.fetchRoles()
  ])
})

async function fetchAllSpaces() {
  try {
    // Superusers and admins see spaces where they have admin rights
    // This filters based on backend logic (superusers see all, admins see their admin spaces)
    allSpaces.value = await spaceService.getAdminSpaces()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load spaces', life: 3000 })
  }
}

async function fetchMemberships() {
  if (!props.user) return

  loading.value = true
  try {
    memberships.value = []
    for (const space of allSpaces.value) {
      try {
        const data = await spaceService.getSpaceUsers(space.id)
        const userMembership = data.find((u: any) => u.id === props.user?.id)
        if (userMembership) {
          memberships.value.push({
            ...userMembership,
            space: space.name,
            space_id: space.id
          })
        }
      } catch (err) {
        console.warn(`Failed to fetch users for space ${space.name}:`, err)
      }
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load memberships', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openNew() {
  currentMembership.value = {}
  isEditMode.value = false
  membershipDialog.value = true
}

function editMembership(data: any) {
  currentMembership.value = {
    space_id: data.space_id,
    space: data.space,
    role_id: data.role.id
  }
  isEditMode.value = true
  membershipDialog.value = true
}

function hideDialog() {
  membershipDialog.value = false
  currentMembership.value = {}
}

async function saveMembership() {
  if (!props.user || !currentMembership.value.space_id || !currentMembership.value.role_id) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill all required fields', life: 3000 })
    return
  }

  loading.value = true
  try {
    if (isEditMode.value) {
      await spaceService.updateUserRoleInSpace(
        props.user.id,
        currentMembership.value.space_id,
        currentMembership.value.role_id
      )
      toast.add({ severity: 'success', summary: 'Success', detail: 'Role updated successfully', life: 3000 })
    } else {
      await spaceService.addUserToSpace(
        props.user.id,
        currentMembership.value.space_id,
        currentMembership.value.role_id
      )
      toast.add({ severity: 'success', summary: 'Success', detail: 'Membership added successfully', life: 3000 })
    }

    await fetchMemberships()
    hideDialog()
  } catch (error: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to save membership', life: 3000 })
  } finally {
    loading.value = false
  }
}

function confirmDelete(data: any) {
  currentMembership.value = {
    space_id: data.space_id,
    space: data.space
  }
  deleteDialog.value = true
}

async function deleteMembership() {
  if (!props.user || !currentMembership.value.space_id) return

  loading.value = true
  try {
    await spaceService.removeUserFromSpace(props.user.id, currentMembership.value.space_id)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Membership removed successfully', life: 3000 })
    deleteDialog.value = false
    currentMembership.value = {}
    await fetchMemberships()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to remove membership', life: 3000 })
  } finally {
    loading.value = false
  }
}

function getActivePermissions(permissions: Record<string, any> | null | undefined) {
  if (!permissions || typeof permissions !== 'object') {
    return {}
  }
  const active: Record<string, any> = {}
  Object.keys(permissions).forEach(key => {
    if (permissions[key] === true || permissions[key] === 'true') {
      active[key] = permissions[key]
    }
  })
  return active
}
</script>
