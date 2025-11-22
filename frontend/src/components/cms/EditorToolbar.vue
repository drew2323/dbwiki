<template>
    <Toolbar class="editor-toolbar border-b border-surface">
        <template #start>
            <div class="flex items-center gap-2 flex-wrap">
                <!-- Text formatting -->
                <ButtonGroup>
                    <Button
                        icon="pi pi-bold"
                        text
                        size="small"
                        :severity="editor.isActive('bold') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleBold().run()"
                        v-tooltip.bottom="'Bold (Cmd+B)'"
                    />
                    <Button
                        icon="pi pi-italic"
                        text
                        size="small"
                        :severity="editor.isActive('italic') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleItalic().run()"
                        v-tooltip.bottom="'Italic (Cmd+I)'"
                    />
                    <Button
                        icon="pi pi-strikethrough"
                        text
                        size="small"
                        :severity="editor.isActive('strike') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleStrike().run()"
                        v-tooltip.bottom="'Strikethrough'"
                    />
                    <Button
                        icon="pi pi-code"
                        text
                        size="small"
                        :severity="editor.isActive('code') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleCode().run()"
                        v-tooltip.bottom="'Inline Code'"
                    />
                </ButtonGroup>

                <Divider layout="vertical" class="hidden md:block" />

                <!-- Headings -->
                <ButtonGroup class="hidden sm:flex">
                    <Button
                        label="H1"
                        text
                        size="small"
                        :severity="editor.isActive('heading', { level: 1 }) ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
                        v-tooltip.bottom="'Heading 1'"
                    />
                    <Button
                        label="H2"
                        text
                        size="small"
                        :severity="editor.isActive('heading', { level: 2 }) ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
                        v-tooltip.bottom="'Heading 2'"
                    />
                    <Button
                        label="H3"
                        text
                        size="small"
                        :severity="editor.isActive('heading', { level: 3 }) ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
                        v-tooltip.bottom="'Heading 3'"
                    />
                </ButtonGroup>

                <Divider layout="vertical" class="hidden md:block" />

                <!-- Lists -->
                <ButtonGroup>
                    <Button
                        icon="pi pi-list"
                        text
                        size="small"
                        :severity="editor.isActive('bulletList') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleBulletList().run()"
                        v-tooltip.bottom="'Bullet List'"
                    />
                    <Button
                        icon="pi pi-sort-numeric-down"
                        text
                        size="small"
                        :severity="editor.isActive('orderedList') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleOrderedList().run()"
                        v-tooltip.bottom="'Numbered List'"
                    />
                </ButtonGroup>

                <Divider layout="vertical" class="hidden md:block" />

                <!-- Blocks -->
                <ButtonGroup class="hidden lg:flex">
                    <Button
                        icon="pi pi-quote-right"
                        text
                        size="small"
                        :severity="editor.isActive('blockquote') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleBlockquote().run()"
                        v-tooltip.bottom="'Blockquote'"
                    />
                    <Button
                        icon="pi pi-bookmark"
                        text
                        size="small"
                        :severity="editor.isActive('codeBlock') ? 'primary' : 'secondary'"
                        @click="editor.chain().focus().toggleCodeBlock().run()"
                        v-tooltip.bottom="'Code Block'"
                    />
                    <Button
                        icon="pi pi-minus"
                        text
                        size="small"
                        severity="secondary"
                        @click="editor.chain().focus().setHorizontalRule().run()"
                        v-tooltip.bottom="'Horizontal Rule'"
                    />
                </ButtonGroup>

                <Divider layout="vertical" class="hidden lg:block" />

                <!-- Link & Image -->
                <ButtonGroup class="hidden md:flex">
                    <Button
                        icon="pi pi-link"
                        text
                        size="small"
                        :severity="editor.isActive('link') ? 'primary' : 'secondary'"
                        @click="toggleLink"
                        v-tooltip.bottom="'Insert Link'"
                    />
                    <Button
                        icon="pi pi-image"
                        text
                        size="small"
                        severity="secondary"
                        @click="addImage"
                        v-tooltip.bottom="'Insert Image'"
                    />
                    <Button
                        icon="pi pi-table"
                        text
                        size="small"
                        :severity="editor.isActive('table') ? 'primary' : 'secondary'"
                        @click="insertTable"
                        v-tooltip.bottom="'Insert Table'"
                    />
                </ButtonGroup>

                <Divider layout="vertical" class="hidden xl:block" />

                <!-- Undo/Redo -->
                <ButtonGroup class="hidden xl:flex">
                    <Button
                        icon="pi pi-undo"
                        text
                        size="small"
                        severity="secondary"
                        :disabled="!editor.can().undo()"
                        @click="editor.chain().focus().undo().run()"
                        v-tooltip.bottom="'Undo (Cmd+Z)'"
                    />
                    <Button
                        icon="pi pi-replay"
                        text
                        size="small"
                        severity="secondary"
                        :disabled="!editor.can().redo()"
                        @click="editor.chain().focus().redo().run()"
                        v-tooltip.bottom="'Redo (Cmd+Shift+Z)'"
                    />
                </ButtonGroup>
            </div>
        </template>

        <template #end>
            <div class="flex items-center gap-3">
                <!-- Save status -->
                <Tag
                    :icon="isSaving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"
                    :value="saveStatusText"
                    :severity="saveStatusSeverity"
                />

                <!-- Publish button -->
                <Button
                    v-if="canPublish"
                    label="Publish"
                    icon="pi pi-upload"
                    severity="success"
                    size="small"
                    @click="$emit('publish')"
                />
            </div>
        </template>
    </Toolbar>

    <!-- Link Dialog -->
    <Dialog
        v-model:visible="showLinkDialog"
        modal
        header="Insert Link"
        :style="{ width: '400px' }"
    >
        <div class="space-y-4">
            <FloatLabel>
                <InputText
                    id="link-url"
                    v-model="linkUrl"
                    class="w-full"
                    @keyup.enter="setLink"
                    autofocus
                />
                <label for="link-url">URL</label>
            </FloatLabel>
        </div>

        <template #footer>
            <Button
                label="Cancel"
                severity="secondary"
                outlined
                @click="showLinkDialog = false"
            />
            <Button
                label="Insert"
                icon="pi pi-link"
                @click="setLink"
            />
        </template>
    </Dialog>

    <!-- Image Dialog -->
    <Dialog
        v-model:visible="showImageDialog"
        modal
        header="Insert Image"
        :style="{ width: '400px' }"
    >
        <div class="space-y-4">
            <FloatLabel>
                <InputText
                    id="image-url"
                    v-model="imageUrl"
                    class="w-full"
                    @keyup.enter="setImage"
                    autofocus
                />
                <label for="image-url">Image URL</label>
            </FloatLabel>

            <Message severity="info" :closable="false">
                You can also drag and drop images directly into the editor
            </Message>
        </div>

        <template #footer>
            <Button
                label="Cancel"
                severity="secondary"
                outlined
                @click="showImageDialog = false"
            />
            <Button
                label="Insert"
                icon="pi pi-image"
                @click="setImage"
            />
        </template>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Editor } from '@tiptap/vue-3';
import Button from 'primevue/button';
import ButtonGroup from 'primevue/buttongroup';
import Toolbar from 'primevue/toolbar';
import Divider from 'primevue/divider';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import FloatLabel from 'primevue/floatlabel';
import Tag from 'primevue/tag';
import Message from 'primevue/message';

interface Props {
    editor: Editor;
    isSaving?: boolean;
    lastSaved?: Date | null;
    canPublish?: boolean;
}

interface Emits {
    (e: 'publish'): void;
}

const props = withDefaults(defineProps<Props>(), {
    isSaving: false,
    lastSaved: null,
    canPublish: false
});

defineEmits<Emits>();

// Save status
const saveStatusText = computed(() => {
    if (props.isSaving) return 'Saving...';
    if (props.lastSaved) return `Saved ${formatLastSaved(props.lastSaved)}`;
    return 'Not saved';
});

const saveStatusSeverity = computed(() => {
    if (props.isSaving) return 'info';
    if (props.lastSaved) return 'success';
    return 'secondary';
});

// Link dialog
const showLinkDialog = ref(false);
const linkUrl = ref('');

const toggleLink = () => {
    if (props.editor.isActive('link')) {
        props.editor.chain().focus().unsetLink().run();
    } else {
        const previousUrl = props.editor.getAttributes('link').href;
        linkUrl.value = previousUrl || '';
        showLinkDialog.value = true;
    }
};

const setLink = () => {
    if (linkUrl.value) {
        props.editor
            .chain()
            .focus()
            .extendMarkRange('link')
            .setLink({ href: linkUrl.value })
            .run();
    }
    showLinkDialog.value = false;
    linkUrl.value = '';
};

// Image dialog
const showImageDialog = ref(false);
const imageUrl = ref('');

const addImage = () => {
    showImageDialog.value = true;
};

const setImage = () => {
    if (imageUrl.value) {
        props.editor.chain().focus().setImage({ src: imageUrl.value }).run();
    }
    showImageDialog.value = false;
    imageUrl.value = '';
};

// Table
const insertTable = () => {
    props.editor
        .chain()
        .focus()
        .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
        .run();
};

// Format last saved time
const formatLastSaved = (date: Date): string => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);

    if (seconds < 10) return 'just now';
    if (seconds < 60) return `${seconds}s ago`;

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;

    return date.toLocaleDateString();
};
</script>

<style scoped>
.editor-toolbar :deep(.p-toolbar) {
    background: var(--surface-50);
    border: none;
}

.dark .editor-toolbar :deep(.p-toolbar) {
    background: var(--surface-800);
}
</style>
