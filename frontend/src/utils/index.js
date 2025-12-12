import { OpenAPI } from '@/client';

const DEFAULT_AVATAR = 'https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png';

/**
 * 获取头像的完整 URL
 * @param {string} url - 头像的相对路径或绝对 URL
 * @returns {string} - 完整的头像 URL
 */
export const getAvatarUrl = (url) => {
    if (!url) return DEFAULT_AVATAR;
    if (url.startsWith('http') || url.startsWith('https')) return url;
    return `${OpenAPI.BASE}${url}`;
};
