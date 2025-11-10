# Architecture Documentation

## Project Structure

```
v3trading/
├── backend/
│   ├── app/
│   │   ├── dependencies/
│   │   │   └── auth.py              # Auth dependencies for route protection
│   │   ├── models/
│   │   │   ├── trade.py             # Trade Pydantic models
│   │   │   ├── position.py          # Position Pydantic models
│   │   │   └── user.py              # User Pydantic models
│   │   ├── routers/
│   │   │   ├── auth.py              # OAuth & authentication routes
│   │   │   ├── trades.py            # Trading endpoints
│   │   │   └── positions.py         # Position endpoints
│   │   └── utils/
│   │       ├── auth.py              # JWT token utilities
│   │       ├── mock_data.py         # Mock trading data generators
│   │       └── mock_users.py        # Mock user storage (in-memory)
│   ├── main.py                      # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env                         # Environment variables (not in git)
│   └── .env.example                 # Environment variables template
│
└── frontend/
    ├── src/
    │   ├── assets/                  # Static assets, styles, images
    │   │   ├── demo/                # Demo data (flags, etc.)
    │   │   └── layout/              # Layout styles and variables
    │   ├── components/              # Vue components
    │   │   ├── dashboard/           # Dashboard widgets (Stats, RecentSales, etc.)
    │   │   ├── landing/             # Landing page components (Hero, Features, etc.)
    │   │   └── FloatingConfigurator.vue  # Theme configurator
    │   ├── composables/             # Composition functions (currently empty)
    │   ├── layout/                  # App layout components
    │   │   ├── composables/         # Layout-specific composables
    │   │   ├── AppLayout.vue        # Main layout wrapper
    │   │   ├── AppTopbar.vue        # Top navigation bar
    │   │   ├── AppSidebar.vue       # Sidebar navigation
    │   │   ├── AppMenu.vue          # Main menu
    │   │   ├── AppMenuItem.vue      # Menu item component
    │   │   ├── AppFooter.vue        # Footer component
    │   │   ├── AppConfigurator.vue  # Theme configuration panel
    │   │   └── AppSettings.vue      # Settings management
    │   ├── router/
    │   │   └── index.js             # Router with auth guards
    │   ├── service/                 # Legacy demo services (Country, Customer, Node, Photo, Product)
    │   ├── services/                # API services (current)
    │   │   ├── api.ts               # Axios instance with interceptors
    │   │   ├── authService.ts       # Auth API calls
    │   │   └── tradingService.ts    # Trading API calls
    │   ├── stores/
    │   │   ├── authStore.ts         # Auth state management (Pinia)
    │   │   └── tradingStore.ts      # Trading state management (Pinia)
    │   ├── types/
    │   │   ├── index.ts             # Common types (Trade, Position, etc.)
    │   │   └── auth.ts              # Auth types (User)
    │   ├── views/
    │   │   ├── Dashboard.vue        # Main dashboard with widgets
    │   │   ├── HomeView.vue         # Landing page with login/user info
    │   │   ├── ApiTest.vue          # Protected API testing page
    │   │   ├── pages/               # Utility pages
    │   │   │   ├── auth/            # Auth pages (Login, Register, Access, Error)
    │   │   │   ├── Crud.vue         # CRUD demo page
    │   │   │   ├── Documentation.vue # Documentation page
    │   │   │   ├── Empty.vue        # Empty page template
    │   │   │   ├── Landing.vue      # Marketing landing page
    │   │   │   └── NotFound.vue     # 404 page
    │   │   └── uikit/               # PrimeVue UI component demos
    │   │       ├── ButtonDoc.vue    # Button components demo
    │   │       ├── ChartDoc.vue     # Chart.js integration demo
    │   │       ├── FileDoc.vue      # File upload demo
    │   │       ├── FormLayout.vue   # Form layout examples
    │   │       ├── InputDoc.vue     # Input components demo
    │   │       ├── ListDoc.vue      # List components demo
    │   │       ├── MediaDoc.vue     # Media components demo
    │   │       ├── MenuDoc.vue      # Menu components demo
    │   │       ├── MessagesDoc.vue  # Messages/toast demo
    │   │       ├── MiscDoc.vue      # Misc components demo
    │   │       ├── OverlayDoc.vue   # Overlay components demo
    │   │       ├── PanelsDoc.vue    # Panel components demo
    │   │       ├── TableDoc.vue     # DataTable demo
    │   │       ├── TimelineDoc.vue  # Timeline demo
    │   │       └── TreeDoc.vue      # Tree components demo
    │   ├── App.vue
    │   └── main.ts
    ├── vite.config.ts               # Vite config with proxy
    ├── tsconfig.json                # TypeScript config
    ├── tailwind.config.js           # Tailwind CSS config
    ├── postcss.config.js            # PostCSS config
    ├── package.json
    └── .env.example
```

## Frontend Architecture

### Service Layer
- **API Client** (`services/api.ts`):
  - Axios instance with base URL `/api`
  - Request interceptor: Adds auth token if available
  - Response interceptor: Handles common errors (401, 403, 404, 500)
  - Helper methods: `get`, `post`, `put`, `patch`, `delete`

- **Service Pattern**:
  - `authService.ts`: Authentication operations
  - `tradingService.ts`: Trading operations
  - All services use typed responses

### State Management (Pinia)
- **Trading Store** (`stores/tradingStore.ts`):
  - State: trades, positions, currentTrade, loading, error
  - Pagination: currentPage, pageSize, totalTrades
  - Actions: fetchTrades, createTrade, cancelTrade, fetchPositions, closePosition
  - Computed: totalPages, hasPositions, totalUnrealizedPnL

- **Auth Store** (`stores/authStore.ts`):
  - State: user, loading, error
  - Computed: isAuthenticated
  - Actions: fetchUser, login, logout

### UI Framework
- PrimeVue 4 provides comprehensive component library
- Auto-import resolver for components
- Theme customization via AppConfigurator
- Responsive design with PrimeVue layout system
- Legacy demo services in `src/service/` for UI kit examples

### TypeScript
- Frontend is fully typed with TypeScript
- Type definitions in `src/types/`
- Router is JavaScript (`index.js`) but can be migrated to TypeScript
- Backend uses Pydantic for type validation

## Backend Architecture

### FastAPI Structure
- **Routers**: Modular route handlers for auth, trades, positions
- **Models**: Pydantic models for data validation
- **Dependencies**: Reusable dependency injection (auth)
- **Utils**: Helper functions for auth, mock data generation

### Data Storage
- **In-Memory**: Current implementation uses in-memory storage
- **Mock Users**: `utils/mock_users.py`
- **Mock Trading Data**: `utils/mock_data.py`
- **Future**: Database integration (PostgreSQL/MongoDB)

### Security
- JWT tokens stored in httpOnly cookies (XSS protection)
- Token expiration: 7 days
- CORS configured (environment variable)
- Session middleware for OAuth state management
