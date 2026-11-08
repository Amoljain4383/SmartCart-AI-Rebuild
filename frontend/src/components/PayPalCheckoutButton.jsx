import React, { useState } from 'react';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { Loader2, AlertCircle, ShieldCheck } from 'lucide-react';
import { ordersApi } from '../api/orders';

export default function PayPalCheckoutButton({ orderId, orderTotalFormatted, currency = 'INR', onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState(null);

  const clientId = import.meta.env.VITE_PAYPAL_CLIENT_ID;
  const isConfigured = Boolean(
    clientId &&
    clientId.trim() !== '' &&
    !clientId.includes('your_paypal_sandbox_client_id')
  );

  // If public Sandbox Client ID is missing, disable checkout and provide configuration guidance
  if (!isConfigured) {
    return (
      <div className="space-y-3 p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm">PayPal Sandbox Client ID Missing</h4>
            <p className="leading-relaxed">
              Online checkout requires a public PayPal Sandbox Client ID.
              Please configure <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-bold">VITE_PAYPAL_CLIENT_ID</code> in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-bold">frontend/.env</code>.
            </p>
            <p className="text-[11px] text-amber-800 pt-1">
              Example: <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">VITE_PAYPAL_CLIENT_ID=test</code> or your PayPal Developer Sandbox App Client ID.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const initialOptions = {
    clientId: clientId,
    currency: currency || 'INR',
    intent: 'capture',
    components: 'buttons',
  };

  return (
    <div className="space-y-4">
      {/* PayPal Sandbox Notice Banner */}
      <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200/80 text-amber-900 text-xs">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong>PayPal Sandbox Buyer Approval:</strong> Click the official PayPal button below to approve this simulated order for <strong>{orderTotalFormatted}</strong> in the PayPal Sandbox environment.
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3.5 bg-rose-50 rounded-xl border border-rose-200 text-rose-900 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">
            <p className="font-semibold">PayPal Transaction Notice</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {capturing && (
        <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center justify-center gap-2 text-xs text-indigo-900 font-semibold">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
          <span>Verifying and capturing payment on SmartCart backend server...</span>
        </div>
      )}

      {/* Official PayPal Buttons Container */}
      <div className={`transition ${capturing ? 'opacity-40 pointer-events-none' : ''}`}>
        <PayPalScriptProvider options={initialOptions}>
          <PayPalButtons
            style={{
              layout: 'vertical',
              color: 'gold',
              shape: 'rect',
              label: 'paypal',
              height: 48,
            }}
            disabled={capturing || loading}
            createOrder={async (data, actions) => {
              try {
                setLoading(true);
                setError(null);
                // Call backend to initialize PayPal Sandbox order
                const res = await ordersApi.createPayPalOrder(orderId);
                if (!res.paypal_order_id) {
                  throw new Error('Backend response did not include a valid PayPal order ID.');
                }
                // Return PayPal order ID to official SDK for buyer approval popup
                return res.paypal_order_id;
              } catch (err) {
                console.error('Error creating PayPal order on backend:', err);
                const message = err.message || 'Failed to initialize PayPal Sandbox order.';
                setError(message);
                throw err;
              } finally {
                setLoading(false);
              }
            }}
            onApprove={async (data, actions) => {
              // Buyer successfully approved in PayPal Sandbox interface
              // Execute secure backend capture and verification
              try {
                setCapturing(true);
                setError(null);
                const captureRes = await ordersApi.capturePayPalOrder(orderId);
                // Confirm payment success only after verified server capture
                if (onSuccess) {
                  onSuccess(captureRes.order || captureRes);
                }
              } catch (err) {
                console.error('Error during backend PayPal capture:', err);
                setError(
                  err.message ||
                    'Payment capture failed or was uncertain on backend. Order status was not marked as paid.'
                );
              } finally {
                setCapturing(false);
              }
            }}
            onCancel={(data) => {
              setError('Payment approval was cancelled in PayPal Sandbox. No funds were debited.');
            }}
            onError={(err) => {
              console.error('PayPal JavaScript SDK error:', err);
              setError(
                typeof err === 'string'
                  ? err
                  : err?.message ||
                      'PayPal SDK encountered an error loading the sandbox checkout interface. Please verify your sandbox network connection and credentials.'
              );
            }}
          />
        </PayPalScriptProvider>
      </div>

      <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
        <span>Official PayPal Sandbox SDK • Server-verified capture • No client-side secret</span>
      </div>
    </div>
  );
}
