<template>
    <Dialog
        v-model:visible="visible"
        modal
        header="Compare versions"
        :style="{ width: '70rem', maxWidth: '95vw' }"
        data-testid="version-diff"
    >
        <div class="flex flex-wrap items-end gap-4 mb-4">
            <div class="flex-1 min-w-48">
                <label class="block text-sm text-muted-color mb-1" for="diff-from">From (older)</label>
                <Select
                    inputId="diff-from"
                    v-model="fromId"
                    :options="options"
                    optionLabel="label"
                    optionValue="value"
                    class="w-full"
                    data-testid="diff-from"
                />
            </div>
            <i class="pi pi-arrow-right text-muted-color pb-3"></i>
            <div class="flex-1 min-w-48">
                <label class="block text-sm text-muted-color mb-1" for="diff-to">To (newer)</label>
                <Select
                    inputId="diff-to"
                    v-model="toId"
                    :options="options"
                    optionLabel="label"
                    optionValue="value"
                    class="w-full"
                    data-testid="diff-to"
                />
            </div>
        </div>

        <div v-if="loading" class="space-y-2">
            <Skeleton v-for="n in 5" :key="n" height="1.5rem" />
        </div>

        <Message v-else-if="error" severity="error" :closable="false">{{ error }}</Message>

        <template v-else-if="fromVersion && toVersion">
            <div class="flex flex-wrap items-center gap-3 mb-3 text-sm">
                <span class="diff-pill del" data-testid="diff-removed">−{{ stats.removed }}</span>
                <span class="diff-pill add" data-testid="diff-added">+{{ stats.added }}</span>
                <span class="text-muted-color">
                    v{{ fromVersion.version_number }} by {{ fromVersion.author_name || 'unknown' }}, {{ formatDate(fromVersion.created_at) }}
                    →
                    v{{ toVersion.version_number }} by {{ toVersion.author_name || 'unknown' }}, {{ formatDate(toVersion.created_at) }}
                </span>
                <label class="ml-auto flex items-center gap-2 cursor-pointer">
                    <ToggleSwitch v-model="changesOnly" inputId="diff-changes-only" />
                    <span>Changes only</span>
                </label>
            </div>

            <div v-if="fromVersion.title !== toVersion.title" class="title-change mb-3" data-testid="diff-title-change">
                <span class="diff-line del">Title: {{ fromVersion.title }}</span>
                <span class="diff-line add">Title: {{ toVersion.title }}</span>
            </div>

            <div v-if="!stats.changed && fromVersion.title === toVersion.title" class="text-center py-8 text-muted-color" data-testid="diff-no-changes">
                <i class="pi pi-check-circle text-3xl mb-2"></i>
                <p>These versions have identical content.</p>
            </div>

            <div v-else class="diff-view" role="table" aria-label="Differences">
                <template v-for="(row, i) in visibleRows" :key="i">
                    <div v-if="row.kind === 'gap'" class="diff-gap">⋯</div>
                    <div v-else-if="row.kind === 'equal'" class="diff-line equal">{{ row.text }}</div>
                    <div v-else-if="row.kind === 'add'" class="diff-line add" data-testid="diff-add-line">{{ row.text }}</div>
                    <div v-else-if="row.kind === 'del'" class="diff-line del" data-testid="diff-del-line">{{ row.text }}</div>
                    <template v-else>
                        <div class="diff-line del" data-testid="diff-del-line">
                            <template v-for="(part, k) in row.parts" :key="`d${k}`">
                                <span v-if="part.type === 'del'" class="word del">{{ part.text }}</span>
                                <span v-else-if="part.type === 'equal'">{{ part.text }}</span>
                            </template>
                        </div>
                        <div class="diff-line add" data-testid="diff-add-line">
                            <template v-for="(part, k) in row.parts" :key="`a${k}`">
                                <span v-if="part.type === 'add'" class="word add">{{ part.text }}</span>
                                <span v-else-if="part.type === 'equal'">{{ part.text }}</span>
                            </template>
                        </div>
                    </template>
                </template>
            </div>
        </template>

        <template #footer>
            <Button label="Close" severity="secondary" @click="visible = false" />
        </template>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Select from 'primevue/select';
import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';
import Message from 'primevue/message';
import ToggleSwitch from 'primevue/toggleswitch';
import { pageService, type PageVersion } from '@/services/pageService';
import { buildDiffRows, summarizeRows, type DiffRow } from '@/utils/diffTiptap';

const props = defineProps<{
    pageId: string | null;
    /** Version list (newest first) as returned by the history endpoint */
    versions: PageVersion[];
    /** Pre-selected pair when the dialog opens */
    initialFromId?: string | null;
    initialToId?: string | null;
}>();

const visible = defineModel<boolean>('visible', { required: true });

const fromId = ref<string | null>(null);
const toId = ref<string | null>(null);
const loading = ref(false);
const error = ref('');
const changesOnly = ref(false);
const fromVersion = ref<PageVersion | null>(null);
const toVersion = ref<PageVersion | null>(null);

const cache = new Map<string, PageVersion>();

const formatDate = (iso: string) => new Date(iso).toLocaleString();

const options = computed(() =>
    props.versions.map((v) => ({
        value: v.id,
        label: `v${v.version_number} · ${v.author_name || 'unknown'} · ${new Date(v.created_at).toLocaleDateString()}`
    }))
);

const loadVersion = async (id: string): Promise<PageVersion> => {
    const hit = cache.get(id);
    if (hit) return hit;
    const full = await pageService.getVersion(props.pageId as string, id);
    cache.set(id, full);
    return full;
};

const rows = computed<DiffRow[]>(() =>
    fromVersion.value && toVersion.value ? buildDiffRows(fromVersion.value.content_json, toVersion.value.content_json) : []
);
const stats = computed(() => summarizeRows(rows.value));

// With "changes only", keep two lines of context around every change
const CONTEXT = 2;
type ViewRow = DiffRow | { kind: 'gap' };
const visibleRows = computed<ViewRow[]>(() => {
    if (!changesOnly.value) return rows.value;
    const keep = rows.value.map(() => false);
    rows.value.forEach((r, i) => {
        if (r.kind !== 'equal') {
            for (let k = Math.max(0, i - CONTEXT); k <= Math.min(rows.value.length - 1, i + CONTEXT); k++) keep[k] = true;
        }
    });
    const out: ViewRow[] = [];
    rows.value.forEach((r, i) => {
        if (keep[i]) out.push(r);
        else if (out.length && out[out.length - 1].kind !== 'gap') out.push({ kind: 'gap' });
    });
    return out;
});

const refresh = async () => {
    if (!visible.value || !fromId.value || !toId.value || !props.pageId) return;
    loading.value = true;
    error.value = '';
    try {
        const [a, b] = await Promise.all([loadVersion(fromId.value), loadVersion(toId.value)]);
        fromVersion.value = a;
        toVersion.value = b;
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Failed to load versions';
    } finally {
        loading.value = false;
    }
};

// Pick sensible defaults whenever the dialog opens: previous version -> selected/newest
watch(visible, (open) => {
    if (!open) return;
    const list = props.versions;
    const to = props.initialToId || list[0]?.id || null;
    const toIdx = list.findIndex((v) => v.id === to);
    fromId.value = props.initialFromId || list[toIdx + 1]?.id || list[Math.min(1, list.length - 1)]?.id || null;
    toId.value = to;
    changesOnly.value = false;
    refresh();
});

watch([fromId, toId], refresh);
watch(() => props.pageId, () => { cache.clear(); fromVersion.value = null; toVersion.value = null; });
</script>

<style scoped>
.diff-view {
    border: 1px solid var(--p-content-border-color, var(--surface-border));
    border-radius: 6px;
    max-height: 55vh;
    overflow: auto;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.85rem;
}

.diff-line {
    padding: 0.15rem 0.75rem 0.15rem 1.75rem;
    white-space: pre-wrap;
    word-break: break-word;
    position: relative;
    min-height: 1.4em;
}

.diff-line.add { background: rgba(34, 197, 94, 0.14); }
.diff-line.del { background: rgba(239, 68, 68, 0.14); }
.diff-line.add::before { content: '+'; position: absolute; left: 0.6rem; color: #16a34a; }
.diff-line.del::before { content: '−'; position: absolute; left: 0.6rem; color: #dc2626; }

.word.add { background: rgba(34, 197, 94, 0.4); border-radius: 3px; }
.word.del { background: rgba(239, 68, 68, 0.4); border-radius: 3px; text-decoration: line-through; }

.diff-gap {
    text-align: center;
    color: var(--p-text-muted-color, #888);
    background: var(--p-surface-100, var(--surface-100));
    font-size: 0.75rem;
}

.diff-pill {
    padding: 0.05rem 0.6rem;
    border-radius: 999px;
    font-weight: 600;
}
.diff-pill.add { background: rgba(34, 197, 94, 0.18); color: #15803d; }
.diff-pill.del { background: rgba(239, 68, 68, 0.18); color: #b91c1c; }

.title-change { border: 1px solid var(--p-content-border-color, var(--surface-border)); border-radius: 6px; overflow: hidden; }
</style>
