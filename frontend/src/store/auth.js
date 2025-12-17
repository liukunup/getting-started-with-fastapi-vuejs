import { defineStore } from 'pinia';
import { LoginService, UserService } from '@/client';
import { staticMenu } from '@/layout/staticMenu';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: null,
        menus: []
    }),
    getters: {
        isAuthenticated: (state) => !!state.token
    },
    actions: {
        async login(username, password) {
            try {
                const response = await LoginService.loginAccessToken({
                    formData: {
                        username: username,
                        password: password
                    }
                });
                this.token = response.access_token;
                localStorage.setItem('token', this.token);
                return true;
            } catch (error) {
                console.error('Login failed:', error);
                throw error;
            }
        },
        async fetchUserInfo() {
            try {
                const user = await UserService.readUserMe();
                this.user = user;
            } catch (error) {
                console.error('Fetch user info failed:', error);
                throw error;
            }
        },
        async fetchMenus() {
            try {
                const menus = await UserService.readUserMenu();
                const mapMenu = (menu) => ({
                    ...menu,
                    visible: !menu.is_hidden,
                    items: menu.items ? menu.items.map(mapMenu) : undefined
                });
                this.menus = [...staticMenu, ...menus.map(mapMenu)];
            } catch (error) {
                console.error('Fetch menus failed:', error);
                this.menus = [...staticMenu];
                throw error;
            }
        },
        logout() {
            this.token = '';
            this.user = null;
            this.menus = [];
            localStorage.removeItem('token');
        }
    }
});
