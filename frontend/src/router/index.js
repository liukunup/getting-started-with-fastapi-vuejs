import AppLayout from '@/layout/AppLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { staticRoutes } from './staticRoutes';

const modules = import.meta.glob('@/views/**/*.vue');

const router = createRouter({
    history: createWebHistory(),
    routes: [...staticRoutes]
});

router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore();
    const publicPages = staticRoutes.map((route) => route.path);
    const authRequired = !publicPages.includes(to.path);

    if (authRequired && !authStore.isAuthenticated) {
        return next('/auth/login');
    }

    if (authStore.isAuthenticated && authStore.menus.length === 0) {
        try {
            await authStore.fetchUserInfo();
            await authStore.fetchMenus();

            const routes = [];
            const generateRoutes = (menus) => {
                menus.forEach((menu) => {
                    if (menu.to && menu.component) {
                        let componentPath = menu.component;
                        if (!componentPath.startsWith('/src/views/')) {
                            if (componentPath.startsWith('@/views/')) {
                                componentPath = componentPath.replace('@/views/', '/src/views/');
                            } else if (componentPath.startsWith('views/')) {
                                componentPath = '/src/' + componentPath;
                            } else {
                                componentPath = '/src/views/' + componentPath;
                            }
                        }

                        if (modules[componentPath]) {
                            let routePath = menu.to;
                            if (routePath === '/') {
                                routePath = '';
                            }
                            routes.push({
                                path: routePath,
                                name: menu.label,
                                component: modules[componentPath]
                            });
                        } else {
                            console.warn(`Component not found: ${componentPath}`);
                        }
                    }
                    if (menu.items && menu.items.length > 0) {
                        generateRoutes(menu.items);
                    }
                });
            };

            generateRoutes(authStore.menus);

            const defaultRoute = routes.find((r) => r.path === '');
            const redirectPath = defaultRoute ? undefined : routes.length > 0 ? routes[0].path : '/pages/empty';

            router.addRoute({
                path: '/',
                component: AppLayout,
                children: [...routes],
                redirect: redirectPath
            });

            router.addRoute({
                path: '/:pathMatch(.*)*',
                redirect: '/pages/notfound'
            });

            return next({ ...to, replace: true });
        } catch (error) {
            console.error('Error generating routes:', error);
            authStore.logout();
            return next('/auth/login');
        }
    }

    next();
});

export default router;
