import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AdminDashboard from '../pages/AdminDashboard';
import { adminApi } from '../api/admin';
import { productsApi } from '../api/products';
import { apiClient } from '../api/client';

vi.mock('../api/admin', () => ({
  adminApi: {
    getDashboard: vi.fn(),
    toggleProductStatus: vi.fn(),
    createProduct: vi.fn(),
    updateProduct: vi.fn(),
    toggleOfferStatus: vi.fn(),
    createOffer: vi.fn(),
    updateOffer: vi.fn(),
  },
}));

vi.mock('../api/products', () => ({
  productsApi: {
    getProducts: vi.fn(),
    getOffers: vi.fn(),
  },
}));

describe('API Client & Admin Dashboard Verification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('API client catches 401, clears localStorage tokens and emits invalidation event', async () => {
    localStorage.setItem('smartcart_token', 'expired-token');
    localStorage.setItem('smartcart_user', JSON.stringify({ email: 'user@example.com' }));

    const eventSpy = vi.fn();
    window.addEventListener('smartcart:auth_invalidated', eventSpy);

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Token has been revoked.' }),
    });

    await expect(apiClient('/api/auth/me')).rejects.toThrow('Token has been revoked.');

    expect(localStorage.getItem('smartcart_token')).toBeNull();
    expect(localStorage.getItem('smartcart_user')).toBeNull();
    expect(eventSpy).toHaveBeenCalled();

    window.removeEventListener('smartcart:auth_invalidated', eventSpy);
  });

  it('Admin dashboard never displays undefined KPI values when backend returns standard dashboard response', async () => {
    // Standard backend dashboard response from Phase 2
    adminApi.getDashboard.mockResolvedValueOnce({
      status: 'success',
      message: 'Admin dashboard access granted.',
      admin: {
        id: 'adm-1',
        email: 'admin@smartcart.local',
        full_name: 'Lead Admin',
        role: 'admin',
      },
    });

    // Real product catalogue data
    productsApi.getProducts.mockResolvedValueOnce([
      { id: 'p1', title: 'Test ANC Headphones', brand: 'Sony', category: 'Audio', is_active: true, offer_count: 3 },
      { id: 'p2', title: 'Fitness Smart Watch', brand: 'Garmin', category: 'Wearables', is_active: false, offer_count: 2 },
    ]);
    productsApi.getOffers.mockResolvedValueOnce([]);

    const { container } = render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Total Retailer Offers')).toBeInTheDocument();
    });

    // Verify accurate KPI values derived from actual products data
    expect(container.textContent).toContain('Catalogue Products');
    expect(container.textContent).toContain('(1 active)');
    expect(container.textContent).toContain('Total Retailer Offers');
    expect(container.textContent).toContain('5');
    expect(container.textContent).toContain('admin@smartcart.local');
    expect(container.textContent).toContain('Role: admin');
    expect(container.textContent).toContain('Operational');

    // Verify container HTML never contains "undefined"
    expect(container.textContent).not.toContain('undefined');
  });
});
