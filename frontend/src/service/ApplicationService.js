import { api } from './api';

export const ApplicationService = {
    async getApplications() {
        return api.get('/applications/');
    },

    async createApplication(application) {
        return api.post('/applications/', application);
    },

    async updateApplication(id, application) {
        return api.put(`/applications/${id}`, application);
    },

    async deleteApplication(id) {
        return api.delete(`/applications/${id}`);
    }
};
