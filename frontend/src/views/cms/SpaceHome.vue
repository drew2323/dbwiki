<template>
    <div class="space-home">
        <!-- Loading State -->
        <div v-if="loading" class="space-y-4">
            <Skeleton height="3rem" width="60%"></Skeleton>
            <Skeleton height="1rem"></Skeleton>
            <Skeleton height="10rem" class="mt-4"></Skeleton>
        </div>

        <!-- Space Info -->
        <div v-else class="space-info">
            <h1 class="text-4xl font-bold mb-4">{{ space?.name }}</h1>

            <div v-if="space?.description" class="text-lg text-muted-color mb-6">
                {{ space.description }}
            </div>

            <!-- If space has home page, redirect to it -->
            <div v-if="space?.home_page_id && homePage">
                <div class="bg-surface-100 dark:bg-surface-800 p-6 rounded-lg mb-6">
                    <div class="flex items-center gap-2 text-muted-color mb-2">
                        <i class="pi pi-home"></i>
                        <span class="text-sm">Redirecting to home page...</span>
                    </div>
                </div>
            </div>

            <!-- No home page set - show recent pages or empty state -->
            <div v-else>
                <!-- Recent Pages -->
                <div v-if="recentPages.length > 0" class="mb-8">
                    <h2 class="text-2xl font-semibold mb-4">Recent Pages</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card
                            v-for="page in recentPages"
                            :key="page.id"
                            class="cursor-pointer hover:shadow-md transition-shadow"
                            @click="goToPage(page)"
                        >
                            <template #title>
                                <div class="flex items-center gap-2">
                                    <i class="pi pi-file text-primary"></i>
                                    <span>{{ page.title }}</span>
                                </div>
                            </template>
                            <template #subtitle>
                                <span class="text-sm text-muted-color">
                                    Updated {{ formatDate(page.updated_at) }}
                                </span>
                            </template>
                        </Card>
                    </div>
                </div>

                <!-- Empty State -->
                <div v-else class="text-center py-12">
                    <i class="pi pi-inbox text-6xl text-muted-color mb-4"></i>
                    <h2 class="text-2xl font-semibold mb-2">No Pages Yet</h2>
                    <p class="text-muted-color mb-6">
                        This wiki is empty. Create your first page to get started.
                    </p>
                    <Button
                        v-if="canEdit"
                        label="Create First Page"
                        icon="pi pi-plus"
                        size="large"
                        @click="showCreateDialog = true"
                    />
                </div>

                <!-- Getting Started (if user can edit) -->
                <div v-if="canEdit && recentPages.length === 0" class="mt-8">
                    <h3 class="text-xl font-semibold mb-4">Getting Started</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card>
                            <template #title>
                                <i class="pi pi-plus-circle text-primary text-2xl mb-2"></i>
                                <div>Create Pages</div>
                            </template>
                            <template #content>
                                <p class="text-sm text-muted-color">
                                    Build your knowledge base by creating pages for different topics
                                </p>
                            </template>
                        </Card>
                        <Card>
                            <template #title>
                                <i class="pi pi-sitemap text-primary text-2xl mb-2"></i>
                                <div>Organize</div>
                            </template>
                            <template #content>
                                <p class="text-sm text-muted-color">
                                    Use the page tree to organize content hierarchically
                                </p>
                            </template>
                        </Card>
                        <Card>
                            <template #title>
                                <i class="pi pi-share-alt text-primary text-2xl mb-2"></i>
                                <div>Collaborate</div>
                            </template>
                            <template #content>
                                <p class="text-sm text-muted-color">
                                    Invite team members and work together on your wiki
                                </p>
                            </template>
                        </Card>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Page Dialog -->
        <CreatePageDialog
            v-if="space"
            v-model:visible="showCreateDialog"
            :space-id="space.id"
            :space-key="route.params.spaceKey as string"
            @created="handlePageCreated"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { pageService, type Page } from '@/services/pageService';
import type { Space } from '@/services/spaceService';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Skeleton from 'primevue/skeleton';
import CreatePageDialog from '@/components/cms/CreatePageDialog.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// Inject space from layout
const space = inject<any>('currentSpace');

// State
const loading = ref(true);
const recentPages = ref<Page[]>([]);
const homePage = ref<Page | null>(null);
const showCreateDialog = ref(false);

// Computed
const canEdit = computed(() => {
    // TODO: Check actual permissions
    return authStore.user?.is_superuser || false;
});

// Load space data
const loadSpaceData = async () => {
    if (!space?.value?.id) return;

    try {
        loading.value = true;

        // Check if space has home page
        if (space.value.home_page_id) {
            try {
                homePage.value = await pageService.getPageById(space.value.home_page_id);
                // Redirect to home page
                router.replace(`/${route.params.spaceKey}/p/${homePage.value.id}-${homePage.value.slug}`);
                return;
            } catch (err) {
                console.error('Failed to load home page:', err);
            }
        }

        // Load recent pages
        const pages = await pageService.listPagesInSpace(space.value.id, 0, 6);
        recentPages.value = pages.sort((a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
    } catch (err) {
        console.error('Failed to load space data:', err);
    } finally {
        loading.value = false;
    }
};

// Navigate to page
const goToPage = (page: Page) => {
    router.push(`/${route.params.spaceKey}/p/${page.id}-${page.slug}`);
};

// Handle page created
const handlePageCreated = async () => {
    // Reload space data to show the new page
    await loadSpaceData();
};

// Format date
const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'today';
    if (days === 1) return 'yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
};

// Watch for space changes
watch(() => space?.value, () => {
    if (space?.value) {
        loadSpaceData();
    }
}, { immediate: true });

onMounted(() => {
    loadSpaceData();
});
</script>

<style scoped>
</style>
