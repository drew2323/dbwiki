<template>
    <Dialog
        v-model:visible="visible"
        modal
        header="Create New Page"
        :style="{ width: '500px' }"
        @hide="handleClose"
    >
        <div class="space-y-4">
            <div>
                <label for="page-title" class="block text-sm font-medium mb-2">
                    Page Title *
                </label>
                <InputText
                    id="page-title"
                    v-model="title"
                    placeholder="Enter page title"
                    class="w-full"
                    :invalid="showErrors && !title"
                    @keyup.enter="handleCreate"
                    autofocus
                />
                <small v-if="showErrors && !title" class="text-red-500">
                    Title is required
                </small>
            </div>

            <div>
                <label for="page-slug" class="block text-sm font-medium mb-2">
                    Slug (optional)
                </label>
                <InputText
                    id="page-slug"
                    v-model="slug"
                    placeholder="auto-generated-from-title"
                    class="w-full"
                />
                <small class="text-muted-color">
                    Leave empty to auto-generate from title
                </small>
            </div>

            <div v-if="showParentSelect">
                <label class="block text-sm font-medium mb-2">
                    Parent Page
                </label>
                <Select
                    v-model="selectedParentId"
                    :options="parentOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select parent page (or root)"
                    class="w-full"
                    showClear
                />
                <small class="text-muted-color">
                    Choose where to place the new page in the tree
                </small>
            </div>

            <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                <div class="flex items-center gap-2 text-red-700 dark:text-red-400">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span class="text-sm">{{ error }}</span>
                </div>
            </div>
        </div>

        <template #footer>
            <Button
                label="Cancel"
                severity="secondary"
                outlined
                @click="handleClose"
            />
            <Button
                label="Create Page"
                icon="pi pi-check"
                :loading="isCreating"
                @click="handleCreate"
            />
        </template>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { pageService, type TreeNode } from '@/services/pageService';
import { useToast } from 'primevue/usetoast';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import Button from 'primevue/button';

interface Props {
    spaceId: string;
    spaceKey: string;
    defaultParentId?: string | null;
    showParentSelect?: boolean;
    treeNodes?: TreeNode[];
}

const props = withDefaults(defineProps<Props>(), {
    defaultParentId: null,
    showParentSelect: true,
    treeNodes: () => []
});

interface Emits {
    (e: 'created', page: any): void;
    (e: 'close'): void;
}

const emit = defineEmits<Emits>();

const router = useRouter();
const toast = useToast();

// State
const visible = defineModel<boolean>('visible', { required: true });
const title = ref('');
const slug = ref('');
const selectedParentId = ref<string | null>(props.defaultParentId);
const isCreating = ref(false);
const error = ref('');
const showErrors = ref(false);

// Build parent options from tree nodes
const parentOptions = computed(() => {
    const options = [
        { label: '(Root Level)', value: null }
    ];

    // Flatten tree nodes for dropdown
    const buildOptions = (nodes: TreeNode[], level: number = 0) => {
        for (const node of nodes) {
            if (node.page_id) {
                const indent = '  '.repeat(level);
                options.push({
                    label: `${indent}${node.title || 'Untitled'}`,
                    value: node.id
                });
            }
        }
    };

    buildOptions(props.treeNodes);
    return options;
});

// Watch for defaultParentId changes
watch(() => props.defaultParentId, (newVal) => {
    selectedParentId.value = newVal;
});

// Handlers
const handleCreate = async () => {
    showErrors.value = true;

    if (!title.value.trim()) {
        return;
    }

    isCreating.value = true;
    error.value = '';

    try {
        // Create the page
        const page = await pageService.createPage(
            props.spaceId,
            title.value.trim(),
            selectedParentId.value || undefined,
            slug.value.trim() || undefined
        );

        toast.add({
            severity: 'success',
            summary: 'Page Created',
            detail: `"${page.title}" has been created`,
            life: 3000
        });

        emit('created', page);
        handleClose();

        // Navigate to the new page
        router.push(`/${props.spaceKey}/p/${page.id}-${page.slug}`);
    } catch (err: any) {
        console.error('Failed to create page:', err);
        error.value = err.response?.data?.detail || 'Failed to create page. Please try again.';

        toast.add({
            severity: 'error',
            summary: 'Creation Failed',
            detail: error.value,
            life: 5000
        });
    } finally {
        isCreating.value = false;
    }
};

const handleClose = () => {
    // Reset form
    title.value = '';
    slug.value = '';
    selectedParentId.value = props.defaultParentId;
    error.value = '';
    showErrors.value = false;

    emit('close');
    visible.value = false;
};
</script>

<style scoped>
:deep(.p-dropdown) {
    max-width: 100%;
}
</style>
