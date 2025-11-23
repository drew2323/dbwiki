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
            @node-drag-start="onNodeDragStart"
            @node-drag-enter="onNodeDragEnter"
            @node-drag-leave="onNodeDragLeave"
            @node-drag-end="onNodeDragEnd"
            @node-drop="onNodeDrop"
        >
            <template #default="slotProps">
                <div
                    class="flex items-center justify-between gap-2 py-1 w-full node-content-wrapper"
                    :draggable="canEdit"
                    @contextmenu.prevent="showContextMenu($event, slotProps.node)"
                >
                    <!-- Left: Icon + Label -->
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                        <i
                            :class="slotProps.node.icon || 'pi pi-file'"
                            class="text-muted-color flex-shrink-0"
                        ></i>
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
                    <div v-if="canEdit" class="node-actions flex-shrink-0">
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
const draggedNode = ref<any>(null);

// Current page from route
const currentPageId = computed(() => {
    const pageIdSlug = route.params.pageIdSlug as string;
    if (!pageIdSlug) return null;
    return pageIdSlug.split('-')[0]; // Extract ID from "id-slug" format
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
            separator: true
        },
        {
            label: 'Rename',
            icon: 'pi pi-pencil',
            command: () => {
                // TODO: Implement rename dialog
                toast.add({
                    severity: 'info',
                    summary: 'Coming Soon',
                    detail: 'Rename functionality will be available soon',
                    life: 3000
                });
            }
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
            command: () => {
                // TODO: Implement delete confirmation
                toast.add({
                    severity: 'info',
                    summary: 'Coming Soon',
                    detail: 'Delete functionality will be available soon',
                    life: 3000
                });
            }
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
    if (node.data?.page_id && node.data?.slug) {
        const spaceKey = route.params.spaceKey;
        router.push(`/${spaceKey}/p/${node.data.page_id}-${node.data.slug}`);
    }
};

// Watch for route changes
watch(() => route.params.pageIdSlug, async (newVal) => {
    if (newVal && currentPageId.value) {
        selectedKeys.value = {};
        selectedKeys.value[currentPageId.value] = true;
    }
});

// Drag and drop handlers
const onNodeDragStart = (event: any) => {
    if (!props.canEdit) return;
    draggedNode.value = event.node;
};

const onNodeDragEnter = (event: any) => {
    // Visual feedback could be added here
};

const onNodeDragLeave = (event: any) => {
    // Clean up visual feedback
};

const onNodeDragEnd = (event: any) => {
    draggedNode.value = null;
};

const onNodeDrop = async (event: any) => {
    if (!props.canEdit || !draggedNode.value) return;

    const droppedNode = draggedNode.value;
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
