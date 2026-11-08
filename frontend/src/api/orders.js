import apiClient from './client';

export const ordersApi = {
  async createOrder({ items, shipping_address, idempotency_key }) {
    const payload = {
      items,
      shipping_address,
    };
    if (idempotency_key) {
      payload.idempotency_key = idempotency_key;
    }

    return apiClient('/api/orders', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getOrders() {
    return apiClient('/api/orders');
  },

  async getOrder(id) {
    return apiClient(`/api/orders/${id}`);
  },

  async createPayPalOrder(orderId) {
    return apiClient(`/api/orders/${orderId}/paypal/create`, {
      method: 'POST',
    });
  },

  async capturePayPalOrder(orderId) {
    return apiClient(`/api/orders/${orderId}/paypal/capture`, {
      method: 'POST',
    });
  },
};
