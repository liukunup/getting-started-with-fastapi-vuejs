import { OpenAPI } from '@/client';

export const MenuService = {
    async getMenus() {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // OpenAPI.BASE might be empty string if relative, or full URL.
        // If it's not set, we assume relative to current origin but with /api/v1 prefix usually handled by proxy or base url.
        // However, looking at Login.vue: window.location.href = `${OpenAPI.BASE}/api/v1/login/oidc`;
        // So OpenAPI.BASE is the backend host.
        
        const baseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || '';
        const url = `${baseUrl}/api/v1/users/me/menu`;

        const response = await fetch(url, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Failed to fetch menus');
        }

        return await response.json();
    }
};
