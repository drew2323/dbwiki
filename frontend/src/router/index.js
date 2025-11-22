import AppLayout from '@/layout/AppLayout.vue';
import AdminLayout from '@/layout/AdminLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        // Public routes (no auth required)
        {
            path: '/',
            name: 'home',
            component: () => import('@/views/pages/Landing.vue')
        },
        {
            path: '/auth/login',
            name: 'login',
            component: () => import('@/views/pages/auth/Login.vue')
        },
        {
            path: '/auth/register',
            name: 'register',
            component: () => import('@/views/pages/auth/Register.vue')
        },
        {
            path: '/auth/access',
            name: 'accessDenied',
            component: () => import('@/views/pages/auth/Access.vue')
        },
        {
            path: '/auth/error',
            name: 'error',
            component: () => import('@/views/pages/auth/Error.vue')
        },
        {
            path: '/pages/notfound',
            name: 'notfound',
            component: () => import('@/views/pages/NotFound.vue')
        },

        // Admin routes (require auth + admin/superuser)
        {
            path: '/admin',
            component: AdminLayout,
            meta: { requiresAuth: true, requiresAdmin: true },
            children: [
                {
                    path: '',
                    redirect: '/admin/dashboard'
                },
                {
                    path: 'dashboard',
                    name: 'admin-dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: 'analytics',
                    name: 'admin-analytics',
                    component: () => import('@/views/Dashboard2.vue')
                },
                {
                    path: 'users',
                    name: 'admin-users',
                    component: () => import('@/views/admin/UserManagement.vue')
                },
                {
                    path: 'spaces',
                    name: 'admin-spaces',
                    component: () => import('@/views/admin/SpaceManagement.vue')
                },
                // Demo/UIKit pages under admin
                {
                    path: 'demo/crud',
                    name: 'admin-demo-crud',
                    component: () => import('@/views/pages/Crud.vue')
                },
                {
                    path: 'demo/empty',
                    name: 'admin-demo-empty',
                    component: () => import('@/views/pages/Empty.vue')
                },
                {
                    path: 'demo/landing',
                    name: 'admin-demo-landing',
                    component: () => import('@/views/pages/Landing.vue')
                },
                // UIKit documentation pages
                {
                    path: 'uikit/formlayout',
                    name: 'admin-uikit-formlayout',
                    component: () => import('@/views/uikit/FormLayout.vue')
                },
                {
                    path: 'uikit/input',
                    name: 'admin-uikit-input',
                    component: () => import('@/views/uikit/InputDoc.vue')
                },
                {
                    path: 'uikit/button',
                    name: 'admin-uikit-button',
                    component: () => import('@/views/uikit/ButtonDoc.vue')
                },
                {
                    path: 'uikit/table',
                    name: 'admin-uikit-table',
                    component: () => import('@/views/uikit/TableDoc.vue')
                },
                {
                    path: 'uikit/list',
                    name: 'admin-uikit-list',
                    component: () => import('@/views/uikit/ListDoc.vue')
                },
                {
                    path: 'uikit/tree',
                    name: 'admin-uikit-tree',
                    component: () => import('@/views/uikit/TreeDoc.vue')
                },
                {
                    path: 'uikit/panel',
                    name: 'admin-uikit-panel',
                    component: () => import('@/views/uikit/PanelsDoc.vue')
                },
                {
                    path: 'uikit/overlay',
                    name: 'admin-uikit-overlay',
                    component: () => import('@/views/uikit/OverlayDoc.vue')
                },
                {
                    path: 'uikit/media',
                    name: 'admin-uikit-media',
                    component: () => import('@/views/uikit/MediaDoc.vue')
                },
                {
                    path: 'uikit/message',
                    name: 'admin-uikit-message',
                    component: () => import('@/views/uikit/MessagesDoc.vue')
                },
                {
                    path: 'uikit/file',
                    name: 'admin-uikit-file',
                    component: () => import('@/views/uikit/FileDoc.vue')
                },
                {
                    path: 'uikit/menu',
                    name: 'admin-uikit-menu',
                    component: () => import('@/views/uikit/MenuDoc.vue')
                },
                {
                    path: 'uikit/charts',
                    name: 'admin-uikit-charts',
                    component: () => import('@/views/uikit/ChartDoc.vue')
                },
                {
                    path: 'uikit/misc',
                    name: 'admin-uikit-misc',
                    component: () => import('@/views/uikit/MiscDoc.vue')
                },
                {
                    path: 'uikit/timeline',
                    name: 'admin-uikit-timeline',
                    component: () => import('@/views/uikit/TimelineDoc.vue')
                },
                {
                    path: 'documentation',
                    name: 'admin-documentation',
                    component: () => import('@/views/pages/Documentation.vue')
                }
            ]
        },

        // Space routes (CMS content)
        {
            path: '/:spaceKey',
            component: () => import('@/views/cms/Space.vue'),
            meta: { requiresAuth: false }, // Public or auth based on space.is_public
            children: [
                {
                    path: '',
                    name: 'space-home',
                    component: () => import('@/views/cms/SpaceHome.vue')
                },
                {
                    path: 'p/:pageIdSlug',
                    name: 'page-view',
                    component: () => import('@/views/cms/PageView.vue')
                }
            ]
        },

        // Catch-all 404
        {
            path: '/:pathMatch(.*)*',
            redirect: '/pages/notfound'
        }
    ]
});

// Navigation guard for auth and admin access
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore();

    // Check if route requires authentication
    if (to.meta.requiresAuth) {
        // Wait for initial auth check to complete
        if (!authStore.initialized) {
            await authStore.fetchUser();
        }

        // Redirect to login if not authenticated
        if (!authStore.isAuthenticated) {
            next({ name: 'login', query: { redirect: to.fullPath } });
            return;
        }

        // Check if route requires admin access
        if (to.meta.requiresAdmin) {
            // Check if user is superuser or has admin role
            if (!authStore.user?.is_superuser) {
                // TODO: Add check for admin role in any space
                // For now, only allow superusers to access admin
                next({ name: 'accessDenied' });
                return;
            }
        }
    }

    next();
});

export default router;
