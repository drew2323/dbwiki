<template>
    <Card class="page-attachments-card">
        <template #title>
            <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <i class="pi pi-paperclip text-primary"></i>
                    <span class="text-base">Attachments</span>
                    <Tag v-if="attachments.length" :value="String(attachments.length)" severity="secondary" rounded />
                </div>
                <Button
                    v-if="canEdit"
                    icon="pi pi-upload"
                    label="Upload"
                    size="small"
                    text
                    data-testid="attachment-upload-button"
                    @click="fileInput?.click()"
                />
            </div>
        </template>

        <template #content>
            <input
                ref="fileInput"
                type="file"
                multiple
                class="hidden"
                data-testid="attachment-file-input"
                @change="onFilesPicked"
            />

            <!-- Drop zone (editors only) -->
            <div
                v-if="canEdit"
                class="dropzone mb-3"
                :class="{ dragging }"
                data-testid="attachment-dropzone"
                @dragenter.prevent="dragging = true"
                @dragover.prevent="dragging = true"
                @dragleave.prevent="onDragLeave"
                @drop.prevent="onDrop"
            >
                <i class="pi pi-cloud-upload text-2xl mb-1"></i>
                <span class="text-sm">Drop files here or use Upload</span>
                <span class="text-xs text-muted-color">Max {{ MAX_MB }} MB per file</span>
            </div>

            <!-- Uploads in progress / failed -->
            <div v-for="u in uploads" :key="u.key" class="upload-row mb-2" data-testid="attachment-upload-row">
                <div class="flex items-center justify-between gap-2 text-sm">
                    <span class="truncate">{{ u.name }}</span>
                    <span v-if="u.error" class="text-red-500 flex items-center gap-1">
                        <i class="pi pi-exclamation-circle"></i>
                        <Button icon="pi pi-times" text rounded size="small" severity="secondary" aria-label="Dismiss" @click="dismissUpload(u.key)" />
                    </span>
                    <span v-else class="text-muted-color">{{ u.percent }}%</span>
                </div>
                <ProgressBar v-if="!u.error" :value="u.percent" :showValue="false" style="height: 4px" />
                <small v-else class="text-red-500">{{ u.error }}</small>
            </div>

            <!-- Loading -->
            <div v-if="loading" class="space-y-2">
                <Skeleton v-for="n in 2" :key="n" height="2.5rem" />
            </div>

            <!-- List -->
            <ul v-else-if="attachments.length" class="attachment-list" data-testid="attachment-list">
                <li v-for="a in attachments" :key="a.id" class="attachment-item" data-testid="attachment-item">
                    <a :href="fileUrl(a.id)" target="_blank" rel="noopener" class="thumb" :title="`Open ${a.filename}`">
                        <img v-if="isImage(a)" :src="fileUrl(a.id)" :alt="a.filename" loading="lazy" />
                        <i v-else :class="iconFor(a)" class="text-xl text-muted-color"></i>
                    </a>
                    <div class="min-w-0 flex-1">
                        <a :href="fileUrl(a.id)" target="_blank" rel="noopener" class="block truncate font-medium text-sm hover:underline">
                            {{ a.filename }}
                        </a>
                        <span class="text-xs text-muted-color">{{ formatBytes(a.size_bytes) }}</span>
                    </div>
                    <div class="flex items-center">
                        <Button
                            v-if="canInsert && isImage(a)"
                            icon="pi pi-image"
                            text
                            rounded
                            size="small"
                            severity="secondary"
                            aria-label="Insert into page"
                            v-tooltip.left="'Insert into page'"
                            data-testid="attachment-insert"
                            @click="emit('insert-image', fileUrl(a.id), a.filename)"
                        />
                        <Button
                            v-if="canEdit"
                            icon="pi pi-trash"
                            text
                            rounded
                            size="small"
                            severity="danger"
                            aria-label="Delete attachment"
                            data-testid="attachment-delete"
                            @click="confirmDelete(a)"
                        />
                    </div>
                </li>
            </ul>

            <p v-else-if="!loading && !canEdit" class="text-sm text-muted-color text-center py-2">
                No attachments
            </p>
            <p v-else-if="!loading && !uploads.length" class="text-sm text-muted-color text-center">
                No attachments yet
            </p>

            <p v-if="loadError" class="text-sm text-red-500 mt-2">{{ loadError }}</p>
        </template>
    </Card>

    <Dialog v-model:visible="showDeleteDialog" modal header="Delete attachment" :style="{ width: '400px' }">
        <p>Delete <strong>{{ toDelete?.filename }}</strong>? Images already inserted into pages will stop displaying.</p>
        <template #footer>
            <Button label="Cancel" severity="secondary" outlined @click="showDeleteDialog = false" />
            <Button label="Delete" icon="pi pi-trash" severity="danger" :loading="deleting" data-testid="attachment-delete-confirm" @click="doDelete" />
        </template>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import Card from 'primevue/card';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import ProgressBar from 'primevue/progressbar';
import Skeleton from 'primevue/skeleton';
import Dialog from 'primevue/dialog';
import { attachmentService, formatBytes, type Attachment } from '@/services/attachmentService';

interface Props {
    pageId: string | null;
    spaceId?: string | null;
    /** May upload and delete */
    canEdit?: boolean;
    /** Show "insert into page" on images (editor is open) */
    canInsert?: boolean;
}

const props = withDefaults(defineProps<Props>(), { spaceId: null, canEdit: false, canInsert: false });
const emit = defineEmits<{ (e: 'insert-image', src: string, alt: string): void }>();

const toast = useToast();
const MAX_MB = 25;

interface Upload { key: number; name: string; percent: number; error: string | null }

const attachments = ref<Attachment[]>([]);
const loading = ref(false);
const loadError = ref('');
const uploads = ref<Upload[]>([]);
const dragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const showDeleteDialog = ref(false);
const toDelete = ref<Attachment | null>(null);
const deleting = ref(false);
let uploadSeq = 0;

const fileUrl = attachmentService.fileUrl;
const isImage = attachmentService.isImage;

const iconFor = (a: Attachment) => {
    if (a.mime_type === 'application/pdf') return 'pi pi-file-pdf';
    if (a.mime_type.startsWith('text/')) return 'pi pi-file-edit';
    if (a.mime_type.includes('zip') || a.mime_type.includes('compressed')) return 'pi pi-box';
    return 'pi pi-file';
};

const load = async () => {
    if (!props.pageId) {
        attachments.value = [];
        return;
    }
    loading.value = true;
    loadError.value = '';
    try {
        attachments.value = await attachmentService.listForPage(props.pageId);
    } catch (err) {
        console.error('Failed to load attachments:', err);
        loadError.value = 'Failed to load attachments';
    } finally {
        loading.value = false;
    }
};

const dismissUpload = (key: number) => {
    uploads.value = uploads.value.filter(u => u.key !== key);
};

const uploadFiles = async (files: File[]) => {
    if (!props.canEdit || !props.spaceId || !props.pageId) return;

    for (const file of files) {
        const entry: Upload = { key: ++uploadSeq, name: file.name, percent: 0, error: null };
        uploads.value.push(entry);
        const row = uploads.value[uploads.value.length - 1]; // reactive proxy

        if (file.size > MAX_MB * 1024 * 1024) {
            row.error = `Too large (max ${MAX_MB} MB)`;
            continue;
        }
        if (file.size === 0) {
            row.error = 'File is empty';
            continue;
        }

        try {
            const created = await attachmentService.upload(props.spaceId, props.pageId, file, (p) => { row.percent = p; });
            attachments.value = [created, ...attachments.value.filter(a => a.id !== created.id)];
            dismissUpload(entry.key);
        } catch (err: any) {
            console.error('Upload failed:', err);
            row.error = err.response?.data?.detail || 'Upload failed';
        }
    }
};

const onFilesPicked = (e: Event) => {
    const input = e.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    input.value = ''; // allow picking the same file again
    uploadFiles(files);
};

const onDrop = (e: DragEvent) => {
    dragging.value = false;
    uploadFiles(Array.from(e.dataTransfer?.files || []));
};

const onDragLeave = (e: DragEvent) => {
    // ignore leave events fired when moving over child elements
    if (!(e.currentTarget as HTMLElement).contains(e.relatedTarget as Node)) dragging.value = false;
};

const confirmDelete = (a: Attachment) => {
    toDelete.value = a;
    showDeleteDialog.value = true;
};

const doDelete = async () => {
    if (!toDelete.value) return;
    deleting.value = true;
    try {
        await attachmentService.remove(toDelete.value.id);
        attachments.value = attachments.value.filter(a => a.id !== toDelete.value!.id);
        showDeleteDialog.value = false;
        toast.add({ severity: 'success', summary: 'Attachment deleted', life: 2000 });
    } catch (err: any) {
        toast.add({ severity: 'error', summary: 'Delete failed', detail: err.response?.data?.detail || 'Could not delete attachment', life: 5000 });
    } finally {
        deleting.value = false;
    }
};

watch(() => props.pageId, () => { uploads.value = []; load(); });
onMounted(load);
</script>

<style scoped>
.dropzone {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.15rem;
    padding: 0.9rem;
    border: 2px dashed var(--p-content-border-color, var(--surface-border));
    border-radius: 8px;
    color: var(--p-text-muted-color, inherit);
    transition: border-color 0.15s, background 0.15s;
}

.dropzone.dragging {
    border-color: var(--p-primary-color);
    background: var(--p-highlight-background, var(--surface-100));
}

.attachment-list {
    list-style: none;
    margin: 0;
    padding: 0;
}

.attachment-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.4rem 0;
}

.attachment-item + .attachment-item {
    border-top: 1px solid var(--p-content-border-color, var(--surface-border));
}

.thumb {
    flex: none;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    overflow: hidden;
    background: var(--p-surface-100, var(--surface-100));
}

.thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
</style>
