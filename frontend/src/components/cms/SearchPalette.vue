<template>
    <Dialog
        v-model:visible="visible"
        modal
        dismissableMask
        :showHeader="false"
        position="top"
        :style="{ width: '40rem', maxWidth: '95vw', marginTop: '10vh' }"
        :pt="{ content: { class: 'p-0' } }"
        @show="onShow"
    >
        <div class="search-palette" data-testid="search-palette">
            <div class="flex items-center gap-2 p-3 border-b border-surface">
                <i class="pi pi-search text-muted-color"></i>
                <input
                    ref="inputRef"
                    v-model="query"
                    type="text"
                    class="search-input flex-1"
                    placeholder="Search pages by title or content…"
                    aria-label="Search pages"
                    autocomplete="off"
                    data-testid="search-input"
                    @keydown.down.prevent="move(1)"
                    @keydown.up.prevent="move(-1)"
                    @keydown.enter.prevent="openActive"
                />
                <i v-if="loading" class="pi pi-spin pi-spinner text-muted-color"></i>
                <kbd class="text-xs text-muted-color border border-surface rounded px-1">Esc</kbd>
            </div>

            <div v-if="spaceKey" class="flex items-center gap-3 px-3 py-2 border-b border-surface text-sm">
                <span class="text-muted-color">Search in</span>
                <button
                    type="button"
                    class="scope-chip"
                    :class="{ active: scope === 'all' }"
                    data-testid="scope-all"
                    @click="scope = 'all'"
                >All spaces</button>
                <button
                    type="button"
                    class="scope-chip"
                    :class="{ active: scope === 'space' }"
                    data-testid="scope-space"
                    @click="scope = 'space'"
                >This space</button>
            </div>

            <div class="results" role="listbox" aria-label="Search results">
                <template v-for="(item, i) in items" :key="`${item.group}-${item.id}`">
                <div
                    v-if="!trimmedQuery && (i === 0 || items[i - 1].group !== item.group)"
                    class="px-3 pt-3 pb-1 text-xs uppercase tracking-wide text-muted-color"
                    :data-testid="`group-${item.group}`"
                >
                    {{ item.group === 'favorite' ? 'Favorites' : 'Recent pages' }}
                </div>

                <div
                    :id="`search-item-${i}`"
                    role="option"
                    :aria-selected="i === activeIndex"
                    class="result-item"
                    :class="{ active: i === activeIndex }"
                    data-testid="search-result"
                    @mouseenter="activeIndex = i"
                    @click="go(item)"
                >
                    <i :class="trimmedQuery ? 'pi pi-file' : item.group === 'favorite' ? 'pi pi-star-fill text-yellow-500' : 'pi pi-history'" class="text-muted-color mt-1"></i>
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                            <span class="font-medium truncate">{{ item.title }}</span>
                            <span v-if="item.spaceName" class="text-xs text-muted-color truncate">{{ item.spaceName }}</span>
                        </div>
                        <div v-if="item.snippet" class="text-sm text-muted-color truncate">{{ item.snippet }}</div>
                    </div>
                    <i v-if="i === activeIndex" class="pi pi-arrow-right text-muted-color text-xs mt-1"></i>
                </div>
                </template>

                <div v-if="!loading && trimmedQuery && items.length === 0 && !failed" class="p-6 text-center text-muted-color">
                    No pages found for “{{ trimmedQuery }}”
                </div>
                <div v-if="failed" class="p-6 text-center text-red-500 text-sm">
                    Search failed. Please try again.
                </div>
                <div v-if="!trimmedQuery && items.length === 0" class="p-6 text-center text-muted-color text-sm">
                    Start typing to search. Starred and recently opened pages show up here.
                </div>
            </div>

            <div class="flex items-center gap-4 px-3 py-2 border-t border-surface text-xs text-muted-color">
                <span><kbd>↑</kbd> <kbd>↓</kbd> navigate</span>
                <span><kbd>Enter</kbd> open</span>
                <span class="ml-auto"><kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>K</kbd> toggle</span>
            </div>
        </div>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import Dialog from 'primevue/dialog';
import { pageService } from '@/services/pageService';
import { useRecentPages } from '@/composables/useRecentPages';
import { useCmsStore } from '@/stores/cmsStore';
import { useFavorites } from '@/composables/useFavorites';
import { useAuthStore } from '@/stores/authStore';

const props = defineProps<{
    /** Space the user is currently in (enables the "this space" filter) */
    spaceId?: string | null;
    spaceKey?: string | null;
}>();

interface Item {
    id: string;
    title: string;
    slug: string;
    spaceKey: string;
    spaceName?: string | null;
    snippet?: string | null;
    group?: 'favorite' | 'recent' | 'result';
}

const router = useRouter();
const cms = useCmsStore();
const { recent } = useRecentPages();
const { favorites, load: loadFavorites } = useFavorites();
const authStore = useAuthStore();

const visible = ref(false);
const query = ref('');
const scope = ref<'all' | 'space'>('all');
const loading = ref(false);
const failed = ref(false);
const results = ref<Item[]>([]);
const activeIndex = ref(0);
const inputRef = ref<HTMLInputElement | null>(null);

const trimmedQuery = computed(() => query.value.trim());

// Empty query shows favorites, then recently opened pages, for quick navigation
const items = computed<Item[]>(() => {
    if (trimmedQuery.value) return results.value;
    const starred: Item[] = favorites.value.map(f => ({
        id: f.page_id, title: f.title, slug: f.slug, spaceKey: f.space_key, spaceName: f.space_name, group: 'favorite'
    }));
    const starredIds = new Set(starred.map(s => s.id));
    const recents: Item[] = recent.value
        .filter(r => !starredIds.has(r.id))
        .map(r => ({ id: r.id, title: r.title, slug: r.slug, spaceKey: r.spaceKey, spaceName: r.spaceName, group: 'recent' }));
    return [...starred, ...recents];
});

let timer: ReturnType<typeof setTimeout> | undefined;
let requestSeq = 0;

const runSearch = async () => {
    const q = trimmedQuery.value;
    if (!q) {
        results.value = [];
        loading.value = false;
        failed.value = false;
        return;
    }

    const seq = ++requestSeq;
    loading.value = true;
    failed.value = false;
    try {
        const spaceId = scope.value === 'space' && props.spaceId ? props.spaceId : undefined;
        const response = await pageService.searchPages(q, spaceId, 15);
        if (seq !== requestSeq) return; // a newer search superseded this one
        results.value = response.results
            .filter(r => r.space_key)
            .map(r => ({
                id: r.page_id,
                title: r.title,
                slug: r.slug,
                spaceKey: r.space_key as string,
                spaceName: r.space_name,
                snippet: r.snippet,
                group: 'result'
            }));
        activeIndex.value = 0;
    } catch (err) {
        if (seq !== requestSeq) return;
        console.error('Search failed:', err);
        failed.value = true;
        results.value = [];
    } finally {
        if (seq === requestSeq) loading.value = false;
    }
};

watch([query, scope], () => {
    activeIndex.value = 0;
    if (timer) clearTimeout(timer);
    if (!trimmedQuery.value) {
        requestSeq++; // drop any in-flight request
        runSearch();
        return;
    }
    loading.value = true;
    timer = setTimeout(runSearch, 200);
});

const move = (delta: number) => {
    const count = items.value.length;
    if (!count) return;
    activeIndex.value = (activeIndex.value + delta + count) % count;
    nextTick(() => document.getElementById(`search-item-${activeIndex.value}`)?.scrollIntoView({ block: 'nearest' }));
};

const go = (item: Item) => {
    visible.value = false;
    router.push(`/${item.spaceKey}/p/${item.id}-${item.slug}`);
};

const openActive = () => {
    const item = items.value[activeIndex.value];
    if (item) go(item);
};

const onShow = () => {
    nextTick(() => inputRef.value?.focus());
};

watch(visible, (open) => {
    if (open) {
        query.value = '';
        results.value = [];
        failed.value = false;
        activeIndex.value = 0;
        if (!props.spaceId) scope.value = 'all';
        if (authStore.isAuthenticated) loadFavorites();
    }
});

// Ctrl/Cmd+K anywhere in the space view toggles the palette
const onKeydown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        visible.value = !visible.value;
    }
};

onMounted(() => window.addEventListener('keydown', onKeydown));
onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeydown);
    if (timer) clearTimeout(timer);
});

// Toolbar button asks the store to open us
watch(() => cms.searchRequest, () => { visible.value = true; });

defineExpose({ open: () => { visible.value = true; } });
</script>

<style scoped>
.search-input {
    background: transparent;
    border: none;
    outline: none;
    font-size: 1.05rem;
    color: inherit;
    min-width: 0;
}

.results {
    max-height: 22rem;
    overflow-y: auto;
}

.result-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.6rem 0.75rem;
    cursor: pointer;
}

.result-item.active {
    background: var(--p-highlight-background, var(--surface-100));
}

.scope-chip {
    padding: 0.1rem 0.6rem;
    border-radius: 999px;
    border: 1px solid var(--p-content-border-color, var(--surface-border));
    background: transparent;
    color: inherit;
    cursor: pointer;
}

.scope-chip.active {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, #fff);
}

kbd {
    font-family: inherit;
    font-size: 0.7rem;
    border: 1px solid var(--p-content-border-color, var(--surface-border));
    border-radius: 4px;
    padding: 0 0.3rem;
}
</style>
