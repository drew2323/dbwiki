<template>
    <Card class="page-backlinks-card">
        <template #title>
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <i class="pi pi-link text-primary"></i>
                    <span class="text-base">Backlinks</span>
                </div>
                <Tag v-if="backlinks.length > 0" :value="backlinks.length" severity="secondary" rounded />
            </div>
        </template>

        <template #content>
            <!-- Loading -->
            <div v-if="loading" class="space-y-2">
                <Skeleton height="2.5rem" v-for="i in 2" :key="i"></Skeleton>
            </div>

            <!-- Backlinks List -->
            <div v-else-if="backlinks.length > 0" class="space-y-2">
                <a
                    v-for="backlink in backlinks"
                    :key="backlink.id"
                    :href="`/${spaceKey}/p/${backlink.src_page_id}-${backlink.src_page_slug}`"
                    class="flex items-center gap-3 p-3 rounded-md hover:bg-surface-100 dark:hover:bg-surface-800 transition-all cursor-pointer border border-transparent hover:border-primary"
                    @click.prevent="navigateToPage(backlink)"
                >
                    <i class="pi pi-arrow-left text-primary"></i>
                    <span class="text-sm font-medium">{{ backlink.src_page_title }}</span>
                </a>
            </div>

            <!-- Empty State -->
            <div v-else class="flex flex-col items-center text-center py-6">
                <i class="pi pi-link text-4xl text-color-secondary mb-2"></i>
                <p class="text-sm text-color-secondary">No pages link here yet</p>
            </div>
        </template>
    </Card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { pageService, type Backlink } from '@/services/pageService';
import Card from 'primevue/card';
import Skeleton from 'primevue/skeleton';
import Tag from 'primevue/tag';

interface Props {
    pageId: string | null;
    spaceKey: string;
}

const props = defineProps<Props>();
const router = useRouter();

const backlinks = ref<Backlink[]>([]);
const loading = ref(false);

// Load backlinks
const loadBacklinks = async () => {
    if (!props.pageId) return;

    try {
        loading.value = true;
        backlinks.value = await pageService.getBacklinks(props.pageId);
    } catch (err) {
        console.error('Failed to load backlinks:', err);
        backlinks.value = [];
    } finally {
        loading.value = false;
    }
};

// Navigate to page
const navigateToPage = (backlink: Backlink) => {
    router.push(`/${props.spaceKey}/p/${backlink.src_page_id}-${backlink.src_page_slug}`);
};

// Watch for page changes
watch(() => props.pageId, () => {
    loadBacklinks();
}, { immediate: true });
</script>

<style scoped>
</style>
