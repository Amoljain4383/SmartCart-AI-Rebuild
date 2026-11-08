import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package, Clock, CheckCircle2, AlertCircle, ArrowRight, ShoppingBag } from 'lucide-react';
import { ordersApi } from '../api/orders';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadOrders() {
      try {
        setLoading(true);
        setError(null);
        const data = await ordersApi.getOrders();
        setOrders(data || []);
      } catch (err) {
        console.error('Failed to load orders:', err);
        setError(err.message || 'Failed to load order history');
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, []);

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'paid':
        return (
          <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-bold px-2.5 py-1 rounded-full border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Paid & Verified
          </span>
        );
      case 'paypal_created':
        return (
          <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs font-bold px-2.5 py-1 rounded-full border border-blue-200">
            <Clock className="w-3.5 h-3.5 text-blue-600" />
            PayPal Created
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 text-xs font-bold px-2.5 py-1 rounded-full border border-amber-200">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            Pending Checkout
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 text-xs font-bold px-2.5 py-1 rounded-full border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div>
        <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Account Activity</span>
        <h1 className="text-3xl font-extrabold text-slate-900 mt-1">My Orders</h1>
        <p className="text-slate-500 text-xs mt-1">
          Review placed orders, server verification logs, and PayPal Sandbox simulation receipts.
        </p>
      </div>

      {error && <Alert type="error" message={error} />}

      {loading ? (
        <LoadingSpinner text="Fetching your orders..." />
      ) : orders.length > 0 ? (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 hover:border-slate-300 transition flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                    Order #{order.id.substring(0, 8)}
                  </span>
                  {getStatusBadge(order.status)}
                  <span className="text-xs text-slate-400">
                    {new Date(order.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                <div className="text-xs text-slate-600">
                  {order.items?.length || 0} item{order.items?.length === 1 ? '' : 's'} •{' '}
                  {order.items?.map((it) => it.retailer_name).filter(Boolean).join(', ') || 'SmartCart Retailers'}
                </div>
              </div>

              <div className="flex items-center justify-between w-full sm:w-auto sm:justify-end gap-5 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
                <div className="text-left sm:text-right">
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Total Landed Cost</span>
                  <span className="text-lg font-black text-slate-900">{order.total_formatted}</span>
                </div>

                <Link
                  to={`/orders/${order.id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-indigo-600 text-white text-xs font-bold rounded-xl transition shadow-sm"
                >
                  <span>Receipt</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-md mx-auto space-y-3">
          <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="font-bold text-slate-800 text-base">No orders placed yet</h3>
          <p className="text-slate-500 text-xs">
            Compare products across retailers and test the simulated PayPal checkout.
          </p>
          <Link
            to="/products"
            className="inline-block mt-2 px-4 py-2 bg-indigo-600 text-white font-bold text-xs rounded-xl hover:bg-indigo-700 transition"
          >
            Explore Catalogue
          </Link>
        </div>
      )}
    </div>
  );
}
