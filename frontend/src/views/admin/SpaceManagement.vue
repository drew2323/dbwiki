<template>
    <div class="space-management">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Space Management</h1>
            <p class="text-surface-600 dark:text-surface-400 mt-2">
                Manage your wiki spaces, create new spaces, and configure space settings.
            </p>
        </div>

        <SpacesTab />
    </div>
</template>

<script setup lang="ts">
import SpacesTab from '@/components/admin/SpacesTab.vue';
</script>

<style scoped>
.space-management {
    @apply p-6;
}
</style>
