<template>
    <div class="space-layout min-h-screen bg-surface-0 dark:bg-surface-900">
        <!-- Space Header/Topbar -->
        <Toolbar class="border-b border-surface">
            <template #start>
                <div class="flex items-center gap-3">
                    <router-link to="/" class="text-color-secondary hover:text-primary transition-colors">
                        <i class="pi pi-home text-xl"></i>
                    </router-link>
                    <i class="pi pi-chevron-right text-color-secondary text-sm"></i>
                    <div class="flex items-center gap-2">
                        <i class="pi pi-book text-primary text-xl"></i>
                        <span class="font-semibold text-lg">{{ currentSpace?.name || 'Loading...' }}</span>
                        <Tag v-if="currentSpace?.is_public" icon="pi pi-globe" value="Public" severity="success" rounded />
                    </div>
                </div>
            </template>

            <template #end>
                <div class="flex items-center gap-2">
                    <Button
                        v-if="isAuthenticated && canEdit"
                        :label="isEditing ? 'View Mode' : 'Edit Mode'"
                        :icon="isEditing ? 'pi pi-eye' : 'pi pi-pencil'"
                        :severity="isEditing ? 'success' : 'secondary'"
                        text
                        @click="toggleEditMode"
                    />
                    <Button
                        v-if="!isAuthenticated"
                        label="Login"
                        icon="pi pi-sign-in"
                        severity="secondary"
                        outlined
                        @click="$router.push('/auth/login')"
                    />
                    <Button
                        v-else
                        icon="pi pi-user"
                        text
                        rounded
                        v-tooltip.bottom="'Admin Dashboard'"
                        @click="$router.push('/admin')"
                    />
                </div>
            </template>
        </Toolbar>

        <!-- Main Content Area: Tree | Content | Sidebar -->
        <div class="flex h-[calc(100vh-4rem)]">
            <!-- Left Sidebar: Page Tree -->
            <div
                class="page-tree-sidebar border-r border-surface bg-surface-50 dark:bg-surface-900 overflow-y-auto transition-all duration-300"
                :class="{
                    'w-0': !showTree,
                    'w-full': showTree && isMobile,
                    'w-64 lg:w-72': showTree && !isMobile
                }"
            >
                <div v-if="showTree" class="h-full flex flex-col">
                    <div class="flex items-center justify-between p-4 border-b border-surface">
                        <div class="flex items-center gap-2">
                            <i class="pi pi-sitemap text-primary"></i>
                            <span class="font-semibold">Pages</span>
                        </div>
                        <Button
                            icon="pi pi-times"
                            text
                            rounded
                            size="small"
                            severity="secondary"
                            @click="showTree = false"
                        />
                    </div>
                    <div class="flex-1 overflow-y-auto p-3">
                        <slot name="tree"></slot>
                    </div>
                </div>
            </div>

            <!-- Toggle Tree Button (when hidden) -->
            <Button
                v-if="!showTree"
                icon="pi pi-bars"
                severity="secondary"
                rounded
                class="fixed top-20 left-4 z-10 shadow-lg"
                v-tooltip.right="'Show Pages'"
                @click="showTree = true"
            />

            <!-- Main Content -->
            <div class="flex-1 overflow-y-auto bg-surface-0 dark:bg-surface-950">
                <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <router-view></router-view>
                </div>
            </div>

            <!-- Right Sidebar: Metadata, Backlinks, Attachments -->
            <div
                class="metadata-sidebar border-l border-surface bg-surface-50 dark:bg-surface-900 overflow-y-auto transition-all duration-300"
                :class="{
                    'w-0': !showSidebar,
                    'w-full': showSidebar && isMobile,
                    'w-80 lg:w-96': showSidebar && !isMobile
                }"
            >
                <div v-if="showSidebar" class="h-full flex flex-col">
                    <div class="flex items-center justify-between p-4 border-b border-surface">
                        <div class="flex items-center gap-2">
                            <i class="pi pi-info-circle text-primary"></i>
                            <span class="font-semibold">Page Info</span>
                        </div>
                        <Button
                            icon="pi pi-times"
                            text
                            rounded
                            size="small"
                            severity="secondary"
                            @click="showSidebar = false"
                        />
                    </div>
                    <!-- Teleport target for page components -->
                    <div class="flex-1 overflow-y-auto p-3">
                        <slot name="sidebar"></slot>
                    </div>
                </div>
            </div>

            <!-- Toggle Sidebar Button (when hidden) -->
            <Button
                v-if="!showSidebar"
                icon="pi pi-info-circle"
                severity="secondary"
                rounded
                class="fixed top-20 right-4 z-10 shadow-lg"
                v-tooltip.left="'Show Page Info'"
                @click="showSidebar = true"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, provide, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import Button from 'primevue/button';
import Toolbar from 'primevue/toolbar';
import Tag from 'primevue/tag';

const authStore = useAuthStore();

// Layout state
const showTree = ref(true);
const showSidebar = ref(true);
const isEditing = ref(false);
const isMobile = ref(false);

// Inject current space from parent (Space.vue)
const currentSpace = inject<any>('currentSpace');

// Computed
const isAuthenticated = computed(() => authStore.isAuthenticated);
const canEdit = computed(() => {
    // TODO: Check if user has edit permissions in this space
    return authStore.user?.is_superuser || false;
});

// Provide isEditing to child components
provide('isEditing', isEditing);

// Methods
const toggleEditMode = () => {
    isEditing.value = !isEditing.value;
};

// Responsive handling
const checkMobile = () => {
    isMobile.value = window.innerWidth < 768;
    // Auto-hide sidebars on mobile
    if (isMobile.value) {
        showTree.value = false;
        showSidebar.value = false;
    }
};

onMounted(() => {
    checkMobile();
    window.addEventListener('resize', checkMobile);
});

onUnmounted(() => {
    window.removeEventListener('resize', checkMobile);
});
</script>

<style scoped>
.space-layout {
    font-family: var(--font-family);
}

.transition-all {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
