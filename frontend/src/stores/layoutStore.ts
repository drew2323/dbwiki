import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

const STORAGE_KEY = 'v3trading-layout-settings'

interface LayoutConfig {
  preset: string
  primary: string
  surface: string | null
  darkTheme: boolean
  menuMode: string
  menuTheme: string
  cardStyle: string
}

interface LayoutState {
  staticMenuDesktopInactive: boolean
  overlayMenuActive: boolean
  profileSidebarVisible: boolean
  configSidebarVisible: boolean
  staticMenuMobileActive: boolean
  menuHoverActive: boolean
  activeMenuItem: string | null
  sidebarActive: boolean
}

const defaultConfig: LayoutConfig = {
  preset: 'Aura',
  primary: 'emerald',
  surface: null,
  darkTheme: false,
  menuMode: 'static',
  menuTheme: 'dark',
  cardStyle: 'filled'
}

export const useLayoutStore = defineStore('layout', () => {
  // Layout Configuration (persisted)
  const layoutConfig = reactive<LayoutConfig>({ ...defaultConfig })

  // Layout State (runtime only - not persisted)
  const layoutState = reactive<LayoutState>({
    staticMenuDesktopInactive: false,
    overlayMenuActive: false,
    profileSidebarVisible: false,
    configSidebarVisible: false,
    staticMenuMobileActive: false,
    menuHoverActive: false,
    activeMenuItem: null,
    sidebarActive: false
  })

  // Computed
  const isDarkTheme = computed(() => layoutConfig.darkTheme)

  const isSidebarActive = computed(() =>
    layoutState.overlayMenuActive || layoutState.staticMenuMobileActive
  )

  const getPrimary = computed(() => layoutConfig.primary)

  const getSurface = computed(() => layoutConfig.surface)

  // For UI compatibility (SelectButton displays 'Light' or 'Dark')
  const colorSchemeDisplay = computed(() => layoutConfig.darkTheme ? 'Dark' : 'Light')

  // Actions
  const setActiveMenuItem = (item: any) => {
    layoutState.activeMenuItem = item.value || item
  }

  const executeDarkModeToggle = () => {
    layoutConfig.darkTheme = !layoutConfig.darkTheme
    document.documentElement.classList.toggle('app-dark')
  }

  const toggleDarkMode = () => {
    if (!document.startViewTransition) {
      executeDarkModeToggle()
      return
    }

    document.startViewTransition(() => executeDarkModeToggle())
  }

  const toggleMenu = () => {
    if (layoutConfig.menuMode === 'overlay') {
      layoutState.overlayMenuActive = !layoutState.overlayMenuActive
    } else if (layoutConfig.menuMode === 'drawer') {
      layoutState.sidebarActive = !layoutState.sidebarActive
    } else if (layoutConfig.menuMode === 'reveal') {
      // On mobile, reveal mode should behave like static mode
      if (window.innerWidth <= 991) {
        layoutState.staticMenuMobileActive = !layoutState.staticMenuMobileActive
      } else {
        // On desktop, reveal mode uses hover, so toggle has minimal effect
        layoutState.staticMenuDesktopInactive = !layoutState.staticMenuDesktopInactive
      }
      return // Exit early to avoid double-toggling
    }

    if (window.innerWidth > 991) {
      layoutState.staticMenuDesktopInactive = !layoutState.staticMenuDesktopInactive
    } else {
      layoutState.staticMenuMobileActive = !layoutState.staticMenuMobileActive
    }
  }

  const applyDarkModeClass = () => {
    if (layoutConfig.darkTheme) {
      document.documentElement.classList.add('app-dark')
    } else {
      document.documentElement.classList.remove('app-dark')
    }
  }

  const updatePreset = (preset: string) => {
    layoutConfig.preset = preset
  }

  const updatePrimary = (color: string) => {
    layoutConfig.primary = color
  }

  const updateSurface = (surface: string) => {
    layoutConfig.surface = surface
  }

  const updateDarkTheme = (isDark: boolean) => {
    if (layoutConfig.darkTheme !== isDark) {
      toggleDarkMode()
    }
  }

  const updateCardStyle = (style: string) => {
    layoutConfig.cardStyle = style.toLowerCase()
  }

  const updateMenuTheme = (theme: string) => {
    layoutConfig.menuTheme = theme.toLowerCase()
  }

  const updateMenuMode = (mode: string) => {
    console.log('Menu type changing to:', mode)
    layoutConfig.menuMode = mode

    // Reset active states when changing menu mode
    layoutState.overlayMenuActive = false
    layoutState.staticMenuMobileActive = false
    layoutState.sidebarActive = false
    layoutState.staticMenuDesktopInactive = false

    console.log('Layout config updated:', layoutConfig.menuMode)
  }

  return {
    // State
    layoutConfig,
    layoutState,

    // Computed
    isDarkTheme,
    isSidebarActive,
    getPrimary,
    getSurface,
    colorSchemeDisplay,

    // Actions
    setActiveMenuItem,
    toggleDarkMode,
    toggleMenu,
    applyDarkModeClass,
    updatePreset,
    updatePrimary,
    updateSurface,
    updateDarkTheme,
    updateCardStyle,
    updateMenuTheme,
    updateMenuMode
  }
}, {
  persist: {
    key: STORAGE_KEY,
    paths: ['layoutConfig']  // Only persist config, not runtime state
  }
})
