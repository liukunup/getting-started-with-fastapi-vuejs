import { createApp } from 'vue';
import { createPinia } from 'pinia';
import axios from 'axios';
import App from './App.vue';
import router from './router';
import { OpenAPI } from './client';
import { useAuthStore } from '@/store/auth';

import Aura from '@primeuix/themes/aura';
import PrimeVue from 'primevue/config';
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';
import Tooltip from 'primevue/tooltip';

import '@/assets/tailwind.css';
import '@/assets/styles.scss';

// 配置 OpenAPI 客户端
OpenAPI.BASE = import.meta.env.VITE_API_URL || '';
OpenAPI.TOKEN = async () => {
    return localStorage.getItem('accessToken') || '';
};

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

// OpenAPI interceptor for token refresh
OpenAPI.interceptors.response.use(async (response) => {
    if (response.status === 401) {
        const originalRequest = response.config;
        if (!originalRequest._retry) {
            originalRequest._retry = true;
            const authStore = useAuthStore();
            const refreshToken = authStore.refreshToken;

            if (refreshToken) {
                try {
                    const refreshResponse = await axios.post(
                        `${OpenAPI.BASE}/api/v1/login/refresh-token?refresh_token=${refreshToken}`
                    );

                    const { access_token, refresh_token } = refreshResponse.data;

                    authStore.accessToken = access_token;
                    authStore.refreshToken = refresh_token;
                    localStorage.setItem('accessToken', access_token);
                    localStorage.setItem('refreshToken', refresh_token);

                    // Update header for original request
                    originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

                    // Retry original request
                    return axios.request(originalRequest);
                } catch (e) {
                    // Only logout if refresh token fails
                    if (e.config && e.config.url && e.config.url.includes('refresh-token')) {
                        authStore.logout();
                        router.push('/auth/login');
                    }
                    throw e;
                }
            } else {
                authStore.logout();
                router.push('/auth/login');
            }
        }
    }
    return response;
});

app.use(router);
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.app-dark'
        }
    }
});
app.use(ToastService);
app.use(ConfirmationService);
app.directive('tooltip', Tooltip);

app.mount('#app');
