const API_URL = 'http://localhost:8000/api/v1';

async function request(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const headers = {
        ...options.headers,
    };

    if (!headers['Content-Type'] && 
        !(options.body instanceof FormData) && 
        !(options.body instanceof URLSearchParams)) {
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers
    };

    const response = await fetch(`${API_URL}${endpoint}`, config);

    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('token');
            // 可以选择重定向到登录页，或者抛出特定错误让调用者处理
            // window.location.href = '/auth/login'; 
        }
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        
        let errorMessage = error.detail || 'Request failed';
        if (Array.isArray(errorMessage)) {
            errorMessage = errorMessage.map((err) => err.msg).join(', ');
        }
        
        throw new Error(errorMessage);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

export const api = {
    get: (endpoint, options) => request(endpoint, { ...options, method: 'GET' }),
    post: (endpoint, body, options) => {
        const isJson = !(body instanceof FormData) && !(body instanceof URLSearchParams);
        return request(endpoint, { 
            ...options, 
            method: 'POST', 
            body: isJson ? JSON.stringify(body) : body 
        });
    },
    put: (endpoint, body, options) => {
        const isJson = !(body instanceof FormData) && !(body instanceof URLSearchParams);
        return request(endpoint, { 
            ...options, 
            method: 'PUT', 
            body: isJson ? JSON.stringify(body) : body 
        });
    },
    patch: (endpoint, body, options) => {
        const isJson = !(body instanceof FormData) && !(body instanceof URLSearchParams);
        return request(endpoint, { 
            ...options, 
            method: 'PATCH', 
            body: isJson ? JSON.stringify(body) : body 
        });
    },
    delete: (endpoint, options) => request(endpoint, { ...options, method: 'DELETE' }),
};
