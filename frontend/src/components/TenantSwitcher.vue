<template>
  <div class="tenant-switcher">
    <Dropdown
      v-model="selectedTenantId"
      :options="tenantOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Select Tenant"
      @change="handleTenantChange"
      :loading="tenantStore.loading"
      :disabled="tenantOptions.length === 0"
      class="w-full md:w-14rem"
    >
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex align-items-center gap-2">
          <i class="pi pi-building"></i>
          <span>{{ getCurrentTenantName(slotProps.value) }}</span>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
        </span>
      </template>
      <template #option="slotProps">
        <div class="flex align-items-center gap-2">
          <i class="pi pi-building"></i>
          <div>
            <div>{{ slotProps.option.label }}</div>
            <div class="text-sm text-500">{{ slotProps.option.role }}</div>
          </div>
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTenantStore } from '@/stores/tenantStore'
import Dropdown from 'primevue/dropdown'

const tenantStore = useTenantStore()

const selectedTenantId = ref<string | null>(tenantStore.currentTenantId)

// Watch for changes in the store's current tenant
watch(
  () => tenantStore.currentTenantId,
  (newId) => {
    selectedTenantId.value = newId
  }
)

const tenantOptions = computed(() => {
  return tenantStore.userTenants.map((ut) => ({
    label: ut.tenant.name,
    value: ut.tenant.id,
    role: ut.role.name
  }))
})

const getCurrentTenantName = (tenantId: string) => {
  const tenant = tenantStore.userTenants.find((ut) => ut.tenant.id === tenantId)
  return tenant?.tenant.name || 'Unknown Tenant'
}

const handleTenantChange = (event: any) => {
  const newTenantId = event.value
  if (newTenantId) {
    tenantStore.switchTenant(newTenantId)
  }
}
</script>

<style scoped>
.tenant-switcher {
  display: flex;
  align-items: center;
}
</style>
