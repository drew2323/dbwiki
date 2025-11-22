<template>
    <div class="tiptap-editor">
        <!-- Toolbar -->
        <EditorToolbar
            v-if="editor"
            :editor="editor"
            :can-publish="canPublish"
            :is-saving="isSaving"
            :last-saved="lastSaved"
            @publish="$emit('publish')"
        />

        <!-- Editor Content -->
        <EditorContent
            :editor="editor"
            class="tiptap-content"
        />

        <!-- Conflict Dialog -->
        <Dialog
            v-model:visible="showConflictDialog"
            modal
            header="Editing Conflict Detected"
            :style="{ width: '500px' }"
        >
            <div class="space-y-4">
                <p class="text-muted-color">
                    Someone else has edited this page while you were working.
                    You can either reload to see their changes (losing your edits),
                    or continue editing (which will overwrite their changes when you save).
                </p>

                <div class="flex gap-2 justify-end">
                    <Button
                        label="Continue Editing"
                        severity="secondary"
                        @click="handleContinueEditing"
                    />
                    <Button
                        label="Reload Page"
                        severity="danger"
                        @click="handleReload"
                    />
                </div>
            </div>
        </Dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import CodeBlock from '@tiptap/extension-code-block';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import EditorToolbar from './EditorToolbar.vue';

interface Props {
    modelValue: any;  // Tiptap JSON content
    etag: string | null;
    isSaving?: boolean;
    lastSaved?: Date | null;
    canPublish?: boolean;
    editable?: boolean;
}

interface Emits {
    (e: 'update:modelValue', value: any): void;
    (e: 'update:etag', value: string): void;
    (e: 'conflict', currentEtag: string): void;
    (e: 'publish'): void;
}

const props = withDefaults(defineProps<Props>(), {
    isSaving: false,
    lastSaved: null,
    canPublish: false,
    editable: true
});

const emit = defineEmits<Emits>();

// State
const showConflictDialog = ref(false);
const conflictEtag = ref<string | null>(null);

// Initialize Tiptap editor
const editor = useEditor({
    extensions: [
        StarterKit.configure({
            heading: {
                levels: [1, 2, 3, 4, 5, 6]
            }
        }),
        Link.configure({
            openOnClick: false,
            HTMLAttributes: {
                class: 'text-primary hover:underline'
            }
        }),
        Image.configure({
            HTMLAttributes: {
                class: 'max-w-full h-auto rounded'
            }
        }),
        Table.configure({
            resizable: true,
            HTMLAttributes: {
                class: 'border-collapse table-auto w-full'
            }
        }),
        TableRow,
        TableCell,
        TableHeader,
        CodeBlock.configure({
            HTMLAttributes: {
                class: 'bg-surface-100 dark:bg-surface-800 p-4 rounded font-mono text-sm'
            }
        })
    ],
    content: props.modelValue || {
        type: 'doc',
        content: [
            {
                type: 'paragraph'
            }
        ]
    },
    editable: props.editable,
    editorProps: {
        attributes: {
            class: 'prose dark:prose-invert max-w-none focus:outline-none min-h-[400px] p-4'
        }
    },
    onUpdate: ({ editor }) => {
        // Emit the JSON content
        emit('update:modelValue', editor.getJSON());
    }
});

// Watch for external content changes
watch(() => props.modelValue, (newValue) => {
    if (!editor.value) return;

    const currentContent = editor.value.getJSON();
    if (JSON.stringify(currentContent) !== JSON.stringify(newValue)) {
        editor.value.commands.setContent(newValue || {
            type: 'doc',
            content: [{ type: 'paragraph' }]
        });
    }
}, { deep: true });

// Watch for editable changes
watch(() => props.editable, (newValue) => {
    if (editor.value) {
        editor.value.setEditable(newValue);
    }
});

// Handle conflict
const handleConflict = (currentEtag: string) => {
    conflictEtag.value = currentEtag;
    showConflictDialog.value = true;
};

const handleContinueEditing = () => {
    // User chooses to overwrite - update our etag and continue
    if (conflictEtag.value) {
        emit('update:etag', conflictEtag.value);
    }
    showConflictDialog.value = false;
};

const handleReload = () => {
    // Reload the page to get fresh content
    window.location.reload();
};

// Expose conflict handler to parent
defineExpose({
    handleConflict
});

// Cleanup
onBeforeUnmount(() => {
    if (editor.value) {
        editor.value.destroy();
    }
});
</script>

<style scoped>
.tiptap-editor {
    @apply border border-surface-200 dark:border-surface-700 rounded-lg overflow-hidden bg-surface-0 dark:bg-surface-900;
}

.tiptap-content {
    @apply min-h-[400px];
}

/* Tiptap editor styles */
:deep(.ProseMirror) {
    @apply outline-none;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    @apply text-muted-color float-left h-0 pointer-events-none;
}

/* Table styles */
:deep(.ProseMirror table) {
    @apply border-collapse table-auto w-full my-4;
}

:deep(.ProseMirror td),
:deep(.ProseMirror th) {
    @apply border border-surface-300 dark:border-surface-700 px-3 py-2 text-left;
}

:deep(.ProseMirror th) {
    @apply bg-surface-100 dark:bg-surface-800 font-semibold;
}

/* Code block styles */
:deep(.ProseMirror pre) {
    @apply bg-surface-100 dark:bg-surface-800 p-4 rounded-lg font-mono text-sm overflow-x-auto my-4;
}

:deep(.ProseMirror code) {
    @apply bg-surface-100 dark:bg-surface-800 px-2 py-1 rounded font-mono text-sm;
}

:deep(.ProseMirror pre code) {
    @apply bg-transparent p-0;
}

/* Link styles */
:deep(.ProseMirror a) {
    @apply text-primary hover:underline cursor-pointer;
}

/* Image styles */
:deep(.ProseMirror img) {
    @apply max-w-full h-auto rounded my-4;
}

/* Heading styles */
:deep(.ProseMirror h1) {
    @apply text-4xl font-bold mt-8 mb-4;
}

:deep(.ProseMirror h2) {
    @apply text-3xl font-bold mt-6 mb-3;
}

:deep(.ProseMirror h3) {
    @apply text-2xl font-bold mt-5 mb-2;
}

:deep(.ProseMirror h4) {
    @apply text-xl font-semibold mt-4 mb-2;
}

:deep(.ProseMirror h5) {
    @apply text-lg font-semibold mt-3 mb-2;
}

:deep(.ProseMirror h6) {
    @apply text-base font-semibold mt-2 mb-1;
}

/* List styles */
:deep(.ProseMirror ul),
:deep(.ProseMirror ol) {
    @apply pl-6 my-4;
}

:deep(.ProseMirror ul) {
    @apply list-disc;
}

:deep(.ProseMirror ol) {
    @apply list-decimal;
}

:deep(.ProseMirror li) {
    @apply my-1;
}

/* Blockquote styles */
:deep(.ProseMirror blockquote) {
    @apply border-l-4 border-primary pl-4 italic my-4 text-muted-color;
}

/* Horizontal rule */
:deep(.ProseMirror hr) {
    @apply border-surface-300 dark:border-surface-700 my-8;
}
</style>
