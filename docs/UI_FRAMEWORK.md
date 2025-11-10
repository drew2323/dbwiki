# UI Framework Documentation

## PrimeVue Integration

### Overview
- **Framework**: PrimeVue 4 with full component library
- **Icons**: PrimeIcons
- **Theming**: PrimeVue Themes (@primevue/themes)
- **Auto-Import**: Components auto-imported via unplugin-vue-components
- **State Management**: Pinia stores for centralized state

### State Management

#### Layout Store (`stores/layoutStore.ts`)
Centralized Pinia store managing all layout state and user preferences with automatic persistence:

**Layout Configuration (Persisted to localStorage)**:
```typescript
layoutConfig: {
  preset: string           // Theme preset: 'Aura', 'Lara', 'Nora'
  primary: string          // Primary color: 'emerald', 'blue', etc.
  surface: string | null   // Surface palette: 'slate', 'zinc', etc.
  darkTheme: boolean       // Dark mode enabled (single source of truth)
  menuMode: string         // Menu mode: 'static', 'overlay', 'drawer', 'reveal', 'slim', 'compact', 'horizontal'
  menuTheme: string        // Menu theme: 'dark', 'primary'
  cardStyle: string        // Card style: 'filled', 'transparent'
}
```

**Layout State (Runtime only - not persisted)**:
```typescript
layoutState: {
  staticMenuDesktopInactive: boolean
  overlayMenuActive: boolean
  profileSidebarVisible: boolean
  configSidebarVisible: boolean
  staticMenuMobileActive: boolean
  menuHoverActive: boolean
  activeMenuItem: string | null
  sidebarActive: boolean
}
```

**Store Actions**:
- `toggleMenu()` - Toggle menu based on current mode
- `toggleDarkMode()` - Toggle dark theme with View Transitions API support
- `setActiveMenuItem(item)` - Set active menu item
- `applyDarkModeClass()` - Apply/remove `.app-dark` class on document
- `updatePreset(preset)` - Update theme preset
- `updatePrimary(color)` - Update primary color
- `updateSurface(surface)` - Update surface palette
- `updateDarkTheme(isDark)` - Update dark theme (toggles if different)
- `updateCardStyle(style)` - Update card style
- `updateMenuTheme(theme)` - Update menu theme
- `updateMenuMode(mode)` - Update menu mode (resets active states)

**Computed Properties**:
- `isDarkTheme` - Returns `layoutConfig.darkTheme`
- `isSidebarActive` - Returns if overlay or mobile menu is active
- `getPrimary` - Returns current primary color
- `getSurface` - Returns current surface palette
- `colorSchemeDisplay` - Returns 'Dark' or 'Light' for UI display

**Usage Example**:
```typescript
import { useLayoutStore } from '@/stores/layoutStore'

const layoutStore = useLayoutStore()

// Read state (reactive)
layoutStore.layoutConfig.darkTheme
layoutStore.isDarkTheme
layoutStore.layoutConfig.menuMode

// Update state (auto-persists and updates everywhere)
layoutStore.toggleDarkMode()
layoutStore.updateMenuMode('overlay')
layoutStore.updatePrimary('emerald')
```

**Key Features**:
- ✅ Automatic localStorage persistence via `pinia-plugin-persistedstate`
- ✅ Bidirectional reactivity - changes anywhere reflect everywhere
- ✅ Type-safe with TypeScript interfaces
- ✅ Centralized single source of truth
- ✅ Consistent with other stores (authStore, tradingStore)

### Theme Configuration

#### AppSettings Component
- Located in `layout/AppSettings.vue`
- Full settings drawer with all theme options
- Uses computed refs for bidirectional binding to layoutStore
- Configurable options:
  - Primary color palette (18 colors)
  - Surface palette (9 palettes)
  - Theme presets (Aura, Lara, Nora)
  - Color scheme (Light/Dark)
  - Card style (Filled/Transparent)
  - Menu theme (Dark/Primary)
  - Menu type (7 modes)

#### AppConfigurator Component
- Located in `layout/AppConfigurator.vue`
- Compact theme configuration dropdown
- Subset of AppSettings options
- Real-time theme preview
- Uses computed refs for bidirectional binding

## Layout System

### AppLayout (`layout/AppLayout.vue`)
Main layout wrapper that provides the application structure:
- Header (AppTopbar)
- Sidebar (AppSidebar)
- Main content area
- Footer (AppFooter)
- Responsive breakpoints

### AppTopbar (`layout/AppTopbar.vue`)
Top navigation bar featuring:
- Logo/branding
- User menu with profile picture
- Notifications dropdown
- Search functionality
- Mobile menu toggle

### AppSidebar (`layout/AppSidebar.vue`)
Side navigation panel:
- Collapsible menu
- AppMenu component integration
- Responsive design
- State persistence

### AppMenu (`layout/AppMenu.vue`)
Main navigation menu:
- Hierarchical menu structure
- AppMenuItem components
- Route-based active states
- Icon support

### AppFooter (`layout/AppFooter.vue`)
Footer component with customizable content

## Dashboard

### Dashboard Widgets

Located in `components/dashboard/`:

**StatsWidget**
- Key metrics display
- Icon support
- Color-coded values
- Trend indicators

**RevenueStreamWidget**
- Revenue visualization
- Chart.js integration
- Time-series data
- Interactive legends

**RecentSalesWidget**
- Recent transactions table
- Sortable columns
- Pagination
- Action buttons

**BestSellingWidget**
- Top products/symbols
- Performance metrics
- Visual indicators

**NotificationsWidget**
- Activity feed
- Real-time updates
- Action links
- Badge indicators

### Charts
- **Library**: Chart.js 4
- **Integration**: Dedicated ChartDoc demo
- **Types**: Line, Bar, Pie, Doughnut, etc.
- **Responsiveness**: Auto-resize

## UI Kit Demos

Complete PrimeVue component demonstrations in `views/uikit/`:

### Component Categories

**Form Components**
- `InputDoc.vue`: Text inputs, TextArea, Number inputs, etc.
- `FormLayout.vue`: Form layout examples and patterns
- `ButtonDoc.vue`: Button variants, sizes, icons

**Data Display**
- `TableDoc.vue`: DataTable with sorting, filtering, pagination, selection
- `ListDoc.vue`: OrderList, PickList, DataView
- `TreeDoc.vue`: Tree, TreeTable components

**Navigation**
- `MenuDoc.vue`: Menubar, TieredMenu, Breadcrumb, Steps, TabMenu
- `PanelsDoc.vue`: Panel, Accordion, TabView, Toolbar

**Overlay**
- `OverlayDoc.vue`: Dialog, Sidebar, Tooltip, ConfirmDialog

**Media**
- `MediaDoc.vue`: Image, Carousel, Galleria

**Messages**
- `MessagesDoc.vue`: Message, Toast, InlineMessage

**Data Visualization**
- `ChartDoc.vue`: Chart.js integration examples
- `TimelineDoc.vue`: Timeline component

**File**
- `FileDoc.vue`: FileUpload component

**Misc**
- `MiscDoc.vue`: ProgressBar, Badge, Avatar, Chip, Tag, etc.

## Landing Page Components

Located in `components/landing/`:

- **HeroWidget**: Hero section with CTA
- **FeaturesWidget**: Feature highlights grid
- **HighlightsWidget**: Key selling points
- **PricingWidget**: Pricing tiers
- **TopbarWidget**: Landing page navigation
- **FooterWidget**: Landing page footer

## Styling

### Tailwind CSS
- Utility-first CSS framework
- Custom configuration in `tailwind.config.js`
- PrimeVue integration
- Responsive design utilities

### Sass
- Component-specific styles
- Layout variables in `assets/layout/`
- Theme customization
- Mixins and utilities

### PostCSS
- Configuration in `postcss.config.js`
- Autoprefixer for browser compatibility
- CSS optimization

## Legacy Components

### Demo Services
Located in `src/service/` (legacy):
- `CountryService.js`: Country data for demos
- `CustomerService.js`: Customer data for tables
- `NodeService.js`: Tree node data
- `PhotoService.js`: Image gallery data
- `ProductService.js`: Product catalog data

These services provide mock data for UI kit demonstrations and can be removed in production.

## Best Practices

### Component Development
1. Use Vue 3 Composition API
2. Follow PrimeVue component patterns
3. Leverage auto-import for PrimeVue components
4. Use TypeScript for type safety
5. Use Pinia stores for state management

### State Management
1. Import layoutStore for layout/theme access: `const layoutStore = useLayoutStore()`
2. Access state reactively: `layoutStore.layoutConfig.darkTheme`
3. Use computed properties for derived state: `layoutStore.isDarkTheme`
4. Update state via actions: `layoutStore.updateMenuMode('overlay')`
5. For theme-reactive components, watch store properties:
   ```typescript
   watch(() => layoutStore.isDarkTheme, () => {
     // Update component when theme changes
   })
   ```

### Theming
1. Use layoutStore for theme state management
2. Use AppSettings for user-facing theme configuration
3. Use AppConfigurator for quick theme adjustments
4. Follow PrimeVue theming guidelines
5. Maintain consistent color palette
6. Test light/dark mode compatibility
7. Use PrimeVue CSS variables for custom styling

### Responsive Design
1. Use PrimeVue responsive utilities
2. Test on multiple breakpoints
3. Mobile-first approach
4. Collapsible sidebar for mobile
5. Layout adapts automatically based on `layoutStore.layoutConfig.menuMode`

## Future Enhancements

- Integration of custom trading components into Dashboard
- Remove/archive legacy UI kit demo pages for production
- Custom theme creation
- Component library expansion
- Advanced data visualization components
