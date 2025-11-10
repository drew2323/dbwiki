<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useLayoutStore } from '@/stores/layoutStore';
import Button from 'primevue/button';
import AppMenuItem from './AppMenuItem.vue';

const layoutStore = useLayoutStore();
const isHovered = ref(false);

// Computed properties for pin functionality
const menuMode = computed(() => layoutStore.layoutConfig.menuMode);
const isPinnable = computed(() => menuMode.value === 'reveal' || menuMode.value === 'static');
const isPinned = computed(() => menuMode.value === 'static');
const showPin = computed(() => {
    // Show pin only on desktop and when menu is pinnable
    if (!isPinnable.value) return false;
    // In static mode, always show
    if (isPinned.value) return true;
    // In reveal mode, only show when hovered
    return isHovered.value;
});

// Toggle between reveal and static modes
const togglePin = () => {
    if (menuMode.value === 'reveal') {
        layoutStore.updateMenuMode('static');
    } else if (menuMode.value === 'static') {
        layoutStore.updateMenuMode('reveal');
    }
};

// Track sidebar hover state
let sidebarElement = null;

const handleMouseEnter = () => {
    isHovered.value = true;
};

const handleMouseLeave = () => {
    isHovered.value = false;
};

onMounted(() => {
    // Find the sidebar element and attach hover listeners
    sidebarElement = document.querySelector('.layout-sidebar');
    if (sidebarElement) {
        sidebarElement.addEventListener('mouseenter', handleMouseEnter);
        sidebarElement.addEventListener('mouseleave', handleMouseLeave);
    }
});

onUnmounted(() => {
    // Clean up event listeners
    if (sidebarElement) {
        sidebarElement.removeEventListener('mouseenter', handleMouseEnter);
        sidebarElement.removeEventListener('mouseleave', handleMouseLeave);
    }
});

const model = ref([
    {
        label: 'Home',
        items: [
            { label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' },
            { label: 'Dashboard2', icon: 'pi pi-fw pi-chart-line', to: '/dashboard2' }
        ]
    },
    {
        label: 'UI Components',
        items: [
            { label: 'Form Layout', icon: 'pi pi-fw pi-id-card', to: '/uikit/formlayout' },
            { label: 'Input', icon: 'pi pi-fw pi-check-square', to: '/uikit/input' },
            { label: 'Button', icon: 'pi pi-fw pi-mobile', to: '/uikit/button', class: 'rotated-icon' },
            { label: 'Table', icon: 'pi pi-fw pi-table', to: '/uikit/table' },
            { label: 'List', icon: 'pi pi-fw pi-list', to: '/uikit/list' },
            { label: 'Tree', icon: 'pi pi-fw pi-share-alt', to: '/uikit/tree' },
            { label: 'Panel', icon: 'pi pi-fw pi-tablet', to: '/uikit/panel' },
            { label: 'Overlay', icon: 'pi pi-fw pi-clone', to: '/uikit/overlay' },
            { label: 'Media', icon: 'pi pi-fw pi-image', to: '/uikit/media' },
            { label: 'Menu', icon: 'pi pi-fw pi-bars', to: '/uikit/menu' },
            { label: 'Message', icon: 'pi pi-fw pi-comment', to: '/uikit/message' },
            { label: 'File', icon: 'pi pi-fw pi-file', to: '/uikit/file' },
            { label: 'Chart', icon: 'pi pi-fw pi-chart-bar', to: '/uikit/charts' },
            { label: 'Timeline', icon: 'pi pi-fw pi-calendar', to: '/uikit/timeline' },
            { label: 'Misc', icon: 'pi pi-fw pi-circle', to: '/uikit/misc' }
        ]
    },
    {
        label: 'Pages',
        icon: 'pi pi-fw pi-briefcase',
        to: '/pages',
        items: [
            {
                label: 'Landing',
                icon: 'pi pi-fw pi-globe',
                to: '/landing'
            },
            {
                label: 'Auth',
                icon: 'pi pi-fw pi-user',
                items: [
                    {
                        label: 'Login',
                        icon: 'pi pi-fw pi-sign-in',
                        to: '/auth/login'
                    },
                    {
                        label: 'Login Alt',
                        icon: 'pi pi-fw pi-sign-in',
                        to: '/auth/login-alt'
                    },
                    {
                        label: 'Register',
                        icon: 'pi pi-fw pi-user-plus',
                        to: '/auth/register'
                    },
                    {
                        label: 'Error',
                        icon: 'pi pi-fw pi-times-circle',
                        to: '/auth/error'
                    },
                    {
                        label: 'Access Denied',
                        icon: 'pi pi-fw pi-lock',
                        to: '/auth/access'
                    }
                ]
            },
            {
                label: 'Crud',
                icon: 'pi pi-fw pi-pencil',
                to: '/pages/crud'
            },
            {
                label: 'Not Found',
                icon: 'pi pi-fw pi-exclamation-circle',
                to: '/pages/notfound'
            },
            {
                label: 'Empty',
                icon: 'pi pi-fw pi-circle-off',
                to: '/pages/empty'
            }
        ]
    },
    {
        label: 'Hierarchy',
        items: [
            {
                label: 'Submenu 1',
                icon: 'pi pi-fw pi-bookmark',
                items: [
                    {
                        label: 'Submenu 1.1',
                        icon: 'pi pi-fw pi-bookmark',
                        items: [
                            { label: 'Submenu 1.1.1', icon: 'pi pi-fw pi-bookmark' },
                            { label: 'Submenu 1.1.2', icon: 'pi pi-fw pi-bookmark' },
                            { label: 'Submenu 1.1.3', icon: 'pi pi-fw pi-bookmark' }
                        ]
                    },
                    {
                        label: 'Submenu 1.2',
                        icon: 'pi pi-fw pi-bookmark',
                        items: [{ label: 'Submenu 1.2.1', icon: 'pi pi-fw pi-bookmark' }]
                    }
                ]
            },
            {
                label: 'Submenu 2',
                icon: 'pi pi-fw pi-bookmark',
                items: [
                    {
                        label: 'Submenu 2.1',
                        icon: 'pi pi-fw pi-bookmark',
                        items: [
                            { label: 'Submenu 2.1.1', icon: 'pi pi-fw pi-bookmark' },
                            { label: 'Submenu 2.1.2', icon: 'pi pi-fw pi-bookmark' }
                        ]
                    },
                    {
                        label: 'Submenu 2.2',
                        icon: 'pi pi-fw pi-bookmark',
                        items: [{ label: 'Submenu 2.2.1', icon: 'pi pi-fw pi-bookmark' }]
                    }
                ]
            }
        ]
    },
    {
        label: 'Get Started',
        items: [
            {
                label: 'Documentation',
                icon: 'pi pi-fw pi-book',
                to: '/documentation'
            },
            {
                label: 'View Source',
                icon: 'pi pi-fw pi-github',
                url: 'https://github.com/primefaces/sakai-vue',
                target: '_blank'
            }
        ]
    }
]);
</script>

<template>
    <div class="menu-container">
        <!-- Pin Button - Desktop only, shown when expanded -->
        <div v-if="showPin" class="menu-pin-wrapper hidden lg:flex">
            <Button
                :icon="isPinned ? 'pi pi-thumbtack' : 'pi pi-thumbtack'"
                @click="togglePin"
                text
                rounded
                size="small"
                :class="{ 'pin-active': isPinned }"
                :title="isPinned ? 'Unpin menu (switch to Reveal)' : 'Pin menu (switch to Static)'"
                severity="secondary"
            />
        </div>

        <ul class="layout-menu">
            <template v-for="(item, i) in model" :key="item">
                <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
                <li v-if="item.separator" class="menu-separator"></li>
            </template>
        </ul>
    </div>
</template>

<style lang="scss" scoped>
.menu-container {
    position: relative;
}

.menu-pin-wrapper {
    position: absolute;
    top: -0.55rem;
    right: 0;
    z-index: 10;
    opacity: 0;
    animation: fadeIn 0.3s ease-in forwards;
    animation-delay: 0.1s;

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    :deep(.p-button) {
        transition: all 0.2s ease;
        color: var(--text-color);

        &:hover {
            background-color: var(--surface-hover);
            color: var(--primary-color);
        }

        &.pin-active {
            color: var(--primary-color);

            .pi-thumbtack {
                transform: rotate(45deg);
            }
        }

        .pi-thumbtack {
            transition: transform 0.2s ease;
        }
    }
}
</style>
