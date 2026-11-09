import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import AICopilotBar from '../components/AICopilotBar';
import Products from '../pages/Products';
import { copilotApi } from '../api/copilot';
import { productsApi } from '../api/products';

vi.mock('../api/copilot', () => ({
  copilotApi: {
    query: vi.fn(),
  },
}));

vi.mock('../api/products', () => ({
  productsApi: {
    getProducts: vi.fn(),
    searchProducts: vi.fn(),
  },
}));

describe('AI Shopping Copilot Frontend Component & Page Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    productsApi.getProducts.mockResolvedValue([
      {
        id: 'p1',
        title: 'Sony WH-1000XM5 Wireless Headphones',
        category: 'Audio',
        brand: 'Sony',
        min_total_cost_formatted: '₹26,498.00',
        min_total_cost_paise: 2649800,
        offer_count: 3,
        is_demo_data: true,
      },
    ]);
  });

  it('renders AICopilotBar with input, submit button, and prompt suggestion chips', () => {
    render(
      <MemoryRouter>
        <AICopilotBar onSearch={vi.fn()} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText(/AI Shopping Copilot/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Sony WH-1000XM5 headphones under ₹28,000/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ask Copilot/i })).toBeInTheDocument();
    expect(screen.getByText('Sony WH-1000XM5 under ₹28,000')).toBeInTheDocument();
  });

  it('submits natural language query on form submission', () => {
    const handleSearch = vi.fn();
    render(
      <MemoryRouter>
        <AICopilotBar onSearch={handleSearch} onReset={vi.fn()} />
      </MemoryRouter>
    );

    const input = screen.getByPlaceholderText(/Sony WH-1000XM5 headphones under ₹28,000/i);
    const submitBtn = screen.getByRole('button', { name: /Ask Copilot/i });

    fireEvent.change(input, { target: { value: 'noise cancelling headphones under 25k' } });
    fireEvent.click(submitBtn);

    expect(handleSearch).toHaveBeenCalledWith('noise cancelling headphones under 25k');
  });

  it('clicking a prompt chip triggers immediate search', () => {
    const handleSearch = vi.fn();
    render(
      <MemoryRouter>
        <AICopilotBar onSearch={handleSearch} onReset={vi.fn()} />
      </MemoryRouter>
    );

    const chip = screen.getByText('Sony WH-1000XM5 under ₹28,000');
    fireEvent.click(chip);

    expect(handleSearch).toHaveBeenCalledWith('Sony WH-1000XM5 under ₹28,000');
  });

  it('displays loading indicator and disables submit button when loading', () => {
    render(
      <MemoryRouter>
        <AICopilotBar onSearch={vi.fn()} onReset={vi.fn()} loading={true} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument();
    const button = screen.getByRole('button', { name: /Analyzing.../i });
    expect(button).toBeDisabled();
  });

  it('renders error message when error prop is supplied', () => {
    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          error="Rate limit exceeded. Maximum 15 inquiries per minute."
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/Rate limit exceeded/i)).toBeInTheDocument();
  });

  it('renders extracted intent criteria, Gemini mode badge, and top recommendation card', () => {
    const sampleCopilotData = {
      query_message: 'Sony headphones under 28k',
      copilot_mode: 'gemini_ai',
      extracted_intent: {
        search_query: 'Sony headphones',
        category: 'Audio',
        brand: 'Sony',
        max_budget_rupees: 28000,
        key_features: ['noise cancelling', 'wireless'],
      },
      matched_products_count: 1,
      matched_products: [
        {
          id: 'prod-sony',
          title: 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
          category: 'Audio',
          brand: 'Sony',
          min_total_cost_formatted: '₹26,498.00',
          min_total_cost_paise: 2649800,
          offer_count: 3,
          is_demo_data: true,
        },
      ],
      top_recommendation: {
        product_id: 'prod-sony',
        product_title: 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
        offer_id: 'off-sonicsound',
        recommended_retailer: 'SonicSound Store (Demo)',
        product_price_formatted: '₹25,999.00',
        shipping_cost_formatted: '₹499.00',
        landed_cost_formatted: '₹26,498.00',
        landed_cost_paise: 2649800,
        savings_explanation: 'Choosing SonicSound Store (Demo) saves you ₹492.00',
        delivery_days: 4,
        retailer_rating: 4.4,
        review_count: 310,
        is_shipping_known: true,
        is_demo_data: true,
      },
      explanation: 'SmartCart AI matched Sony WH-1000XM5 within your ₹28,000 budget.',
      is_demo_data: true,
    };

    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          copilotData={sampleCopilotData}
        />
      </MemoryRouter>
    );

    // Mode badge
    expect(screen.getByText(/Gemini 3.8 Flash/i)).toBeInTheDocument();

    // Extracted intent tags
    expect(screen.getByText('Sony headphones')).toBeInTheDocument();
    expect(screen.getByText(/Category: Audio/i)).toBeInTheDocument();
    expect(screen.getByText(/Brand: Sony/i)).toBeInTheDocument();
    expect(screen.getByText(/Budget Cap: ₹28,000/i)).toBeInTheDocument();
    expect(screen.getByText('noise cancelling')).toBeInTheDocument();

    // Top recommendation card
    expect(screen.getByText(/AI Best Value — True Landed Cost/i)).toBeInTheDocument();
    expect(screen.getByText('SonicSound Store (Demo)')).toBeInTheDocument();
    expect(screen.getByText('₹26,498.00')).toBeInTheDocument();
    expect(screen.getByText(/saves you ₹492.00/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Select for Checkout/i })).toBeInTheDocument();
  });

  it('renders deterministic local engine badge when copilot_mode is fallback', () => {
    const fallbackData = {
      query_message: 'Sony headphones under 28k',
      copilot_mode: 'fallback_no_key',
      extracted_intent: {
        search_query: 'Sony headphones',
        category: 'Audio',
        brand: 'Sony',
        max_budget_rupees: 28000,
        key_features: [],
      },
      matched_products_count: 1,
      matched_products: [],
      top_recommendation: null,
      explanation: 'Operating via deterministic local fallback.',
      is_demo_data: true,
    };

    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          copilotData={fallbackData}
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/Deterministic Local Engine/i)).toBeInTheDocument();
  });

  it('integrates with Products page and displays AI matched products', async () => {
    copilotApi.query.mockResolvedValueOnce({
      query_message: 'Sony headphones under 28k',
      copilot_mode: 'gemini_ai',
      extracted_intent: {
        search_query: 'Sony headphones',
        category: 'Audio',
        brand: 'Sony',
        max_budget_rupees: 28000,
        key_features: ['noise cancelling'],
      },
      matched_products_count: 1,
      matched_products: [
        {
          id: 'prod-sony',
          title: 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
          description: 'Industry-leading noise cancellation',
          category: 'Audio',
          brand: 'Sony',
          min_total_cost_formatted: '₹26,498.00',
          min_total_cost_paise: 2649800,
          offer_count: 3,
          is_demo_data: true,
        },
      ],
      top_recommendation: null,
      explanation: 'Matched Sony WH-1000XM5.',
      is_demo_data: true,
    });

    render(
      <MemoryRouter initialEntries={['/products']}>
        <Products />
      </MemoryRouter>
    );

    // Initial catalogue loaded
    await waitFor(() => {
      expect(screen.getByText('Simulated Product Catalogue')).toBeInTheDocument();
    });

    // Enter copilot search
    const input = screen.getByPlaceholderText(/Sony WH-1000XM5 headphones under ₹28,000/i);
    const submitBtn = screen.getByRole('button', { name: /Ask Copilot/i });

    fireEvent.change(input, { target: { value: 'Sony headphones under 28k' } });
    fireEvent.click(submitBtn);

    // Wait for copilot response
    await waitFor(() => {
      expect(copilotApi.query).toHaveBeenCalledWith('Sony headphones under 28k');
      expect(screen.getByText(/AI matched catalogue product/i)).toBeInTheDocument();
    });
  });

  it('omits AI Best Value recommendation card and checkout action when top_recommendation is null', () => {
    const dataWithoutRecommendation = {
      query_message: 'Sony headphones under 20k',
      copilot_mode: 'gemini_ai',
      extracted_intent: {
        search_query: 'Sony headphones',
        category: 'Audio',
        brand: 'Sony',
        max_budget_rupees: 20000,
        key_features: [],
      },
      matched_products_count: 0,
      matched_products: [],
      top_recommendation: null,
      explanation: 'No confirmed active offers are currently available under your ₹20,000 budget.',
      is_demo_data: true,
      notice: 'All product prices, shipping rates, and retailer offers are simulated demo data.',
    };

    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          copilotData={dataWithoutRecommendation}
        />
      </MemoryRouter>
    );

    // Recommendation card and CTA must NOT be rendered
    expect(screen.queryByText(/AI Best Value — True Landed Cost/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Select for Checkout/i })).not.toBeInTheDocument();
    expect(screen.getByText(/No confirmed active offers are currently available/i)).toBeInTheDocument();
  });

  it('handles unknown shipping cost without representing it as free delivery or confirmed landed cost', () => {
    const unknownShippingData = {
      query_message: 'Mystery Soundbar',
      copilot_mode: 'fallback_no_key',
      extracted_intent: {
        search_query: 'Mystery Soundbar',
        category: 'Audio',
        brand: 'Sony',
        max_budget_rupees: null,
        key_features: [],
      },
      matched_products_count: 1,
      matched_products: [],
      top_recommendation: {
        product_id: 'prod-mystery',
        product_title: 'Mystery Soundbar',
        offer_id: 'off-unknown',
        recommended_retailer: 'Unknown Shipping Store (Demo)',
        product_price_formatted: '₹5,000.00',
        shipping_cost_formatted: 'Unknown / Unconfirmed',
        landed_cost_formatted: 'Incomplete (Unknown Shipping)',
        landed_cost_paise: 500000,
        savings_explanation: null,
        delivery_days: 5,
        retailer_rating: 4.0,
        review_count: 50,
        is_shipping_known: false,
        is_demo_data: true,
      },
      explanation: 'Matched Mystery Soundbar with unconfirmed shipping.',
      is_demo_data: true,
      notice: 'All product prices, shipping rates, and retailer offers are simulated demo data.',
    };

    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          copilotData={unknownShippingData}
        />
      </MemoryRouter>
    );

    // Must NOT state FREE Delivery
    expect(screen.queryByText(/FREE Delivery/i)).not.toBeInTheDocument();
    // Must display Unconfirmed Shipping & Unconfirmed / Incomplete
    expect(screen.getByText('Unconfirmed Shipping')).toBeInTheDocument();
    expect(screen.getByText(/Unconfirmed \/ Incomplete/i)).toBeInTheDocument();
    expect(screen.getByText('Simulated Offer — Unconfirmed Shipping')).toBeInTheDocument();
    expect(screen.getByText(/Shipping cost is unconfirmed/i)).toBeInTheDocument();
  });

  it('visibly renders the demo-data disclosure notice in the Copilot response', () => {
    const copilotDataWithNotice = {
      query_message: 'wireless headphones',
      copilot_mode: 'gemini_ai',
      extracted_intent: {
        search_query: 'wireless headphones',
        category: 'Audio',
      },
      matched_products_count: 1,
      matched_products: [],
      top_recommendation: null,
      explanation: 'Matched Sony WH-1000XM5.',
      is_demo_data: true,
      notice: 'All product prices, shipping rates, and retailer offers are simulated demo data.',
    };

    render(
      <MemoryRouter>
        <AICopilotBar
          onSearch={vi.fn()}
          onReset={vi.fn()}
          copilotData={copilotDataWithNotice}
        />
      </MemoryRouter>
    );

    expect(
      screen.getByText('All product prices, shipping rates, and retailer offers are simulated demo data.')
    ).toBeInTheDocument();
  });

  it('displays empty state on Products page when Copilot returns no matching products', async () => {
    copilotApi.query.mockResolvedValueOnce({
      query_message: '4K OLED Gaming Monitor under 10k',
      copilot_mode: 'gemini_ai',
      extracted_intent: {
        search_query: '4K OLED Gaming Monitor',
        category: 'Monitors',
        brand: null,
        max_budget_rupees: 10000,
        key_features: [],
      },
      matched_products_count: 0,
      matched_products: [],
      top_recommendation: null,
      explanation: 'No active products in our catalogue matched 4K OLED Gaming Monitor under ₹10,000.',
      is_demo_data: true,
      notice: 'All product prices, shipping rates, and retailer offers are simulated demo data.',
    });

    render(
      <MemoryRouter initialEntries={['/products']}>
        <Products />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Simulated Product Catalogue')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Sony WH-1000XM5 headphones under ₹28,000/i);
    const submitBtn = screen.getByRole('button', { name: /Ask Copilot/i });

    fireEvent.change(input, { target: { value: '4K OLED Gaming Monitor under 10k' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(copilotApi.query).toHaveBeenCalledWith('4K OLED Gaming Monitor under 10k');
      expect(
        screen.getByText(/No items in our catalogue matched your Copilot inquiry or budget constraint/i)
      ).toBeInTheDocument();
    });
  });
});
