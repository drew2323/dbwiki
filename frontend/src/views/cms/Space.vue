<template>
    <SpaceLayout>
        <!-- Page Tree (left sidebar) -->
        <template #tree>
            <PageTree
                v-if="currentSpace"
                :spaceId="currentSpace.id"
                :spaceKey="currentSpace.key"
                :canEdit="canEdit"
            />
        </template>

        <!-- Main content (router-view is in SpaceLayout) -->

        <!-- Sidebar (right) -->
        <template #sidebar>
            <div class="space-y-6">
                <!-- Components will be shown/hidden based on current page -->
                <slot name="sidebar-content">
                    <!-- Default empty state -->
                    <div class="text-center py-8 text-muted-color text-sm">
                        Select a page to view details
                    </div>
                </slot>
            </div>
        </template>
    </SpaceLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, provide } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { spaceService, type Space } from '@/services/spaceService';
import SpaceLayout from '@/layout/SpaceLayout.vue';
import PageTree from '@/components/cms/PageTree.vue';

const route = useRoute();
const authStore = useAuthStore();

// State
const currentSpace = ref<Space | null>(null);
const loading = ref(true);

// Load space data
onMounted(async () => {
    // First, check authentication status
    if (!authStore.initialized) {
        await authStore.fetchUser();
    }

    const spaceKey = route.params.spaceKey as string;
    try {
        // For now, we'll fetch from public spaces or user spaces
        const publicSpaces = await spaceService.getPublicSpaces();
        currentSpace.value = publicSpaces.find(s => s.key === spaceKey) || null;

        if (!currentSpace.value && authStore.isAuthenticated) {
            // Try user spaces
            const userSpaces = await spaceService.getMySpaces();
            const userSpace = userSpaces.find(us => us.space.key === spaceKey);
            currentSpace.value = userSpace?.space || null;
        }

        console.log('Space.vue: loaded currentSpace=', currentSpace.value);
    } catch (error) {
        console.error('Failed to load space:', error);
    } finally {
        loading.value = false;
    }
});

// Provide space context to child components
provide('currentSpace', currentSpace);

// Computed
const canEdit = computed(() => {
    // TODO: Check actual space permissions
    return authStore.user?.is_superuser || false;
});
</script>

<style scoped>
</style>
