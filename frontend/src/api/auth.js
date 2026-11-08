import apiClient from './client';

export const authApi = {
  async register(email, password, full_name) {
    return apiClient('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
  },

  async login(email, password) {
    return apiClient('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async getProfile() {
    return apiClient('/api/auth/me');
  },

  async logout() {
    try {
      return await apiClient('/api/auth/logout', {
        method: 'POST',
      });
    } catch {
      // Even if network fails, client-side cleanup will proceed
      return { message: 'Logged out locally' };
    }
  },
};
