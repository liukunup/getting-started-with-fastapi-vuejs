import { createApp } from 'vue';
import { createPinia } from 'pinia';
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
OpenAPI.BASE = import.meta.env.VITE_API_URL;
OpenAPI.TOKEN = async () => {
    return localStorage.getItem('token') || '';
};

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

// 配置 OpenAPI 客户端
OpenAPI.BASE = import.meta.env.VITE_API_URL;
OpenAPI.TOKEN = async () => {
    return localStorage.getItem('token') || '';
};

OpenAPI.interceptors.response.use(async (response) => {
    if (response.status === 401) {
        const authStore = useAuthStore();
        authStore.logout();
        router.push('/auth/login');
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
