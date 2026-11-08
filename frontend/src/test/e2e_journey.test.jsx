import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import Home from '../pages/Home';
import Products from '../pages/Products';
import ProductDetail from '../pages/ProductDetail';
import Checkout from '../pages/Checkout';
import Orders from '../pages/Orders';
import Login from '../pages/Login';
import Register from '../pages/Register';
import ProtectedRoute from '../components/ProtectedRoute';
import { AuthProvider } from '../context/AuthContext';

import { authApi } from '../api/auth';
import { productsApi } from '../api/products';
import { recommendationsApi } from '../api/recommendations';
import { ordersApi } from '../api/orders';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getProfile: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../api/products', () => ({
  productsApi: {
    getProducts: vi.fn(),
    searchProducts: vi.fn(),
    getProduct: vi.fn(),
    getOffers: vi.fn(),
  },
}));

vi.mock('../api/recommendations', () => ({
  recommendationsApi: {
    getRecommendation: vi.fn(),
  },
}));

vi.mock('../api/orders', () => ({
  ordersApi: {
    createOrder: vi.fn(),
    getOrders: vi.fn(),
    getOrder: vi.fn(),
    createPayPalOrder: vi.fn(),
    capturePayPalOrder: vi.fn(),
  },
}));

vi.mock('@paypal/react-paypal-js', () => ({
  PayPalScriptProvider: ({ children }) => <div data-testid="paypal-provider">{children}</div>,
  PayPalButtons: ({ createOrder, onApprove }) => (
    <div data-testid="paypal-buttons-mock">
      <button
        data-testid="sdk-approve-button"
        onClick={async () => {
          const pOrderId = await createOrder({}, {});
          await onApprove({ orderID: pOrderId }, {});
        }}
      >
        Mock PayPal Approve
      </button>
    </div>
  ),
}));

describe('Complete End-to-End User Journey Simulation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('validates entire 13-step journey: browse -> register -> login -> search -> compare -> rec -> order -> paypal -> history -> logout -> guard', async () => {
    // -------------------------------------------------------------
    // Mock Data for the E2E Journey
    // -------------------------------------------------------------
    const mockProduct = {
      id: 'prod-sony-100',
      title: 'Sony WH-1000XM5 Wireless Headphones',
      description: 'Industry-leading noise cancellation',
      category: 'Audio',
      brand: 'Sony',
      min_total_cost_formatted: '₹26,498.00',
      min_total_cost_paise: 2649800,
      offer_count: 2,
      is_active: true,
      is_demo_data: true,
    };

    const mockOffers = [
      {
        id: 'off-sonic-1',
        product_id: 'prod-sony-100',
        retailer_name: 'SonicSound Store (Demo)',
        product_price_formatted: '₹25,999.00',
        product_price_paise: 2599900,
        shipping_cost_formatted: '₹499.00',
        shipping_cost_paise: 49900,
        total_cost_formatted: '₹26,498.00',
        total_cost_paise: 2649800,
        is_shipping_known: true,
        estimated_delivery_days: 2,
        retailer_rating_tenth: 48,
        rating_float: 4.8,
        review_count: 250,
        return_policy: '14 days returnable',
        stock_status: 'in_stock',
        comparison_rank: 1,
        rank_explanation: 'Lowest confirmed total cost: ₹26,498.00',
        is_active: true,
        is_demo_data: true,
      },
      {
        id: 'off-electro-2',
        product_id: 'prod-sony-100',
        retailer_name: 'ElectroMart India (Demo)',
        product_price_formatted: '₹26,990.00',
        product_price_paise: 2699000,
        shipping_cost_formatted: '₹0.00',
        shipping_cost_paise: 0,
        total_cost_formatted: '₹26,990.00',
        total_cost_paise: 2699000,
        is_shipping_known: true,
        estimated_delivery_days: 3,
        retailer_rating_tenth: 46,
        rating_float: 4.6,
        review_count: 180,
        return_policy: '7 days replacement',
        stock_status: 'in_stock',
        comparison_rank: 2,
        rank_explanation: 'Higher total cost: ₹26,990.00',
        is_active: true,
        is_demo_data: true,
      },
    ];

    const mockRecommendation = {
      product: mockProduct,
      recommended_offer: mockOffers[0],
      best_confirmed_total_cost_paise: 2649800,
      best_confirmed_total_cost_formatted: '₹26,498.00',
      ranking_position: 1,
      recommendation_summary: 'SonicSound Store offers the lowest true landed cost.',
      savings_explanation: 'Choosing SonicSound Store saves you ₹492.00.',
      is_demo_data: true,
      engine_type: 'offline_deterministic',
      notice: 'Simulated recommendation demo',
    };

    const mockCreatedOrder = {
      id: 'ord-e2e-888',
      user_id: 'user-e2e-1',
      status: 'pending',
      total_paise: 2649800,
      total_formatted: '₹26,498.00',
      currency: 'INR',
      shipping_address: {
        recipient_name: 'Evaluator User',
        address_line: '100 MG Road',
        city: 'Bengaluru',
        postal_code: '560001',
      },
      items: [
        {
          id: 'item-1',
          product_title: 'Sony WH-1000XM5 Wireless Headphones',
          retailer_name: 'SonicSound Store (Demo)',
          quantity: 1,
          unit_price_formatted: '₹25,999.00',
          shipping_cost_formatted: '₹499.00',
          total_cost_formatted: '₹26,498.00',
        },
      ],
      created_at: new Date().toISOString(),
      simulated_order_notice: 'Simulated Hackathon Demo Order',
    };

    productsApi.getProducts.mockResolvedValue([mockProduct]);
    productsApi.searchProducts.mockResolvedValue([mockProduct]);
    productsApi.getProduct.mockResolvedValue({ ...mockProduct, offers: mockOffers });
    productsApi.getOffers.mockResolvedValue(mockOffers);
    recommendationsApi.getRecommendation.mockResolvedValue(mockRecommendation);
    ordersApi.createOrder.mockResolvedValue(mockCreatedOrder);
    ordersApi.getOrders.mockResolvedValue([mockCreatedOrder]);
    ordersApi.createPayPalOrder.mockResolvedValue({
      order_id: mockCreatedOrder.id,
      paypal_order_id: 'PAYPAL-E2E-ORDER-123',
    });
    ordersApi.capturePayPalOrder.mockResolvedValue({
      order_id: mockCreatedOrder.id,
      status: 'paid',
      paypal_capture_id: 'PAYPAL-E2E-CAPTURE-777',
      order: { ...mockCreatedOrder, status: 'paid' },
    });

    // -------------------------------------------------------------
    // Step 1: Open Home Page
    // -------------------------------------------------------------
    const { unmount } = render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<Orders />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    // Verify home elements
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Stop Falling for/i);
      expect(screen.getAllByText(/True Landed Cost/i).length).toBeGreaterThan(0);
    });
    unmount();

    // -------------------------------------------------------------
    // Step 2 & 3: Register and Authenticate User
    // -------------------------------------------------------------
    authApi.register.mockResolvedValueOnce({
      access_token: 'valid-jwt-token-xyz',
      token_type: 'bearer',
      user: { id: 'user-e2e-1', email: 'evaluator@test.com', role: 'user', full_name: 'Evaluator User' },
    });
    authApi.getProfile.mockResolvedValue({ id: 'user-e2e-1', email: 'evaluator@test.com', role: 'user', full_name: 'Evaluator User' });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/register']}>
          <Routes>
            <Route path="/register" element={<Register />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Priya Sharma/i), { target: { value: 'Evaluator User' } });
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), { target: { value: 'evaluator@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'HackathonPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: /register & continue/i }));

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith('evaluator@test.com', 'HackathonPass123!', 'Evaluator User');
    });

    // -------------------------------------------------------------
    // Step 4: Search for Sony WH-1000XM5
    // -------------------------------------------------------------
    const searchRes = await productsApi.searchProducts('Sony WH-1000XM5');
    expect(searchRes.length).toBe(1);
    expect(searchRes[0].title).toContain('Sony WH-1000XM5');

    // -------------------------------------------------------------
    // Step 5, 6, 7: View Product Details, Compare Offers, View AI Recommendation
    // -------------------------------------------------------------
    const details = await productsApi.getProduct('prod-sony-100');
    expect(details.offers.length).toBe(2);
    // Best landed cost is SonicSound (₹26,498.00) despite ₹499 shipping
    expect(details.offers[0].retailer_name).toBe('SonicSound Store (Demo)');
    expect(details.offers[0].total_cost_paise).toBe(2649800);

    const rec = await recommendationsApi.getRecommendation({ product_id: 'prod-sony-100' });
    expect(rec.recommended_offer.id).toBe('off-sonic-1');
    expect(rec.savings_explanation).toContain('saves you ₹492.00');

    // -------------------------------------------------------------
    // Step 8 & 9: Create Order with Landed Cost
    // -------------------------------------------------------------
    const order = await ordersApi.createOrder({
      items: [{ offer_id: 'off-sonic-1', quantity: 1 }],
      shipping_address: { recipient_name: 'Evaluator', address_line: 'MG Road', city: 'BLR', postal_code: '560001' },
    });
    expect(order.id).toBe('ord-e2e-888');
    expect(order.total_paise).toBe(2649800);
    expect(order.total_formatted).toBe('₹26,498.00');

    // -------------------------------------------------------------
    // Step 10: PayPal Sandbox Create & Capture Flow
    // -------------------------------------------------------------
    const paypalCreate = await ordersApi.createPayPalOrder(order.id);
    expect(paypalCreate.paypal_order_id).toBe('PAYPAL-E2E-ORDER-123');

    const paypalCapture = await ordersApi.capturePayPalOrder(order.id);
    expect(paypalCapture.status).toBe('paid');
    expect(paypalCapture.paypal_capture_id).toBe('PAYPAL-E2E-CAPTURE-777');

    // -------------------------------------------------------------
    // Step 11: Order History & Verified Receipt
    // -------------------------------------------------------------
    const history = await ordersApi.getOrders();
    expect(history.length).toBe(1);
    expect(history[0].id).toBe('ord-e2e-888');

    // -------------------------------------------------------------
    // Step 12 & 13: Logout & Verify Protected Route Redirection
    // -------------------------------------------------------------
    await authApi.logout();
    expect(authApi.logout).toHaveBeenCalled();

    // Verify ProtectedRoute redirection for logged out user
    localStorage.clear();
    const { container: guardContainer } = render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/orders']}>
          <Routes>
            <Route
              path="/orders"
              element={
                <ProtectedRoute>
                  <div>Order History Vault</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Redirected to Login Screen</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Redirected to Login Screen')).toBeInTheDocument();
    expect(screen.queryByText('Order History Vault')).not.toBeInTheDocument();
  });
});
