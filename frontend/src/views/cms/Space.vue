<template>
    <SpaceLayout @create-root-page="handleCreateRootPage">
        <!-- Page Tree (left sidebar) -->
        <template #tree>
            <div v-if="!loading && !currentSpace" class="text-center py-8 text-sm text-muted-color">
                <i class="pi pi-lock text-3xl mb-2"></i>
                <p>This space does not exist or you do not have access to it.</p>
            </div>
            <PageTree
                ref="pageTreeRef"
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
import { ref, computed, onMounted, provide, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { spaceService, type SpaceDetail } from '@/services/spaceService';
import SpaceLayout from '@/layout/SpaceLayout.vue';
import PageTree from '@/components/cms/PageTree.vue';

const route = useRoute();
const authStore = useAuthStore();

// Refs
const pageTreeRef = ref();

// State
const currentSpace = ref<SpaceDetail | null>(null);
const loading = ref(true);

// Load space data
const loadSpace = async () => {
    // First, check authentication status
    if (!authStore.initialized) {
        await authStore.fetchUser();
    }

    const spaceKey = route.params.spaceKey as string;

    loading.value = true;
    try {
        // Works for public spaces without login and for private spaces the user may read
        currentSpace.value = await spaceService.getSpaceByKey(spaceKey);
    } catch (error) {
        console.error('Failed to load space:', error);
        currentSpace.value = null;
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    loadSpace();
});

// Watch for route changes to reload space
watch(
    () => route.params.spaceKey,
    (newSpaceKey, oldSpaceKey) => {
        if (newSpaceKey && newSpaceKey !== oldSpaceKey) {
            console.log('Space.vue: Route changed from', oldSpaceKey, 'to', newSpaceKey);
            loadSpace();
        }
    }
);

// Computed - edit rights come from the backend (superuser, creator or admin/edit role)
const canEdit = computed(() => !!currentSpace.value?.can_edit && authStore.isAuthenticated);

// Provide space context to child components
provide('currentSpace', currentSpace);
provide('spaceCanEdit', canEdit);

// Methods
const handleCreateRootPage = () => {
    pageTreeRef.value?.createRootPage();
};
</script>

<style scoped>
</style>
