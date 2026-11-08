import apiClient from './client';

export const recommendationsApi = {
  async getRecommendation({ product_id, query }) {
    const payload = {};
    if (product_id) payload.product_id = product_id;
    if (query) payload.query = query;

    return apiClient('/api/recommendations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
