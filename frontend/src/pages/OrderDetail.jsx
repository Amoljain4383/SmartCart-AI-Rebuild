import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { CheckCircle2, Clock, Package, ShieldCheck, ArrowLeft, AlertCircle, Truck, FileText } from 'lucide-react';
import { ordersApi } from '../api/orders';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';
import PayPalCheckoutButton from '../components/PayPalCheckoutButton';

export default function OrderDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const paymentSuccess = searchParams.get('payment_success') === 'true';

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOrder = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ordersApi.getOrder(id);
      setOrder(data);
    } catch (err) {
      console.error('Failed to load order receipt:', err);
      setError(err.message || 'Failed to load order details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrder();
  }, [id]);

  if (loading) {
    return <LoadingSpinner text="Retrieving verified order receipt..." />;
  }

  if (error || !order) {
    return (
      <div className="max-w-xl mx-auto px-4 py-12">
        <Alert type="error" message={error || 'Order not found'} />
        <Link to="/orders" className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 mt-4">
          <ArrowLeft className="w-4 h-4" /> Back to My Orders
        </Link>
      </div>
    );
  }

  const isPaid = (order.status || '').toLowerCase() === 'paid';

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back button */}
      <Link
        to="/orders"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to all orders
      </Link>

      {/* Success Banner if redirected from capture */}
      {paymentSuccess && isPaid && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-3 shadow-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <h4 className="font-bold text-sm">PayPal Sandbox Payment Verified!</h4>
            <p className="mt-0.5">
              The payment was securely verified on the backend. Your simulated purchase for order #{order.id.substring(0, 8)} is complete.
            </p>
          </div>
        </div>
      )}

      {/* Main Receipt Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Receipt Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Order Receipt
              </h1>
              {isPaid ? (
                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-bold px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Paid & Verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 text-xs font-bold px-2.5 py-1 rounded-full border border-amber-200">
                  <Clock className="w-3.5 h-3.5 text-amber-600" />
                  Status: {order.status}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Order ID: {order.id}
            </p>
          </div>

          <div className="text-left sm:text-right text-xs text-slate-500">
            <span className="block font-medium text-slate-400">Order Placed</span>
            <span className="font-semibold text-slate-800">
              {new Date(order.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>

        {/* PayPal Details if available */}
        {order.paypal_order_id && (
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs space-y-1 font-mono">
            <div className="text-slate-400 font-sans font-semibold uppercase tracking-wider text-[10px]">
              PayPal Sandbox Transaction Verification
            </div>
            <div className="text-slate-700">
              PayPal Order ID: <strong>{order.paypal_order_id}</strong>
            </div>
            {order.paypal_capture_id && (
              <div className="text-slate-700">
                PayPal Capture ID: <strong>{order.paypal_capture_id}</strong>
              </div>
            )}
          </div>
        )}

        {/* If pending payment, allow completing PayPal checkout */}
        {!isPaid && (
          <div className="p-4 bg-indigo-50/60 rounded-2xl border border-indigo-200 space-y-3">
            <h4 className="text-xs font-bold text-slate-900">Payment Pending</h4>
            <PayPalCheckoutButton
              orderId={order.id}
              orderTotalFormatted={order.total_formatted}
              currency={order.currency || 'INR'}
              onSuccess={() => fetchOrder()}
            />
          </div>
        )}

        {/* Line Items */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Ordered Line Items ({order.items?.length || 0})
          </h3>
          <div className="divide-y divide-slate-100 border border-slate-100 rounded-2xl overflow-hidden">
            {order.items?.map((item) => (
              <div key={item.id} className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">{item.product_title}</h4>
                  <p className="text-slate-500 text-[11px] mt-0.5">
                    Retailer: <strong>{item.retailer_name}</strong> • Quantity: {item.quantity}
                  </p>
                  <p className="text-slate-400 text-[10px] mt-0.5">
                    Base: {item.unit_price_formatted} + Shipping: {item.shipping_cost_formatted}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-medium block">Total</span>
                  <span className="font-black text-slate-900 text-sm">{item.total_cost_formatted}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Shipping Address & Landed Cost Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
          {/* Shipping Address */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-800 mb-2">
              <Truck className="w-4 h-4 text-slate-400" />
              Delivery Destination
            </div>
            <p className="font-semibold text-slate-700">{order.shipping_address?.recipient_name}</p>
            <p className="text-slate-500">{order.shipping_address?.address_line}</p>
            <p className="text-slate-500">
              {order.shipping_address?.city}, {order.shipping_address?.postal_code}
            </p>
            {order.shipping_address?.state && (
              <p className="text-slate-500">{order.shipping_address.state}</p>
            )}
          </div>

          {/* Totals */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs space-y-2">
            <div className="flex justify-between text-slate-600">
              <span>Currency</span>
              <span className="font-bold text-slate-800">{order.currency}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Raw Integer Amount</span>
              <span className="font-bold text-slate-800">{order.total_paise} paise</span>
            </div>
            <div className="flex justify-between text-slate-900 font-extrabold text-sm pt-2 border-t border-slate-200">
              <span>Total Landed Cost</span>
              <span className="text-indigo-600 text-base">{order.total_formatted}</span>
            </div>
          </div>
        </div>

        {/* Demo Notice */}
        <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200/80 text-amber-900 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {order.simulated_order_notice ||
              'SmartCart AI Demo Notice: This is a simulated prototype order. No physical items will be shipped and no real bank accounts were debited.'}
          </p>
        </div>
      </div>
    </div>
  );
}
