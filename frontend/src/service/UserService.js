import { api } from './api';

export const UserService = {
    async getMe() {
        return api.get('/users/me');
    },

    async getUsers() {
        return api.get('/users/');
    },

    async createUser(user) {
        return api.post('/users/', user);
    },

    async updateUser(id, user) {
        return api.patch(`/users/${id}`, user);
    },

    async deleteUser(id) {
        return api.delete(`/users/${id}`);
    }
};
