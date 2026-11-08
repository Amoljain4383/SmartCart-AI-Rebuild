import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { ShoppingBag, Truck, ShieldCheck, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { productsApi } from '../api/products';
import { ordersApi } from '../api/orders';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';
import PayPalCheckoutButton from '../components/PayPalCheckoutButton';

export default function Checkout() {
  const [searchParams] = useSearchParams();
  const offerId = searchParams.get('offerId');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [offer, setOffer] = useState(null);
  const [product, setProduct] = useState(null);

  // Shipping Form State
  const [shippingAddress, setShippingAddress] = useState({
    recipient_name: user?.full_name || '',
    address_line: '124 Brigade Road, Indiranagar',
    city: 'Bengaluru',
    postal_code: '560001',
    state: 'Karnataka',
  });

  // Created Order State
  const [createdOrder, setCreatedOrder] = useState(null);
  const [orderCreating, setOrderCreating] = useState(false);

  useEffect(() => {
    async function resolveOffer() {
      if (!offerId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch products to locate the offer
        const allProducts = await productsApi.getProducts({ limit: 100 });
        let matchedOffer = null;
        let matchedProduct = null;

        for (const p of allProducts) {
          const detail = await productsApi.getProduct(p.id);
          const found = detail.offers?.find((o) => o.id === offerId);
          if (found) {
            matchedOffer = found;
            matchedProduct = detail;
            break;
          }
        }

        if (!matchedOffer) {
          throw new Error(`Offer with ID '${offerId}' was not found or is no longer available.`);
        }

        setOffer(matchedOffer);
        setProduct(matchedProduct);
      } catch (err) {
        console.error('Failed to load offer for checkout:', err);
        setError(err.message || 'Failed to load selected offer');
      } finally {
        setLoading(false);
      }
    }

    resolveOffer();
  }, [offerId]);

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    if (!offer) return;

    try {
      setOrderCreating(true);
      setError(null);

      // Generate a client idempotency key to prevent double submits
      const idempotencyKey = `sc-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      const orderPayload = {
        items: [
          {
            offer_id: offer.id,
            quantity: 1,
          },
        ],
        shipping_address: {
          recipient_name: shippingAddress.recipient_name,
          address_line: shippingAddress.address_line,
          city: shippingAddress.city,
          postal_code: shippingAddress.postal_code,
          state: shippingAddress.state,
        },
        idempotency_key: idempotencyKey,
      };

      const order = await ordersApi.createOrder(orderPayload);
      setCreatedOrder(order);
    } catch (err) {
      console.error('Order creation error:', err);
      setError(err.message || 'Failed to initialize order on server');
    } finally {
      setOrderCreating(false);
    }
  };

  const handlePaymentSuccess = (capturedOrder) => {
    navigate(`/orders/${capturedOrder.id || createdOrder.id}?payment_success=true`);
  };

  if (loading) {
    return <LoadingSpinner text="Preparing checkout details..." />;
  }

  if (!offerId || (!offer && !loading)) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800">No Offer Selected</h2>
        <p className="text-xs text-slate-500">
          Please select a retailer offer from our catalogue comparison table before proceeding to checkout.
        </p>
        <Link
          to="/products"
          className="inline-block px-5 py-2.5 bg-indigo-600 text-white font-bold text-xs rounded-xl hover:bg-indigo-700 transition"
        >
          Browse Catalogue
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div>
        <Link
          to={`/products/${product?.id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to product comparison
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
          Complete Your Order
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Review verified landed cost breakdown and proceed with PayPal Sandbox payment.
        </p>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Shipping & Confirmation */}
        <div className="lg:col-span-7 space-y-6">
          {/* Step 1: Shipping Address Form */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <Truck className="w-4 h-4 text-indigo-600" />
                1. Shipping Address
              </h2>
              {createdOrder && (
                <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Confirmed
                </span>
              )}
            </div>

            <form onSubmit={handleCreateOrder} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Recipient Name
                </label>
                <input
                  type="text"
                  required
                  disabled={Boolean(createdOrder)}
                  value={shippingAddress.recipient_name}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, recipient_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Delivery Street Address
                </label>
                <input
                  type="text"
                  required
                  disabled={Boolean(createdOrder)}
                  value={shippingAddress.address_line}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, address_line: e.target.value })}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-60"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    required
                    disabled={Boolean(createdOrder)}
                    value={shippingAddress.city}
                    onChange={(e) => setShippingAddress({ ...shippingAddress, city: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-60"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Postal Code
                  </label>
                  <input
                    type="text"
                    required
                    disabled={Boolean(createdOrder)}
                    value={shippingAddress.postal_code}
                    onChange={(e) => setShippingAddress({ ...shippingAddress, postal_code: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-60"
                  />
                </div>
              </div>

              {!createdOrder && (
                <button
                  type="submit"
                  disabled={orderCreating}
                  className="w-full mt-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl text-xs shadow-sm transition flex items-center justify-center gap-2"
                >
                  {orderCreating ? 'Calculating Landed Cost on Backend...' : 'Confirm Address & Proceed to Payment'}
                </button>
              )}
            </form>
          </div>

          {/* Step 2: Payment Section */}
          {createdOrder && (
            <div className="bg-white rounded-2xl border border-indigo-200 p-6 shadow-sm ring-2 ring-indigo-500/10">
              <h2 className="font-bold text-slate-900 text-base mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                2. PayPal Sandbox Payment
              </h2>

              <PayPalCheckoutButton
                orderId={createdOrder.id}
                orderTotalFormatted={createdOrder.total_formatted}
                currency={createdOrder.currency || 'INR'}
                onSuccess={handlePaymentSuccess}
              />
            </div>
          )}
        </div>

        {/* Right: Order Landed Cost Summary */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5">
          <h2 className="font-bold text-slate-900 text-base flex items-center gap-2 border-b border-slate-100 pb-3">
            <ShoppingBag className="w-4 h-4 text-indigo-600" />
            Landed Cost Summary
          </h2>

          {/* Product + Retailer info */}
          <div className="flex gap-3 items-center">
            {product?.image_url && (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-16 h-16 object-contain rounded-xl bg-slate-50 border border-slate-100 p-1"
              />
            )}
            <div className="flex-1 min-w-0">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                {product?.brand}
              </span>
              <h4 className="text-xs font-bold text-slate-900 truncate">
                {product?.title}
              </h4>
              <p className="text-[11px] text-slate-500">
                Fulfilling Retailer: <strong>{offer.retailer_name}</strong>
              </p>
            </div>
          </div>

          {/* Itemized Price Breakdown */}
          <div className="space-y-2.5 pt-3 border-t border-slate-100 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Item Sticker Price</span>
              <span className="font-semibold text-slate-800">{offer.product_price_formatted}</span>
            </div>

            <div className="flex justify-between text-slate-600">
              <span>Verified Delivery Fee</span>
              <span className="font-semibold text-slate-800">
                {offer.shipping_cost_paise === 0 ? (
                  <span className="text-emerald-600 font-bold">FREE</span>
                ) : (
                  offer.shipping_cost_formatted
                )}
              </span>
            </div>

            <div className="flex justify-between text-slate-900 text-sm font-black pt-3 border-t border-slate-200">
              <span>Total Landed Cost</span>
              <span className="text-indigo-600 text-base">{offer.total_cost_formatted}</span>
            </div>
          </div>

          {/* Precision note */}
          <div className="p-3 bg-slate-50 rounded-xl text-[11px] text-slate-500 border border-slate-200/60 leading-relaxed">
            🛡️ <strong>Monetary Precision:</strong> Calculated on server in exact integer paise ({offer.total_cost_paise} paise). No floating-point roundoff.
          </div>
        </div>
      </div>
    </div>
  );
}
