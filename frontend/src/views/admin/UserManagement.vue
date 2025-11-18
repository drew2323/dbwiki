<template>
  <div class="card">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-3">
      <h2 class="text-2xl font-semibold">User Management</h2>
      <div class="flex gap-2">
        <Tag icon="pi pi-users" :value="`${tabDescriptions[activeIndex].count}`" severity="info" />
      </div>
    </div>

    <TabView v-model:activeIndex="activeIndex">
      <TabPanel>
        <template #header>
          <div class="flex items-center gap-2">
            <i class="pi pi-users"></i>
            <span>Users</span>
          </div>
        </template>
        <UserManagementTab />
      </TabPanel>

      <TabPanel>
        <template #header>
          <div class="flex items-center gap-2">
            <i class="pi pi-box"></i>
            <span>Spaces</span>
          </div>
        </template>
        <SpacesTab />
      </TabPanel>

      <TabPanel>
        <template #header>
          <div class="flex items-center gap-2">
            <i class="pi pi-shield"></i>
            <span>Roles</span>
          </div>
        </template>
        <RolesTab />
      </TabPanel>

      <TabPanel>
        <template #header>
          <div class="flex items-center gap-2">
            <i class="pi pi-sitemap"></i>
            <span class="hidden md:inline">User-Space-Roles</span>
            <span class="md:hidden">Associations</span>
          </div>
        </template>
        <UserSpaceMembershipsTab />
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useRoleStore } from '@/stores/roleStore'

// PrimeVue Components
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Tag from 'primevue/tag'

// Tab Components
import UserManagementTab from '@/components/admin/UserManagementTab.vue'
import SpacesTab from '@/components/admin/SpacesTab.vue'
import RolesTab from '@/components/admin/RolesTab.vue'
import UserSpaceMembershipsTab from '@/components/admin/UserSpaceMembershipsTab.vue'

const userStore = useUserStore()
const roleStore = useRoleStore()

const activeIndex = ref(0)

const tabDescriptions = computed(() => [
  { name: 'Users', count: `${userStore.userCount} users`, icon: 'pi-users' },
  { name: 'Spaces', count: 'Manage spaces', icon: 'pi-box' },
  { name: 'Roles', count: `${roleStore.roleCount} roles`, icon: 'pi-shield' },
  { name: 'Associations', count: 'User-Space-Roles', icon: 'pi-sitemap' }
])
</script>
