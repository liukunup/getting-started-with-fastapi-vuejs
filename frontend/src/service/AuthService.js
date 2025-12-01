import { api } from './api';

export const AuthService = {
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        return api.post('/login/access-token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
    },

    async register(email, password, fullName) {
        return api.post('/login/register', {
            email: email,
            password: password,
            full_name: fullName
        });
    },

    async forgotPassword(email) {
        return api.post(`/login/password-recovery/${email}`);
    },

    async resetPassword(token, newPassword) {
        return api.post('/login/reset-password/', {
            token: token,
            new_password: newPassword
        });
    }
};
