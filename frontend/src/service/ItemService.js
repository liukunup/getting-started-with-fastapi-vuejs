import { api } from './api';

export const ItemService = {
    async getItems() {
        return api.get('/items/');
    },

    async createItem(item) {
        return api.post('/items/', item);
    },

    async updateItem(id, item) {
        return api.put(`/items/${id}`, item);
    },

    async deleteItem(id) {
        return api.delete(`/items/${id}`);
    }
};
