import { api } from './api';

export const GroupService = {
    async getGroups() {
        return api.get('/groups/');
    },

    async createGroup(group) {
        return api.post('/groups/', group);
    },

    async updateGroup(id, group) {
        return api.put(`/groups/${id}`, group);
    },

    async deleteGroup(id) {
        return api.delete(`/groups/${id}`);
    }
};
