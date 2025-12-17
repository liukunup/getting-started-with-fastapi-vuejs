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

/**
 * 格式化日期时间
 * @param {string|Date} value - 日期时间字符串或对象
 * @returns {string} - 格式化后的日期时间字符串
 */
export const formatDateTime = (value) => {
    if (!value) return '';
    const date = value instanceof Date ? value : new Date(value);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
};
