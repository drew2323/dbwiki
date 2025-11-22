<template>
    <Card class="page-outline-card">
        <template #title>
            <div class="flex items-center gap-2">
                <i class="pi pi-list text-primary"></i>
                <span class="text-base">Table of Contents</span>
            </div>
        </template>

        <template #content>
            <!-- Loading -->
            <div v-if="loading" class="space-y-2">
                <Skeleton height="1.5rem" v-for="i in 3" :key="i"></Skeleton>
            </div>

            <!-- Outline -->
            <nav v-else-if="headings.length > 0" class="space-y-1">
                <a
                    v-for="heading in headings"
                    :key="heading.id"
                    :href="`#${heading.id}`"
                    :class="[
                        'block py-2 px-3 text-sm rounded-md transition-all cursor-pointer',
                        heading.level > 1 ? `pl-${(heading.level - 1) * 2 + 3}` : 'pl-3',
                        activeHeading === heading.id
                            ? 'bg-primary-50 dark:bg-primary-900 text-primary border-l-2 border-primary font-medium'
                            : 'text-color-secondary hover:bg-surface-100 dark:hover:bg-surface-800 border-l-2 border-transparent'
                    ]"
                    @click.prevent="scrollToHeading(heading.id)"
                >
                    {{ heading.text }}
                </a>
            </nav>

            <!-- Empty State -->
            <div v-else class="flex flex-col items-center text-center py-6">
                <i class="pi pi-list text-4xl text-color-secondary mb-2"></i>
                <p class="text-sm text-color-secondary">No headings in this page</p>
            </div>
        </template>
    </Card>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import Card from 'primevue/card';
import Skeleton from 'primevue/skeleton';

interface Props {
    content: any; // Tiptap JSON
    loading?: boolean;
}

interface Heading {
    id: string;
    text: string;
    level: number;
}

const props = withDefaults(defineProps<Props>(), {
    loading: false
});

const headings = ref<Heading[]>([]);
const activeHeading = ref<string | null>(null);

// Extract headings from Tiptap JSON
const extractHeadings = (json: any): Heading[] => {
    if (!json || !json.content) return [];

    const result: Heading[] = [];
    let headingIndex = 0;

    const traverse = (node: any) => {
        if (node.type === 'heading') {
            const text = node.content?.map((n: any) => n.text || '').join('') || 'Untitled';
            const id = `heading-${headingIndex++}`;
            result.push({
                id,
                text,
                level: node.attrs?.level || 1
            });
        }

        if (node.content && Array.isArray(node.content)) {
            node.content.forEach(traverse);
        }
    };

    traverse(json);
    return result;
};

// Scroll to heading
const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        activeHeading.value = id;
    }
};

// Track scroll position to highlight active heading
const handleScroll = () => {
    const scrollPosition = window.scrollY + 100; // Offset for header

    for (let i = headings.value.length - 1; i >= 0; i--) {
        const heading = headings.value[i];
        const element = document.getElementById(heading.id);

        if (element && element.offsetTop <= scrollPosition) {
            activeHeading.value = heading.id;
            break;
        }
    }
};

// Watch for content changes
watch(() => props.content, (newContent) => {
    headings.value = extractHeadings(newContent);
}, { deep: true, immediate: true });

// Setup scroll listener
onMounted(() => {
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check
});

onBeforeUnmount(() => {
    window.removeEventListener('scroll', handleScroll);
});
</script>

<style scoped>
/* Dynamic padding based on heading level */
.pl-4 { padding-left: 1rem; }
.pl-6 { padding-left: 1.5rem; }
.pl-8 { padding-left: 2rem; }
.pl-10 { padding-left: 2.5rem; }
.pl-12 { padding-left: 3rem; }
</style>
