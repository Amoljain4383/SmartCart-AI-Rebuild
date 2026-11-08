import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PayPalCheckoutButton from '../components/PayPalCheckoutButton';
import { ordersApi } from '../api/orders';

let mockButtonsProps = {};

vi.mock('@paypal/react-paypal-js', () => ({
  PayPalScriptProvider: ({ children }) => <div data-testid="paypal-provider">{children}</div>,
  PayPalButtons: (props) => {
    mockButtonsProps = props;
    return (
      <div data-testid="paypal-buttons-mock">
        <button
          data-testid="simulate-create-btn"
          onClick={async () => {
            await props.createOrder({}, {});
          }}
        >
          Mock Create
        </button>
        <button
          data-testid="simulate-approve-btn"
          onClick={async () => {
            await props.onApprove({ orderID: 'PAYPAL-MOCK-123' }, {});
          }}
        >
          Mock Approve
        </button>
      </div>
    );
  },
}));

vi.mock('../api/orders', () => ({
  ordersApi: {
    createPayPalOrder: vi.fn(),
    capturePayPalOrder: vi.fn(),
  },
}));

describe('PayPal Sandbox Checkout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders disabled checkout notice if VITE_PAYPAL_CLIENT_ID is missing or placeholder', () => {
    const originalEnv = import.meta.env.VITE_PAYPAL_CLIENT_ID;
    import.meta.env.VITE_PAYPAL_CLIENT_ID = 'your_paypal_sandbox_client_id';

    render(
      <PayPalCheckoutButton
        orderId="ord-1"
        orderTotalFormatted="₹2,499.00"
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByText(/PayPal Sandbox Client ID Missing/i)).toBeInTheDocument();
    expect(screen.queryByTestId('paypal-provider')).not.toBeInTheDocument();

    import.meta.env.VITE_PAYPAL_CLIENT_ID = originalEnv;
  });

  it('createOrder invokes backend ordersApi.createPayPalOrder and returns paypal_order_id', async () => {
    ordersApi.createPayPalOrder.mockResolvedValueOnce({
      order_id: 'ord-123',
      paypal_order_id: 'PAYPAL-ORDER-777',
      status: 'paypal_created',
      amount: '2499.00',
      currency: 'INR',
    });

    render(
      <PayPalCheckoutButton
        orderId="ord-123"
        orderTotalFormatted="₹2,499.00"
        currency="INR"
        onSuccess={vi.fn()}
      />
    );

    expect(screen.getByTestId('paypal-provider')).toBeInTheDocument();

    // Trigger createOrder
    const paypalOrderId = await mockButtonsProps.createOrder({}, {});
    expect(ordersApi.createPayPalOrder).toHaveBeenCalledWith('ord-123');
    expect(paypalOrderId).toBe('PAYPAL-ORDER-777');
  });

  it('buyer approval executes backend capture and notifies success ONLY after server confirmation', async () => {
    const successSpy = vi.fn();
    ordersApi.capturePayPalOrder.mockResolvedValueOnce({
      order_id: 'ord-123',
      paypal_order_id: 'PAYPAL-ORDER-777',
      paypal_capture_id: 'CAPTURE-999',
      status: 'paid',
      order: { id: 'ord-123', status: 'paid', total_formatted: '₹2,499.00' },
      message: 'Payment captured successfully.',
    });

    render(
      <PayPalCheckoutButton
        orderId="ord-123"
        orderTotalFormatted="₹2,499.00"
        currency="INR"
        onSuccess={successSpy}
      />
    );

    // Prior to approval, success callback has not been called
    expect(successSpy).not.toHaveBeenCalled();

    // Trigger buyer approval
    await mockButtonsProps.onApprove({ orderID: 'PAYPAL-ORDER-777' }, {});

    expect(ordersApi.capturePayPalOrder).toHaveBeenCalledWith('ord-123');
    expect(successSpy).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'ord-123', status: 'paid' })
    );
  });

  it('handles backend capture failure without granting false payment success', async () => {
    const successSpy = vi.fn();
    ordersApi.capturePayPalOrder.mockRejectedValueOnce(
      new Error('PayPal capture gateway timeout or currency mismatch')
    );

    render(
      <PayPalCheckoutButton
        orderId="ord-123"
        orderTotalFormatted="₹2,499.00"
        currency="INR"
        onSuccess={successSpy}
      />
    );

    await mockButtonsProps.onApprove({ orderID: 'PAYPAL-ORDER-777' }, {});

    expect(ordersApi.capturePayPalOrder).toHaveBeenCalledWith('ord-123');
    // Success must NOT be called on failure
    expect(successSpy).not.toHaveBeenCalled();

    // Error message must be rendered to user
    await waitFor(() => {
      expect(
        screen.getByText(/PayPal capture gateway timeout or currency mismatch/i)
      ).toBeInTheDocument();
    });
  });
});
