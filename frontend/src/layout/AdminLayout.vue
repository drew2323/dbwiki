<template>
    <div class="layout-wrapper" :class="[containerClass, `layout-card-${layoutStore.layoutConfig.cardStyle}`]">
        <app-topbar></app-topbar>

        <!-- Horizontal Menu (when horizontal mode) -->
        <div v-if="layoutStore.layoutConfig.menuMode === 'horizontal'" class="layout-horizontal-menu">
            <app-menu></app-menu>
        </div>

        <!-- Sidebar Menu (for all other modes) -->
        <app-sidebar v-else></app-sidebar>

        <!-- Drawer Menu (when drawer mode) -->
        <Drawer
            v-if="layoutStore.layoutConfig.menuMode === 'drawer'"
            v-model:visible="layoutStore.layoutState.sidebarActive"
            position="left"
            class="layout-drawer-menu"
            :style="{ width: '20rem' }"
        >
            <app-menu></app-menu>
        </Drawer>

        <div class="layout-main-container">
            <div class="layout-main">
                <router-view></router-view>
            </div>
            <app-footer></app-footer>
        </div>
        <app-configurator></app-configurator>
        <div class="layout-mask"></div>
    </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue';
import { useLayoutStore } from '@/stores/layoutStore';
import AppTopbar from './AppTopbar.vue';
import AppFooter from './AppFooter.vue';
import AppSidebar from './AppSidebar.vue';
import AppMenu from './AppMenu.vue';
import AppConfigurator from './AppConfigurator.vue';
import Drawer from 'primevue/drawer';

const layoutStore = useLayoutStore();

const outsideClickListener = ref(null);

watch(
    () => layoutStore.layoutState.overlayMenuActive,
    (newVal) => {
        if (newVal) {
            bindOutsideClickListener();
        } else {
            unbindOutsideClickListener();
        }
    }
);

const containerClass = computed(() => {
    const classes = {
        // Base layout modes
        'layout-static': layoutStore.layoutConfig.menuMode === 'static',
        'layout-overlay': layoutStore.layoutConfig.menuMode === 'overlay',
        'layout-slim': layoutStore.layoutConfig.menuMode === 'slim',
        'layout-compact': layoutStore.layoutConfig.menuMode === 'compact',
        'layout-reveal': layoutStore.layoutConfig.menuMode === 'reveal',
        'layout-drawer': layoutStore.layoutConfig.menuMode === 'drawer',
        'layout-horizontal': layoutStore.layoutConfig.menuMode === 'horizontal',

        // Active states
        'layout-static-inactive': layoutStore.layoutState.staticMenuDesktopInactive && layoutStore.layoutConfig.menuMode === 'static',
        'layout-overlay-active': layoutStore.layoutState.overlayMenuActive,
        'layout-mobile-active': layoutStore.layoutState.staticMenuMobileActive,
        'layout-sidebar-active': layoutStore.layoutState.sidebarActive
    };

    return classes;
});

function bindOutsideClickListener() {
    if (!outsideClickListener.value) {
        outsideClickListener.value = (event) => {
            if (isOutsideClicked(event)) {
                layoutStore.layoutState.overlayMenuActive = false;
                layoutStore.layoutState.staticMenuMobileActive = false;
            }
        };
        document.addEventListener('click', outsideClickListener.value);
    }
}

function unbindOutsideClickListener() {
    if (outsideClickListener.value) {
        document.removeEventListener('click', outsideClickListener.value);
        outsideClickListener.value = null;
    }
}

function isOutsideClicked(event) {
    const sidebarEl = document.querySelector('.layout-sidebar');
    const topbarEl = document.querySelector('.layout-menu-button');

    return !(sidebarEl.isSameNode(event.target) || sidebarEl.contains(event.target) || topbarEl.isSameNode(event.target) || topbarEl.contains(event.target));
}
</script>

<style lang="scss" scoped></style>
