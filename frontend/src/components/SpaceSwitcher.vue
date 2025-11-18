<template>
  <div class="space-switcher">
    <Dropdown
      v-model="selectedSpaceId"
      :options="spaceOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Select Space"
      @change="handleSpaceChange"
      :loading="spaceStore.loading"
      :disabled="spaceOptions.length === 0"
      class="w-full md:w-14rem"
    >
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex align-items-center gap-2">
          <i class="pi pi-box"></i>
          <span>{{ getCurrentSpaceName(slotProps.value) }}</span>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
        </span>
      </template>
      <template #option="slotProps">
        <div class="flex align-items-center gap-2">
          <i class="pi pi-box"></i>
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
import { useSpaceStore } from '@/stores/spaceStore'
import Dropdown from 'primevue/dropdown'

const spaceStore = useSpaceStore()

const selectedSpaceId = ref<string | null>(spaceStore.currentSpaceId)

// Watch for changes in the store's current space
watch(
  () => spaceStore.currentSpaceId,
  (newId) => {
    selectedSpaceId.value = newId
  }
)

const spaceOptions = computed(() => {
  return spaceStore.userSpaces.map((us) => ({
    label: us.space.name,
    value: us.space.id,
    role: us.role.name
  }))
})

const getCurrentSpaceName = (spaceId: string) => {
  const space = spaceStore.userSpaces.find((us) => us.space.id === spaceId)
  return space?.space.name || 'Unknown Space'
}

const handleSpaceChange = (event: any) => {
  const newSpaceId = event.value
  if (newSpaceId) {
    spaceStore.switchSpace(newSpaceId)
  }
}
</script>

<style scoped>
.space-switcher {
  display: flex;
  align-items: center;
}
</style>
