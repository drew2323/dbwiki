<template>
    <div class="page-tree">
        <!-- Loading State -->
        <div v-if="loading" class="space-y-2">
            <Skeleton v-for="n in 5" :key="n" height="2rem"></Skeleton>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-4">
            <i class="pi pi-exclamation-triangle text-red-500 mb-2"></i>
            <p class="text-sm text-muted-color">{{ error }}</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="treeNodes.length === 0" class="text-center py-8">
            <i class="pi pi-inbox text-4xl text-muted-color mb-2"></i>
            <p class="text-sm text-muted-color">No pages yet</p>
            <Button
                v-if="canEdit"
                label="Create First Page"
                icon="pi pi-plus"
                size="small"
                class="mt-3"
                @click="showCreateDialog = true"
            />
        </div>

        <!-- Tree with Drag-Drop -->
        <Tree
            v-else
            :value="treeNodes"
            :expandedKeys="expandedKeys"
            @nodeExpand="onNodeExpand"
            @nodeCollapse="onNodeCollapse"
            selectionMode="single"
            v-model:selectionKeys="selectedKeys"
            @nodeSelect="onNodeSelect"
            class="w-full border-none"
            :dragdrop="canEdit"
            draggableScope="pages"
            droppableScope="pages"
            @node-drop="onNodeDrop"
        >
            <template #default="slotProps">
                <div
                    class="flex items-center justify-between gap-2 py-1 w-full node-content-wrapper"
                    @contextmenu.prevent="showContextMenu($event, slotProps.node)"
                    @click="onNodeSelect(slotProps.node)"
                >
                    <!-- Left: Label + Archive Icon -->
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                        <span
                            class="truncate"
                            :class="{
                                'font-semibold': slotProps.node.key === currentPageId,
                                'text-muted-color': slotProps.node.is_archived
                            }"
                        >
                            {{ slotProps.node.label }}
                        </span>
                        <i
                            v-if="slotProps.node.is_archived"
                            class="pi pi-eye-slash text-xs text-muted-color flex-shrink-0"
                            title="Archived"
                        ></i>
                    </div>

                    <!-- Right: Hover Action Button -->
                    <div v-if="canEdit" class="node-actions flex-shrink-0 flex items-center">
                        <Button
                            icon="pi pi-ellipsis-h"
                            text
                            rounded
                            size="small"
                            severity="secondary"
                            class="action-button"
                            aria-label="Page actions"
                            data-testid="page-actions"
                            v-tooltip.bottom="'Page actions'"
                            @click.stop="showContextMenu($event, slotProps.node)"
                        />
                        <Button
                            icon="pi pi-plus"
                            text
                            rounded
                            size="small"
                            severity="secondary"
                            class="action-button"
                            v-tooltip.bottom="'Add child page'"
                            @click.stop="openCreateDialogForNode(slotProps.node)"
                        />
                    </div>
                </div>
            </template>
        </Tree>

        <!-- Context Menu -->
        <ContextMenu ref="contextMenu" :model="contextMenuItems" />

        <!-- Rename Dialog -->
        <Dialog
            v-model:visible="showRenameDialog"
            modal
            header="Rename Page"
            :style="{ width: '420px' }"
        >
            <label for="rename-title" class="block text-sm font-medium mb-2">Title</label>
            <InputText
                id="rename-title"
                v-model="renameTitle"
                class="w-full"
                :invalid="!renameTitle.trim()"
                data-testid="rename-input"
                @keyup.enter="submitRename"
                autofocus
            />
            <small class="text-muted-color block mt-2">
                The page address is updated to match the new title.
            </small>
            <template #footer>
                <Button label="Cancel" severity="secondary" outlined @click="showRenameDialog = false" />
                <Button
                    label="Rename"
                    icon="pi pi-check"
                    :loading="isWorking"
                    :disabled="!renameTitle.trim()"
                    data-testid="rename-confirm"
                    @click="submitRename"
                />
            </template>
        </Dialog>

        <!-- Delete Dialog -->
        <Dialog
            v-model:visible="showDeleteDialog"
            modal
            header="Delete Page"
            :style="{ width: '460px' }"
        >
            <p class="mb-3">
                What should happen to <strong>{{ deleteTarget?.label }}</strong>
                <span v-if="deleteDescendantCount > 0">
                    and its {{ deleteDescendantCount }} sub-page{{ deleteDescendantCount === 1 ? '' : 's' }}
                </span>?
            </p>
            <div class="flex flex-col gap-3">
                <div class="flex items-start gap-2">
                    <RadioButton v-model="deleteMode" inputId="del-archive" value="archive" />
                    <label for="del-archive" class="cursor-pointer">
                        <span class="font-medium">Archive</span>
                        <span class="block text-sm text-muted-color">Hides the page from readers. You can unarchive it later.</span>
                    </label>
                </div>
                <div class="flex items-start gap-2">
                    <RadioButton v-model="deleteMode" inputId="del-hard" value="hard" />
                    <label for="del-hard" class="cursor-pointer">
                        <span class="font-medium text-red-500">Delete permanently</span>
                        <span class="block text-sm text-muted-color">Removes the page, its versions and links. This cannot be undone.</span>
                    </label>
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" severity="secondary" outlined @click="showDeleteDialog = false" />
                <Button
                    :label="deleteMode === 'hard' ? 'Delete permanently' : 'Archive'"
                    :icon="deleteMode === 'hard' ? 'pi pi-trash' : 'pi pi-eye-slash'"
                    :severity="deleteMode === 'hard' ? 'danger' : 'primary'"
                    :loading="isWorking"
                    data-testid="delete-confirm"
                    @click="submitDelete"
                />
            </template>
        </Dialog>

        <!-- Create Page Dialog -->
        <CreatePageDialog
            v-model:visible="showCreateDialog"
            :space-id="spaceId"
            :space-key="spaceKey"
            :default-parent-id="selectedContextNode?.data?.id"
            :tree-nodes="flatTreeNodes"
            @created="handlePageCreated"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { pageService, type TreeNode as TreeNodeType } from '@/services/pageService';
import { useToast } from 'primevue/usetoast';
import Tree from 'primevue/tree';
import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';
import ContextMenu from 'primevue/contextmenu';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import RadioButton from 'primevue/radiobutton';
import { useCmsStore } from '@/stores/cmsStore';
import CreatePageDialog from './CreatePageDialog.vue';

// Props
const props = defineProps<{
    spaceId: string
    spaceKey: string
    canEdit?: boolean
}>();

const router = useRouter();
const route = useRoute();
const toast = useToast();
const cms = useCmsStore();

// State
const treeNodes = ref<any[]>([]);
const flatTreeNodes = ref<TreeNodeType[]>([]);
const expandedKeys = ref<Record<string, boolean>>({});
const selectedKeys = ref<Record<string, boolean>>({});
const loading = ref(true);
const error = ref<string | null>(null);
const showCreateDialog = ref(false);
const contextMenu = ref();
const selectedContextNode = ref<any>(null);
const showRenameDialog = ref(false);
const renameTitle = ref('');
const showDeleteDialog = ref(false);
const deleteTarget = ref<any>(null);
const deleteMode = ref<'archive' | 'hard'>('archive');
const isWorking = ref(false);

// Current page from route
const currentPageId = computed(() => {
    const pageIdSlug = route.params.pageIdSlug as string;
    if (!pageIdSlug) return null;
    // Route param is "<uuid>-<slug>"; a UUID itself contains dashes
    const match = pageIdSlug.match(/^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i);
    return match ? match[1] : pageIdSlug.split('-')[0];
});

// Context menu items
const contextMenuItems = computed(() => {
    if (!selectedContextNode.value || !props.canEdit) return [];

    return [
        {
            label: 'Create Child Page',
            icon: 'pi pi-plus',
            command: () => {
                showCreateDialog.value = true;
            }
        },
        {
            label: 'Duplicate',
            icon: 'pi pi-copy',
            command: () => duplicateNode(selectedContextNode.value)
        },
        {
            separator: true
        },
        {
            label: 'Rename',
            icon: 'pi pi-pencil',
            command: () => openRenameDialog(selectedContextNode.value)
        },
        {
            label: selectedContextNode.value?.is_archived ? 'Unarchive' : 'Archive',
            icon: selectedContextNode.value?.is_archived ? 'pi pi-eye' : 'pi pi-eye-slash',
            command: async () => {
                await toggleArchive(selectedContextNode.value);
            }
        },
        {
            separator: true
        },
        {
            label: 'Delete',
            icon: 'pi pi-trash',
            class: 'text-red-500',
            command: () => openDeleteDialog(selectedContextNode.value)
        }
    ];
});

// Load tree
const loadTree = async () => {
    try {
        loading.value = true;
        error.value = null;

        const nodes = await pageService.getSpaceTree(props.spaceId);
        console.log('PageTree: loaded nodes', nodes);
        flatTreeNodes.value = nodes;
        treeNodes.value = buildTreeStructure(nodes);
        console.log('PageTree: built tree', treeNodes.value);

        // Auto-expand to current page
        if (currentPageId.value) {
            await expandToPage(currentPageId.value);
        }
    } catch (err) {
        console.error('Failed to load page tree:', err);
        error.value = 'Failed to load pages';
    } finally {
        loading.value = false;
    }
};

// Build tree structure from flat nodes
const buildTreeStructure = (nodes: TreeNodeType[]): any[] => {
    const nodeMap = new Map<string, any>();
    const rootNodes: any[] = [];

    // Create node objects
    // Readers must not see archived pages; editors see them greyed out
    const visible = props.canEdit ? nodes : nodes.filter(n => !n.is_archived);
    nodes = visible;

    nodes.forEach(node => {
        if (!node.page_id) return; // Skip root sentinel

        nodeMap.set(node.id, {
            key: node.page_id,
            label: node.title || 'Untitled',
            icon: node.has_children ? 'pi pi-folder' : 'pi pi-file',
            children: [],
            data: node,
            is_archived: node.is_archived,
            leaf: !node.has_children
        });
    });

    // Build tree hierarchy
    nodes.forEach(node => {
        if (!node.page_id) return;

        const treeNode = nodeMap.get(node.id);
        if (!treeNode) return;

        if (node.parent_id) {
            const parent = nodeMap.get(node.parent_id);
            if (parent) {
                parent.children.push(treeNode);
            } else {
                rootNodes.push(treeNode);
            }
        } else {
            rootNodes.push(treeNode);
        }
    });

    return rootNodes;
};

// Expand tree to show specific page
const expandToPage = async (pageId: string) => {
    try {
        const breadcrumb = await pageService.getBreadcrumb(pageId);
        breadcrumb.forEach(item => {
            expandedKeys.value[item.id] = true;
        });
        selectedKeys.value[pageId] = true;
    } catch (err) {
        console.error('Failed to expand to page:', err);
    }
};

// Event handlers
const onNodeExpand = (node: any) => {
    expandedKeys.value[node.key] = true;
};

const onNodeCollapse = (node: any) => {
    delete expandedKeys.value[node.key];
};

const onNodeSelect = (node: any) => {
    console.log('PageTree: onNodeSelect called with node:', node);
    console.log('PageTree: node.data:', node.data);
    if (node.data?.page_id && node.data?.slug) {
        const spaceKey = route.params.spaceKey;
        const targetPath = `/${spaceKey}/p/${node.data.page_id}-${node.data.slug}`;
        console.log('PageTree: Navigating to:', targetPath);
        router.push(targetPath);
    } else {
        console.warn('PageTree: Missing page_id or slug in node.data:', node.data);
    }
};

// Watch for route changes
watch(() => route.params.pageIdSlug, async (newVal) => {
    if (newVal && currentPageId.value) {
        selectedKeys.value = {};
        selectedKeys.value[currentPageId.value] = true;
    }
});

// Drag and drop handler
const onNodeDrop = async (event: any) => {
    if (!props.canEdit) return;

    const droppedNode = event.dragNode;
    const targetNode = event.dropNode;
    const dropIndex = event.dropIndex;

    console.log('Drop event:', { droppedNode, targetNode, dropIndex });

    try {
        // Get the tree node IDs
        const droppedTreeNodeId = droppedNode.data.id;
        const targetTreeNodeId = targetNode?.data?.id;

        // Calculate new parent and position
        let newParentId: string | null = null;
        let newPosition: number = 1024; // Default position

        if (targetNode) {
            // Dropped onto another node - make it a child
            newParentId = targetTreeNodeId;
            newPosition = 1024; // First child position
        } else {
            // Dropped at root level
            newParentId = null;
            newPosition = (dropIndex + 1) * 1024;
        }

        // Optimistic update - store old tree
        const oldTreeNodes = [...treeNodes.value];

        // Update tree immediately (optimistic)
        await loadTree();

        // Make API call to move node
        try {
            await pageService.moveNode(droppedTreeNodeId, newParentId, newPosition);

            toast.add({
                severity: 'success',
                summary: 'Page Moved',
                detail: `"${droppedNode.label}" has been moved`,
                life: 2000
            });

            // Reload tree to get correct positions
            await loadTree();
        } catch (err: any) {
            console.error('Failed to move node:', err);

            // Rollback on error
            treeNodes.value = oldTreeNodes;

            toast.add({
                severity: 'error',
                summary: 'Move Failed',
                detail: err.response?.data?.detail || 'Failed to move page',
                life: 5000
            });
        }
    } catch (err) {
        console.error('Drop operation failed:', err);
    }
};

// Context menu
const showContextMenu = (event: MouseEvent, node: any) => {
    if (!props.canEdit) return;
    selectedContextNode.value = node;
    contextMenu.value.show(event);
};

// Open create dialog for a specific node (child page)
const openCreateDialogForNode = (node: any) => {
    selectedContextNode.value = node;
    showCreateDialog.value = true;
};

// Toggle archive status
const toggleArchive = async (node: any) => {
    if (!node?.data?.page_id) return;

    try {
        const isArchived = node.is_archived;
        await pageService.updatePage(node.data.page_id, {
            is_archived: !isArchived
        });

        toast.add({
            severity: 'success',
            summary: isArchived ? 'Unarchived' : 'Archived',
            detail: `"${node.label}" has been ${isArchived ? 'unarchived' : 'archived'}`,
            life: 2000
        });

        await loadTree();
    } catch (err: any) {
        console.error('Failed to toggle archive:', err);
        toast.add({
            severity: 'error',
            summary: 'Operation Failed',
            detail: err.response?.data?.detail || 'Failed to update page',
            life: 5000
        });
    }
};

// Pages below a tree node (any depth), used for the delete confirmation
const countDescendants = (treeNodeId: string): number => {
    const childrenOf = new Map<string, TreeNodeType[]>();
    flatTreeNodes.value.forEach(n => {
        if (n.parent_id && n.page_id) {
            childrenOf.set(n.parent_id, [...(childrenOf.get(n.parent_id) || []), n]);
        }
    });
    let count = 0;
    const walk = (id: string) => {
        (childrenOf.get(id) || []).forEach(child => { count++; walk(child.id); });
    };
    walk(treeNodeId);
    return count;
};
const deleteDescendantCount = computed(() =>
    deleteTarget.value?.data?.id ? countDescendants(deleteTarget.value.data.id) : 0
);

// Is `pageId` the open page, or below the given tree node?
const isOpenPageWithin = (treeNodeId: string, pageId: string): boolean => {
    if (!currentPageId.value) return false;
    if (currentPageId.value === pageId) return true;
    let node = flatTreeNodes.value.find(n => n.page_id === currentPageId.value);
    while (node?.parent_id) {
        if (node.parent_id === treeNodeId) return true;
        node = flatTreeNodes.value.find(n => n.id === node!.parent_id);
    }
    return false;
};

const apiError = (err: any, fallback: string) => err.response?.data?.detail || fallback;

// Rename
const openRenameDialog = (node: any) => {
    if (!node?.data?.page_id) return;
    selectedContextNode.value = node;
    renameTitle.value = node.label;
    showRenameDialog.value = true;
};

const submitRename = async () => {
    const node = selectedContextNode.value;
    const title = renameTitle.value.trim();
    if (!node?.data?.page_id || !title || isWorking.value) return;

    isWorking.value = true;
    try {
        const page = await pageService.updatePage(node.data.page_id, { title });
        showRenameDialog.value = false;
        toast.add({ severity: 'success', summary: 'Page Renamed', detail: `"${page.title}"`, life: 2000 });

        await loadTree();
        if (currentPageId.value === page.id) {
            // Slug follows the title, so move to the new address and refresh the open page
            await router.replace(`/${route.params.spaceKey}/p/${page.id}-${page.slug}`);
            cms.refreshPage();
        }
    } catch (err: any) {
        toast.add({ severity: 'error', summary: 'Rename Failed', detail: apiError(err, 'Failed to rename page'), life: 5000 });
    } finally {
        isWorking.value = false;
    }
};

// Delete / archive with confirmation
const openDeleteDialog = (node: any) => {
    if (!node?.data?.page_id) return;
    selectedContextNode.value = node;
    deleteTarget.value = node;
    deleteMode.value = 'archive';
    showDeleteDialog.value = true;
};

const submitDelete = async () => {
    const node = deleteTarget.value;
    if (!node?.data?.page_id || isWorking.value) return;

    isWorking.value = true;
    try {
        const hard = deleteMode.value === 'hard';
        const wasOpen = isOpenPageWithin(node.data.id, node.data.page_id);
        await pageService.deletePage(node.data.page_id, hard);
        showDeleteDialog.value = false;
        toast.add({
            severity: 'success',
            summary: hard ? 'Page Deleted' : 'Page Archived',
            detail: `"${node.label}"${deleteDescendantCount.value ? ` and ${deleteDescendantCount.value} sub-page(s)` : ''}`,
            life: 3000
        });

        // Leave a page that no longer exists before reloading the tree around it
        if (wasOpen && hard) {
            await router.push(`/${route.params.spaceKey}`);
        }
        await loadTree();
        if (wasOpen && !hard) {
            cms.refreshPage();
        }
    } catch (err: any) {
        toast.add({ severity: 'error', summary: 'Delete Failed', detail: apiError(err, 'Failed to delete page'), life: 5000 });
    } finally {
        isWorking.value = false;
    }
};

// Duplicate next to the original and open the copy
const duplicateNode = async (node: any) => {
    if (!node?.data?.page_id) return;
    try {
        const copy = await pageService.duplicatePage(node.data.page_id);
        toast.add({ severity: 'success', summary: 'Page Duplicated', detail: `"${copy.title}"`, life: 2500 });
        await loadTree();
        router.push(`/${route.params.spaceKey}/p/${copy.id}-${copy.slug}`);
    } catch (err: any) {
        toast.add({ severity: 'error', summary: 'Duplicate Failed', detail: apiError(err, 'Failed to duplicate page'), life: 5000 });
    }
};

// Handle page created
const handlePageCreated = async (page: any) => {
    // Store currently expanded keys before reload
    const currentlyExpanded = { ...expandedKeys.value };

    await loadTree();

    // If the page has a parent, make sure it's expanded
    if (selectedContextNode.value?.data?.id) {
        const parentTreeNodeId = selectedContextNode.value.data.id;
        // Find the parent node's page_id to use as key
        const parentNode = flatTreeNodes.value.find(n => n.id === parentTreeNodeId);
        if (parentNode?.page_id) {
            expandedKeys.value[parentNode.page_id] = true;
        }
    }

    // Restore other expanded keys
    Object.keys(currentlyExpanded).forEach(key => {
        if (currentlyExpanded[key]) {
            expandedKeys.value[key] = true;
        }
    });
};

// Other components (e.g. page view) can ask for a tree reload
watch(() => cms.treeRevision, () => loadTree());
// Archived pages are only shown to editors
watch(() => props.canEdit, () => {
    treeNodes.value = buildTreeStructure([...flatTreeNodes.value]);
});

// Load on mount
onMounted(() => {
    loadTree();
});

// Watch for space changes and reload tree
watch(
    () => props.spaceId,
    async (newSpaceId, oldSpaceId) => {
        if (newSpaceId && newSpaceId !== oldSpaceId) {
            console.log('PageTree: Space changed from', oldSpaceId, 'to', newSpaceId, '- reloading tree');
            // Reset tree state to avoid UX issues with stale expanded/selected keys
            selectedKeys.value = {};
            expandedKeys.value = {};
            // Reload tree for new space
            await loadTree();
        }
    }
);

// Create root page (called from parent via ref)
const createRootPage = () => {
    selectedContextNode.value = null;
    showCreateDialog.value = true;
};

// Expose methods
defineExpose({
    reload: loadTree,
    createRootPage
});
</script>

<style scoped>
.page-tree :deep(.p-tree) {
    background: transparent;
    border: none;
    padding: 0;
}

.page-tree :deep(.p-tree-node-content) {
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
}

.page-tree :deep(.p-tree-node-content > div) {
    width: 100%;
}

.page-tree :deep(.p-tree-node-content:hover) {
    background: var(--surface-100);
}

/* Node wrapper takes full width */
.node-content-wrapper {
    position: relative;
    width: 100%;
}

/* Hide action button by default on desktop */
.node-actions {
    opacity: 0;
    transition: opacity 0.2s ease;
}

/* Show action button on hover (desktop) */
.node-content-wrapper:hover .node-actions {
    opacity: 1;
}

/* Always show on touch devices */
@media (hover: none) {
    .node-actions {
        opacity: 1;
    }
}

/* Subtle styling for action button */
.action-button {
    width: 1.75rem;
    height: 1.75rem;
}

.page-tree :deep(.p-tree-node-content.p-tree-node-selectable:not(.p-disabled).p-tree-node-selected) {
    background: var(--primary-50);
    color: var(--primary-700);
}
</style>
