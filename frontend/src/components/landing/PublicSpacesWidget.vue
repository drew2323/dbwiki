<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { spaceService, type Space } from '@/services/spaceService';
import Card from 'primevue/card';
import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';

const router = useRouter();
const spaces = ref<Space[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
    try {
        spaces.value = await spaceService.getPublicSpaces(0, 12);
    } catch (err) {
        console.error('Failed to load public spaces:', err);
        error.value = 'Failed to load public spaces';
    } finally {
        loading.value = false;
    }
});

const viewSpace = (spaceKey: string) => {
    // Navigate to space (will be implemented in Sprint 4)
    router.push(`/${spaceKey}`);
};

const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
};
</script>

<template>
    <section id="public-spaces" class="py-12 px-6 lg:px-20 mx-0 md:mx-12 lg:mx-20">
        <div class="text-center mb-12">
            <div class="text-surface-900 dark:text-surface-0 font-normal mb-2 text-4xl">Explore Public Wikis</div>
            <span class="text-muted-color text-2xl">Discover knowledge shared by our community</span>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card v-for="n in 6" :key="n">
                <template #content>
                    <Skeleton class="mb-4" height="2rem"></Skeleton>
                    <Skeleton class="mb-3" height="1rem"></Skeleton>
                    <Skeleton class="mb-3" height="1rem"></Skeleton>
                    <Skeleton height="1rem" width="70%"></Skeleton>
                </template>
            </Card>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-12">
            <i class="pi pi-exclamation-triangle text-6xl text-red-500 mb-4"></i>
            <p class="text-xl text-muted-color">{{ error }}</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="spaces.length === 0" class="text-center py-12">
            <i class="pi pi-inbox text-6xl text-muted-color mb-4"></i>
            <p class="text-xl text-muted-color">No public wikis available yet</p>
            <p class="text-muted-color mt-2">Be the first to create one!</p>
        </div>

        <!-- Spaces Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card
                v-for="space in spaces"
                :key="space.id"
                class="cursor-pointer hover:shadow-lg transition-shadow"
                @click="viewSpace(space.key)"
            >
                <template #title>
                    <div class="flex items-center gap-2">
                        <i class="pi pi-book text-primary"></i>
                        <span>{{ space.name }}</span>
                    </div>
                </template>
                <template #subtitle>
                    <div class="flex items-center gap-2 text-sm text-muted-color">
                        <i class="pi pi-globe"></i>
                        <span>/{{ space.key }}</span>
                    </div>
                </template>
                <template #content>
                    <p class="text-muted-color line-clamp-3 mb-4">
                        {{ space.description || 'No description available' }}
                    </p>
                    <div class="flex items-center justify-between text-sm text-muted-color">
                        <span>
                            <i class="pi pi-calendar mr-1"></i>
                            {{ formatDate(space.created_at) }}
                        </span>
                        <Button
                            label="View"
                            icon="pi pi-arrow-right"
                            size="small"
                            text
                            @click.stop="viewSpace(space.key)"
                        />
                    </div>
                </template>
            </Card>
        </div>

        <!-- View All Link -->
        <div v-if="spaces.length > 0" class="text-center mt-8">
            <Button
                label="View All Public Wikis"
                icon="pi pi-arrow-right"
                iconPos="right"
                outlined
                size="large"
            />
        </div>
    </section>
</template>

<style scoped>
.line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
</style>
