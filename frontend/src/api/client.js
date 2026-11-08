// Centralized API Client for SmartCart AI
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function apiClient(endpoint, options = {}) {
  const token = localStorage.getItem('smartcart_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Check for 401 Unauthorized / Token Revocation
    if (response.status === 401) {
      if (token) {
        localStorage.removeItem('smartcart_token');
        localStorage.removeItem('smartcart_user');
        window.dispatchEvent(new Event('smartcart:auth_invalidated'));
      }
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = data?.detail || data?.message || `HTTP ${response.status}: ${response.statusText}`;
      const error = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Could not connect to SmartCart backend API server. Please ensure the backend is running at ' + API_BASE);
    }
    throw error;
  }
}

export default apiClient;
