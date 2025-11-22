<template>
    <Card class="page-attachments-card">
        <template #title>
            <div class="flex items-center gap-2">
                <i class="pi pi-paperclip text-primary"></i>
                <span class="text-base">Attachments</span>
            </div>
        </template>

        <template #content>
            <!-- Placeholder for future implementation -->
            <Message severity="info" :closable="false">
                <div class="flex flex-col items-center text-center py-4">
                    <i class="pi pi-cloud-upload text-5xl mb-3"></i>
                    <p class="font-medium mb-1">File Attachments</p>
                    <p class="text-sm text-color-secondary">
                        Coming soon: Upload and manage file attachments
                    </p>
                </div>
            </Message>
        </template>
    </Card>
</template>

<script setup lang="ts">
import Card from 'primevue/card';
import Message from 'primevue/message';

interface Props {
    pageId: string | null;
}

const props = defineProps<Props>();

// TODO: Implement file upload and attachment management
// - Upload files
// - Display attachment list
// - Download/delete attachments
// - Drag-drop upload
</script>
