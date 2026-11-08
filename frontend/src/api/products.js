import apiClient from './client';

export const productsApi = {
  async getProducts(params = {}) {
    const query = new URLSearchParams();
    if (params.category) query.set('category', params.category);
    if (params.brand) query.set('brand', params.brand);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.skip !== undefined) query.set('skip', params.skip);
    if (params.limit !== undefined) query.set('limit', params.limit);

    const queryString = query.toString();
    return apiClient(`/api/products${queryString ? `?${queryString}` : ''}`);
  },

  async searchProducts(q) {
    const query = new URLSearchParams({ q });
    return apiClient(`/api/products/search?${query.toString()}`);
  },

  async getProduct(id) {
    return apiClient(`/api/products/${id}`);
  },

  async getOffers(productId, params = {}) {
    const query = new URLSearchParams();
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.retailer) query.set('retailer', params.retailer);

    const queryString = query.toString();
    return apiClient(`/api/products/${productId}/offers${queryString ? `?${queryString}` : ''}`);
  },
};
