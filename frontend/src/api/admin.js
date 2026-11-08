import apiClient from './client';

export const adminApi = {
  async getDashboard() {
    return apiClient('/api/admin/dashboard');
  },

  async createProduct(productData) {
    return apiClient('/api/admin/products', {
      method: 'POST',
      body: JSON.stringify(productData),
    });
  },

  async updateProduct(id, productData) {
    return apiClient(`/api/admin/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(productData),
    });
  },

  async toggleProductStatus(id, isActive) {
    return apiClient(`/api/admin/products/${id}/status?is_active=${isActive}`, {
      method: 'PATCH',
    });
  },

  async createOffer(productId, offerData) {
    return apiClient(`/api/admin/products/${productId}/offers`, {
      method: 'POST',
      body: JSON.stringify(offerData),
    });
  },

  async updateOffer(id, offerData) {
    return apiClient(`/api/admin/offers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(offerData),
    });
  },

  async toggleOfferStatus(id, isActive) {
    return apiClient(`/api/admin/offers/${id}/status?is_active=${isActive}`, {
      method: 'PATCH',
    });
  },
};
