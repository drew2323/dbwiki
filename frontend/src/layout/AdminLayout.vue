<template>
    <div class="layout-wrapper" :class="containerClass">
        <app-topbar></app-topbar>
        <div class="layout-sidebar">
            <app-sidebar></app-sidebar>
        </div>
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
import { computed } from 'vue';
import AppTopbar from './AppTopbar.vue';
import AppFooter from './AppFooter.vue';
import AppSidebar from './AppSidebar.vue';
import AppConfigurator from './AppConfigurator.vue';
import { useLayoutStore } from '@/stores/layoutStore';

const layoutStore = useLayoutStore();

const containerClass = computed(() => {
    return {
        'layout-theme-light': layoutStore.layoutColorMode === 'light',
        'layout-theme-dark': layoutStore.layoutColorMode === 'dark',
        'layout-overlay': layoutStore.menuMode === 'overlay',
        'layout-static': layoutStore.menuMode === 'static',
        'layout-static-inactive': layoutStore.staticMenuDesktopInactive && layoutStore.menuMode === 'static',
        'layout-overlay-active': layoutStore.overlayMenuActive,
        'layout-mobile-active': layoutStore.staticMenuMobileActive,
        'p-input-filled': layoutStore.inputStyle === 'filled',
        'p-ripple-disabled': !layoutStore.ripple
    };
});
</script>

<style lang="scss" scoped></style>
