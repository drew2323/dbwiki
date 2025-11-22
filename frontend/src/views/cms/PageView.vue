<template>
    <div class="page-view">
        <!-- Loading State -->
        <Card v-if="loading">
            <template #content>
                <div class="space-y-4">
                    <Skeleton height="3rem" width="70%"></Skeleton>
                    <Skeleton height="1rem"></Skeleton>
                    <Skeleton height="1rem"></Skeleton>
                    <Skeleton height="1rem" width="80%"></Skeleton>
                    <Skeleton height="15rem" class="mt-4"></Skeleton>
                </div>
            </template>
        </Card>

        <!-- Error State -->
        <Message v-else-if="error" severity="error" class="mb-4">
            <div class="flex flex-col items-center text-center py-8">
                <i class="pi pi-exclamation-triangle text-6xl mb-4"></i>
                <h2 class="text-2xl font-semibold mb-2">Page Not Found</h2>
                <p class="mb-4">{{ error }}</p>
                <Button
                    label="Back to Space"
                    icon="pi pi-arrow-left"
                    severity="secondary"
                    @click="$router.push(`/${$route.params.spaceKey}`)"
                />
            </div>
        </Message>

        <!-- Page Content -->
        <div v-else-if="page">
            <!-- View Mode -->
            <Card v-if="!isEditing" class="page-card">
                <template #header>
                    <!-- Breadcrumb -->
                    <div v-if="breadcrumb.length > 0" class="px-6 pt-6">
                        <Breadcrumb :model="breadcrumbItems" />
                    </div>
                </template>

                <template #title>
                    <div class="flex items-start justify-between gap-4">
                        <h1 class="text-3xl md:text-4xl font-bold">{{ page.title }}</h1>
                        <Tag v-if="page.is_archived" icon="pi pi-eye-slash" value="Archived" severity="warn" />
                    </div>
                </template>

                <template #subtitle>
                    <div class="flex flex-wrap items-center gap-2 mt-2">
                        <Tag icon="pi pi-clock" :value="`Updated ${formatDate(page.updated_at)}`" severity="secondary" />
                        <Tag v-if="latestVersion" icon="pi pi-bookmark" :value="`Version ${latestVersion.version_number}`" severity="info" />
                    </div>
                </template>

                <template #content>
                    <!-- Page Content (Read-only) -->
                    <div :key="pageId" class="page-content prose dark:prose-invert max-w-none min-h-[200px]">
                        <!-- If we have published version with content, show it -->
                        <template v-if="latestVersion?.content_json">
                            <div v-html="renderContent(latestVersion.content_json)" class="rendered-content" :key="`version-${latestVersion.id}`"></div>
                        </template>

                        <!-- Otherwise show draft (for editors) -->
                        <template v-else-if="page?.draft_json">
                            <div v-html="renderContent(page.draft_json)" class="rendered-content" :key="`draft-${page.id}`"></div>
                        </template>

                        <!-- Empty state -->
                        <template v-else>
                            <div class="flex flex-col items-center text-center py-12">
                                <i class="pi pi-file text-6xl text-color-secondary mb-4"></i>
                                <p class="text-color-secondary mb-4">This page is empty</p>
                                <Button
                                    v-if="canEdit"
                                    label="Start Editing"
                                    icon="pi pi-pencil"
                                    @click="startEditing"
                                />
                            </div>
                        </template>
                    </div>
                </template>

                <template #footer>
                    <!-- Actions -->
                    <Toolbar v-if="canEdit" class="border-none p-0">
                        <template #start>
                            <div class="flex gap-2">
                                <Button
                                    label="Edit Page"
                                    icon="pi pi-pencil"
                                    @click="startEditing"
                                />
                                <Button
                                    label="View History"
                                    icon="pi pi-history"
                                    severity="secondary"
                                    outlined
                                    @click="showHistory = true"
                                />
                            </div>
                        </template>
                    </Toolbar>
                </template>
            </Card>

            <!-- Edit Mode -->
            <Card v-else class="editor-card">
                <template #title>
                    <div class="pt-2">
                        <FloatLabel>
                            <InputText
                                id="page-title"
                                v-model="editTitle"
                                class="w-full text-3xl md:text-4xl font-bold"
                            />
                            <label for="page-title">Page Title</label>
                        </FloatLabel>
                    </div>
                </template>

                <template #content>
                    <!-- Tiptap Editor -->
                    <TiptapEditor
                        ref="editorRef"
                        v-model="draftContent"
                        v-model:etag="currentEtag"
                        :is-saving="isSaving"
                        :last-saved="lastSaved"
                        :can-publish="hasUnsavedChanges || !latestVersion"
                        @publish="handlePublish"
                    />
                </template>

                <template #footer>
                    <Toolbar class="border-none p-0">
                        <template #start>
                            <Button
                                label="Cancel"
                                icon="pi pi-times"
                                severity="secondary"
                                outlined
                                @click="cancelEditing"
                            />
                        </template>
                        <template #end>
                            <Button
                                label="View History"
                                icon="pi pi-history"
                                severity="secondary"
                                outlined
                                @click="showHistory = true"
                            />
                        </template>
                    </Toolbar>
                </template>
            </Card>
        </div>

        <!-- Version History Dialog -->
        <Dialog
            v-model:visible="showHistory"
            header="Page History"
            :style="{ width: '70vw', maxWidth: '900px' }"
            modal
            @show="loadVersionHistory"
        >
            <!-- Loading -->
            <div v-if="versionsLoading" class="space-y-3">
                <Skeleton height="5rem" v-for="i in 3" :key="i"></Skeleton>
            </div>

            <!-- Version List -->
            <div v-else-if="versions.length > 0" class="space-y-3">
                <Card
                    v-for="version in versions"
                    :key="version.id"
                    class="version-card"
                >
                    <template #content>
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-2">
                                    <span class="font-semibold text-lg">Version {{ version.version_number }}</span>
                                    <Tag v-if="latestVersion?.id === version.id" value="Latest" severity="success" />
                                </div>
                                <div class="flex items-center gap-2 text-sm text-color-secondary mb-2">
                                    <Tag icon="pi pi-clock" :value="formatDate(version.created_at)" severity="secondary" />
                                </div>
                                <p v-if="version.notes" class="text-sm text-color-secondary italic mt-2">
                                    "{{ version.notes }}"
                                </p>
                            </div>
                            <div class="flex gap-2 ml-4">
                                <Button
                                    label="View"
                                    icon="pi pi-eye"
                                    size="small"
                                    outlined
                                    @click="viewVersion(version)"
                                />
                                <Button
                                    v-if="canEdit && latestVersion?.id !== version.id"
                                    label="Restore"
                                    icon="pi pi-refresh"
                                    size="small"
                                    severity="warn"
                                    outlined
                                    @click="confirmRestore(version)"
                                />
                            </div>
                        </div>
                    </template>
                </Card>
            </div>

            <!-- Empty State -->
            <div v-else class="flex flex-col items-center text-center py-12">
                <i class="pi pi-inbox text-6xl text-color-secondary mb-4"></i>
                <p class="text-color-secondary mb-2">No published versions yet</p>
                <p class="text-sm text-color-secondary">Publish this page to create the first version</p>
            </div>
        </Dialog>

        <!-- View Version Dialog -->
        <Dialog
            v-model:visible="showVersionView"
            :header="`Version ${selectedVersion?.version_number} - ${selectedVersion?.title}`"
            :style="{ width: '80vw' }"
            modal
        >
            <div v-if="selectedVersion" class="prose dark:prose-invert max-w-none">
                <div v-html="renderContent(selectedVersion.content_json)"></div>
            </div>
        </Dialog>

        <!-- Restore Confirmation Dialog -->
        <Dialog
            v-model:visible="showRestoreDialog"
            header="Restore Version"
            :style="{ width: '400px' }"
            modal
        >
            <div class="space-y-4">
                <p class="text-muted-color">
                    Are you sure you want to restore version {{ selectedVersion?.version_number }}?
                    This will replace your current draft with the content from this version.
                </p>
                <div class="flex gap-2 justify-end">
                    <Button
                        label="Cancel"
                        severity="secondary"
                        @click="showRestoreDialog = false"
                    />
                    <Button
                        label="Restore"
                        icon="pi pi-refresh"
                        severity="warning"
                        :loading="isRestoring"
                        @click="restoreVersion"
                    />
                </div>
            </div>
        </Dialog>

        <!-- Publish Confirmation Dialog -->
        <Dialog
            v-model:visible="showPublishDialog"
            header="Publish Page"
            :style="{ width: '400px' }"
            modal
        >
            <div class="space-y-4">
                <p class="text-muted-color">
                    Publishing will create a new version and make your changes visible to all users.
                </p>

                <div>
                    <label class="block text-sm font-medium mb-2">Version Notes (optional)</label>
                    <Textarea
                        v-model="publishNotes"
                        placeholder="Describe what changed in this version"
                        rows="3"
                        class="w-full"
                    />
                </div>

                <div class="flex gap-2 justify-end">
                    <Button
                        label="Cancel"
                        severity="secondary"
                        @click="showPublishDialog = false"
                    />
                    <Button
                        label="Publish"
                        icon="pi pi-upload"
                        severity="success"
                        :loading="isPublishing"
                        @click="confirmPublish"
                    />
                </div>
            </div>
        </Dialog>

        <!-- Sidebar Components (teleported to layout) -->
        <Teleport to=".sidebar-content" v-if="page && !loading && !error" :disabled="!sidebarMounted">
            <div class="space-y-3">
                <!-- Page Outline -->
                <PageOutline
                    :content="latestVersion?.content_json || page.draft_json"
                    :loading="loading"
                />

                <!-- Backlinks -->
                <PageBacklinks
                    :page-id="pageId"
                    :space-key="route.params.spaceKey as string"
                />

                <!-- Attachments -->
                <PageAttachments
                    :page-id="pageId"
                />
            </div>
        </Teleport>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { pageService, type PageDetail, type PageVersion } from '@/services/pageService';
import { useAuthStore } from '@/stores/authStore';
import { useAutosave } from '@/composables/useAutosave';
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Breadcrumb from 'primevue/breadcrumb';
import Dialog from 'primevue/dialog';
import Skeleton from 'primevue/skeleton';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import Toolbar from 'primevue/toolbar';
import FloatLabel from 'primevue/floatlabel';
import TiptapEditor from '@/components/cms/TiptapEditor.vue';
import PageOutline from '@/components/cms/PageOutline.vue';
import PageBacklinks from '@/components/cms/PageBacklinks.vue';
import PageAttachments from '@/components/cms/PageAttachments.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();

// Inject edit mode from SpaceLayout
const isEditing = inject<any>('isEditing', ref(false));

// State
const page = ref<PageDetail | null>(null);
const latestVersion = ref<PageVersion | null>(null);
const breadcrumb = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showHistory = ref(false);
const versions = ref<PageVersion[]>([]);
const versionsLoading = ref(false);
const selectedVersion = ref<PageVersion | null>(null);
const showVersionView = ref(false);
const showRestoreDialog = ref(false);
const isRestoring = ref(false);
const sidebarMounted = ref(false);

// Edit mode state
const editorRef = ref<any>(null);
const editTitle = ref('');
const draftContent = ref<any>(null);
const currentEtag = ref<string | null>(null);
const showPublishDialog = ref(false);
const publishNotes = ref('');
const isPublishing = ref(false);

// Computed
const pageId = computed(() => {
    const pageIdSlug = route.params.pageIdSlug as string;
    if (!pageIdSlug) return null;

    // UUID format: 8-4-4-4-12 characters (36 chars with dashes)
    // Extract first 36 characters as the UUID
    // Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-slug
    const match = pageIdSlug.match(/^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i);
    return match ? match[1] : pageIdSlug.split('-')[0]; // Fallback to old logic
});

const canEdit = computed(() => {
    // TODO: Check actual permissions
    return authStore.user?.is_superuser || false;
});

const breadcrumbItems = computed(() => {
    return breadcrumb.value.map(item => ({
        label: item.title,
        command: () => router.push(`/${route.params.spaceKey}/p/${item.id}-${item.slug}`)
    }));
});

// Setup autosave when in edit mode
const { isSaving, lastSaved, hasUnsavedChanges, saveNow } = useAutosave({
    pageId: computed(() => pageId.value),
    content: draftContent,
    etag: currentEtag,
    debounceMs: 5000,
    onConflict: (newEtag) => {
        if (editorRef.value) {
            editorRef.value.handleConflict(newEtag);
        }
    },
    onEtagUpdate: (newEtag) => {
        currentEtag.value = newEtag;
    }
});

// Load page data
const loadPage = async () => {
    if (!pageId.value) {
        error.value = 'Invalid page ID';
        loading.value = false;
        return;
    }

    try {
        loading.value = true;
        error.value = null;

        // Load page details
        page.value = await pageService.getPageById(pageId.value);

        // Load latest version if published
        try {
            const versions = await pageService.listVersions(pageId.value, 0, 1);
            if (versions.length > 0) {
                // Fetch the full version with content
                latestVersion.value = await pageService.getVersion(pageId.value, versions[0].id);
            }
        } catch (err) {
            // No versions yet, that's ok
            console.log('No published versions yet');
            latestVersion.value = null;
        }

        // Load breadcrumb
        try {
            breadcrumb.value = await pageService.getBreadcrumb(pageId.value);
        } catch (err) {
            console.error('Failed to load breadcrumb:', err);
        }

        // If we're in edit mode, initialize editor state
        if (isEditing.value) {
            initializeEditMode();
        }
    } catch (err: any) {
        console.error('Failed to load page:', err);
        error.value = err.response?.data?.detail || 'Failed to load page';
    } finally {
        loading.value = false;
    }
};

// Initialize edit mode with page data
const initializeEditMode = () => {
    if (!page.value) return;

    editTitle.value = page.value.title;
    currentEtag.value = page.value.draft_etag;

    // Use draft if available, otherwise start with published or empty
    if (page.value.draft_json) {
        draftContent.value = page.value.draft_json;
    } else if (latestVersion.value?.content_json) {
        draftContent.value = latestVersion.value.content_json;
    } else {
        draftContent.value = {
            type: 'doc',
            content: [{ type: 'paragraph' }]
        };
    }
};

// Render Tiptap JSON to HTML for view mode
const renderContent = (json: any) => {
    if (!json) return '';

    let headingIndex = 0;

    // Simple Tiptap JSON to HTML renderer
    const renderNode = (node: any): string => {
        if (!node) return '';

        if (node.text) {
            let text = node.text;
            if (node.marks) {
                for (const mark of node.marks) {
                    if (mark.type === 'bold') text = `<strong>${text}</strong>`;
                    if (mark.type === 'italic') text = `<em>${text}</em>`;
                    if (mark.type === 'code') text = `<code>${text}</code>`;
                    if (mark.type === 'strike') text = `<s>${text}</s>`;
                    if (mark.type === 'link') {
                        text = `<a href="${mark.attrs.href}" class="text-primary hover:underline">${text}</a>`;
                    }
                }
            }
            return text;
        }

        const children = node.content ? node.content.map(renderNode).join('') : '';

        switch (node.type) {
            case 'doc':
                return children;
            case 'paragraph':
                return `<p>${children || '<br>'}</p>`;
            case 'heading':
                // Add ID to headings for outline navigation
                const headingId = `heading-${headingIndex++}`;
                return `<h${node.attrs?.level || 1} id="${headingId}">${children}</h${node.attrs?.level || 1}>`;
            case 'bulletList':
                return `<ul>${children}</ul>`;
            case 'orderedList':
                return `<ol>${children}</ol>`;
            case 'listItem':
                return `<li>${children}</li>`;
            case 'codeBlock':
                return `<pre><code>${children}</code></pre>`;
            case 'blockquote':
                return `<blockquote>${children}</blockquote>`;
            case 'horizontalRule':
                return '<hr>';
            case 'image':
                return `<img src="${node.attrs?.src}" alt="${node.attrs?.alt || ''}" />`;
            case 'hardBreak':
                return '<br>';
            default:
                return children;
        }
    };

    return renderNode(json);
};

// Format date
const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
};

// Actions
const startEditing = () => {
    if (!canEdit.value) return;
    isEditing.value = true;
    initializeEditMode();
};

const cancelEditing = () => {
    if (hasUnsavedChanges.value) {
        if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
            return;
        }
    }
    isEditing.value = false;
    // Reload page to get fresh data
    loadPage();
};

const handlePublish = () => {
    showPublishDialog.value = true;
};

const confirmPublish = async () => {
    if (!pageId.value) return;

    try {
        isPublishing.value = true;

        // First save any pending changes
        await saveNow();

        // Update title if changed
        if (editTitle.value !== page.value?.title) {
            await pageService.updatePage(pageId.value, { title: editTitle.value });
        }

        // Publish the draft
        const version = await pageService.publishPage(pageId.value, publishNotes.value || undefined);

        toast.add({
            severity: 'success',
            summary: 'Published',
            detail: `Version ${version.version_number} published successfully`,
            life: 3000
        });

        // Reset state
        showPublishDialog.value = false;
        publishNotes.value = '';
        isEditing.value = false;

        // Reload page
        await loadPage();
    } catch (err: any) {
        console.error('Publish failed:', err);
        toast.add({
            severity: 'error',
            summary: 'Publish Failed',
            detail: err.response?.data?.detail || 'Failed to publish page',
            life: 5000
        });
    } finally {
        isPublishing.value = false;
    }
};

// Version History Management
const loadVersionHistory = async () => {
    if (!pageId.value) return;

    try {
        versionsLoading.value = true;
        versions.value = await pageService.listVersions(pageId.value, 0, 50);
    } catch (err: any) {
        console.error('Failed to load version history:', err);
        toast.add({
            severity: 'error',
            summary: 'Load Failed',
            detail: 'Failed to load version history',
            life: 3000
        });
    } finally {
        versionsLoading.value = false;
    }
};

const viewVersion = (version: PageVersion) => {
    selectedVersion.value = version;
    showVersionView.value = true;
};

const confirmRestore = (version: PageVersion) => {
    selectedVersion.value = version;
    showRestoreDialog.value = true;
};

const restoreVersion = async () => {
    if (!pageId.value || !selectedVersion.value) return;

    try {
        isRestoring.value = true;

        // Call restore API
        const response = await pageService.restoreVersion(pageId.value, selectedVersion.value.id);

        toast.add({
            severity: 'success',
            summary: 'Version Restored',
            detail: `Version ${selectedVersion.value.version_number} has been restored to draft`,
            life: 3000
        });

        // Close dialogs
        showRestoreDialog.value = false;
        showHistory.value = false;

        // Reload page to get updated draft
        await loadPage();

        // Switch to edit mode to show the restored content
        if (canEdit.value) {
            isEditing.value = true;
        }
    } catch (err: any) {
        console.error('Failed to restore version:', err);
        toast.add({
            severity: 'error',
            summary: 'Restore Failed',
            detail: err.response?.data?.detail || 'Failed to restore version',
            life: 5000
        });
    } finally {
        isRestoring.value = false;
    }
};

// Watch for route changes
watch(() => route.params.pageIdSlug, () => {
    if (route.name === 'page-view') {
        loadPage();
    }
});

// Watch for edit mode changes from parent
watch(isEditing, (newValue, oldValue) => {
    if (newValue && page.value) {
        // Entering edit mode
        initializeEditMode();
    } else if (!newValue && oldValue && page.value) {
        // Exiting edit mode - reload page to get updated draft
        loadPage();
    }
});

// Keyboard Shortcuts
useKeyboardShortcuts([
    {
        key: 'e',
        ctrl: true,
        description: 'Toggle edit mode',
        handler: () => {
            if (canEdit.value) {
                isEditing.value = !isEditing.value;
            }
        }
    },
    {
        key: 's',
        ctrl: true,
        description: 'Save draft',
        handler: async () => {
            if (isEditing.value && hasUnsavedChanges.value) {
                await saveNow();
                toast.add({
                    severity: 'success',
                    summary: 'Saved',
                    detail: 'Draft saved successfully',
                    life: 2000
                });
            }
        }
    },
    {
        key: 'p',
        ctrl: true,
        shift: true,
        description: 'Publish page',
        handler: () => {
            if (isEditing.value && canEdit.value) {
                showPublishDialog.value = true;
            }
        }
    },
    {
        key: 'h',
        ctrl: true,
        description: 'View history',
        handler: () => {
            showHistory.value = true;
        }
    },
    {
        key: 'Escape',
        description: 'Cancel editing',
        handler: () => {
            if (isEditing.value) {
                cancelEditing();
            }
        }
    }
]);

// Load on mount
onMounted(() => {
    // Check if sidebar exists
    const checkSidebar = () => {
        const sidebar = document.querySelector('.sidebar-content');
        sidebarMounted.value = !!sidebar;
    };

    checkSidebar();
    // Recheck after a brief delay to ensure layout is mounted
    setTimeout(checkSidebar, 100);

    loadPage();
});
</script>

<style scoped>
.page-content {
    line-height: 1.7;
}

.rendered-content {
    color: var(--text-color);
}

/* Basic prose styling */
.prose :deep(p) {
    margin-bottom: 1rem;
    color: var(--text-color);
}

.prose :deep(h1) {
    font-size: 2rem;
    font-weight: 700;
    margin: 2rem 0 1rem;
    color: var(--text-color);
}

.prose :deep(h2) {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 1.5rem 0 0.75rem;
    color: var(--text-color);
}

.prose :deep(h3) {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 1.25rem 0 0.5rem;
    color: var(--text-color);
}

.prose :deep(h4),
.prose :deep(h5),
.prose :deep(h6) {
    font-weight: 600;
    margin: 1rem 0 0.5rem;
    color: var(--text-color);
}

.prose :deep(ul), .prose :deep(ol) {
    margin: 1rem 0;
    padding-left: 2rem;
}

.prose :deep(li) {
    margin: 0.5rem 0;
}

.prose :deep(code) {
    background: var(--surface-100);
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.9em;
}

.prose :deep(pre) {
    background: var(--surface-100);
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin: 1rem 0;
}

.prose :deep(blockquote) {
    border-left: 4px solid var(--primary-500);
    padding-left: 1rem;
    margin: 1rem 0;
    color: var(--text-color-secondary);
}
</style>
