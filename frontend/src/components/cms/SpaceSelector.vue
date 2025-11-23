<template>
    <div class="space-selector flex items-center gap-2">
        <!-- SplitButton for Space Navigation and Switching -->
        <SplitButton
            :label="space?.name || 'Loading...'"
            :icon="space?.is_public ? 'pi pi-globe' : 'pi pi-lock'"
            :model="spaceMenuItems"
            :loading="loading"
            :disabled="!space"
            @click="navigateToSpaceHome"
            severity="secondary"
            text
        >
            <template #dropdownicon>
                <i class="pi pi-chevron-down text-sm"></i>
            </template>
        </SplitButton>

        <!-- Public/Private Tag (shown next to the button) -->
        <Tag
            v-if="space"
            :icon="space.is_public ? 'pi pi-globe' : 'pi pi-lock'"
            :value="space.is_public ? 'Public' : 'Private'"
            :severity="space.is_public ? 'info' : 'secondary'"
            rounded
        />
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { spaceService, type Space } from '@/services/spaceService';
import SplitButton from 'primevue/splitbutton';
import Tag from 'primevue/tag';

// Props
interface Props {
    currentSpace: any; // Can be a ref or a Space object
}

const props = defineProps<Props>();

// Unwrap the current space if it's a ref
const space = computed(() => {
    // If it's a ref (from inject), unwrap it
    if (props.currentSpace && typeof props.currentSpace === 'object' && 'value' in props.currentSpace) {
        return props.currentSpace.value;
    }
    // Otherwise, it's already the space object
    return props.currentSpace;
});

// Composables
const router = useRouter();
const authStore = useAuthStore();

// State
const availableSpaces = ref<Space[]>([]);
const loading = ref(false);

// Computed
const spaceMenuItems = computed(() => {
    if (!availableSpaces.value.length) {
        return [
            {
                label: 'No spaces available',
                disabled: true,
                icon: 'pi pi-info-circle'
            }
        ];
    }

    return availableSpaces.value.map((s) => {
        const iconClass = s.is_public ? 'pi pi-globe' : 'pi pi-lock';
        return {
            label: s.name,
            icon: iconClass,
            command: () => switchSpace(s),
            class: s.id === space.value?.id ? 'bg-primary-50 dark:bg-primary-900/20' : '',
            template: (item: any) => {
                return {
                    default: () => {
                        return `
                            <div class="flex items-center gap-2 w-full">
                                <i class="${iconClass}"></i>
                                <span class="flex-1">${item.label}</span>
                                ${s.id === space.value?.id ? '<i class="pi pi-check text-primary"></i>' : ''}
                            </div>
                        `;
                    }
                };
            }
        };
    });
});

// Methods
const navigateToSpaceHome = () => {
    if (space.value?.key) {
        router.push(`/${space.value.key}`);
    }
};

const switchSpace = (selectedSpace: Space) => {
    if (selectedSpace.key !== space.value?.key) {
        router.push(`/${selectedSpace.key}`);
    }
};

const fetchAvailableSpaces = async () => {
    loading.value = true;

    try {
        const spaces: Space[] = [];

        // Fetch public spaces
        try {
            const publicSpaces = await spaceService.getPublicSpaces();
            console.log('SpaceSelector: Fetched public spaces:', publicSpaces);
            spaces.push(...publicSpaces);
        } catch (err) {
            console.error('Failed to fetch public spaces:', err);
            // Continue anyway - user might still have private spaces
        }

        // Fetch user spaces if authenticated
        if (authStore.isAuthenticated) {
            try {
                const userSpaces = await spaceService.getMySpaces();
                console.log('SpaceSelector: Fetched user spaces:', userSpaces);

                // Extract Space objects and add them
                const userSpaceObjects = userSpaces.map(us => us.space);

                // Merge and deduplicate by space ID
                userSpaceObjects.forEach(userSpace => {
                    if (!spaces.find(s => s.id === userSpace.id)) {
                        spaces.push(userSpace);
                    }
                });
            } catch (err) {
                console.error('Failed to fetch user spaces:', err);
            }
        }

        // Sort: Current space first, then alphabetically
        availableSpaces.value = spaces.sort((a, b) => {
            if (a.id === space.value?.id) return -1;
            if (b.id === space.value?.id) return 1;
            return a.name.localeCompare(b.name);
        });

        console.log('SpaceSelector: Total available spaces:', availableSpaces.value);
    } catch (error) {
        console.error('Failed to fetch available spaces:', error);
        availableSpaces.value = [];
    } finally {
        loading.value = false;
        console.log('SpaceSelector: Loading complete, loading state:', loading.value);
    }
};

// Lifecycle
onMounted(() => {
    console.log('SpaceSelector: Mounted, currentSpace:', space.value);
    // Only fetch if we have a current space
    if (space.value) {
        fetchAvailableSpaces();
    }
});

// Watch for auth changes to refetch spaces
watch(
    () => authStore.isAuthenticated,
    (newVal) => {
        console.log('SpaceSelector: Auth changed:', newVal);
        fetchAvailableSpaces();
    }
);

// Watch for current space to become available and trigger fetch
watch(
    () => space.value,
    (newSpace, oldSpace) => {
        console.log('SpaceSelector: currentSpace changed from', oldSpace, 'to', newSpace);

        // If we just got a space for the first time, fetch available spaces
        if (newSpace && !oldSpace) {
            fetchAvailableSpaces();
        } else if (newSpace && availableSpaces.value.length > 0) {
            // Re-sort to put current space first
            availableSpaces.value = [...availableSpaces.value].sort((a, b) => {
                if (a.id === newSpace.id) return -1;
                if (b.id === newSpace.id) return 1;
                return a.name.localeCompare(b.name);
            });
        }
    },
    { immediate: true }
);
</script>

<style scoped>
.space-selector {
    display: flex;
    align-items: center;
}

/* Override SplitButton styles to make it more compact */
:deep(.p-splitbutton) {
    .p-button {
        font-weight: 600;
        font-size: 1.125rem;
    }
}
</style>
