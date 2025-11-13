<template>
  <div class="card">
    <h2 class="text-2xl font-semibold mb-4">User Management</h2>
    <TabView>
      <TabPanel header="Users">
        <UserManagementTab />
      </TabPanel>
      <TabPanel header="Auth Identities">
        <AuthIdentitiesTab />
      </TabPanel>
      <TabPanel header="Roles">
        <RolesTab />
      </TabPanel>
      <TabPanel header="Tenants">
        <TenantsTab />
      </TabPanel>
      <TabPanel header="User-Tenant-Roles">
        <UserTenantRolesTab />
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import UserManagementTab from '@/components/admin/UserManagementTab.vue'
import AuthIdentitiesTab from '@/components/admin/AuthIdentitiesTab.vue'
import RolesTab from '@/components/admin/RolesTab.vue'
import TenantsTab from '@/components/admin/TenantsTab.vue'
import UserTenantRolesTab from '@/components/admin/UserTenantRolesTab.vue'
</script>
