import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Package,
  Store,
  CreditCard,
  Users,
  Plus,
  Edit2,
  Check,
  X,
  ToggleLeft,
  ToggleRight,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { adminApi } from '../api/admin';
import { productsApi } from '../api/products';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedProductOffers, setSelectedProductOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);

  const [activeTab, setActiveTab] = useState('products'); // 'products' | 'offers'

  // Product Modal State
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    title: '',
    description: '',
    category: '',
    brand: '',
    image_url: '',
    is_active: true,
  });

  // Offer Modal State
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [editingOffer, setEditingOffer] = useState(null);
  const [offerForm, setOfferForm] = useState({
    retailer_name: '',
    product_price: '',
    shipping_cost: '0',
    estimated_delivery_days: 3,
    retailer_rating_tenth: 45,
    review_count: 50,
    return_policy: '14 days returnable',
    stock_status: 'in_stock',
    is_active: true,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const dash = await adminApi.getDashboard();
      setMetrics(dash);

      const prods = await productsApi.getProducts({ limit: 100 });
      setProducts(prods || []);

      if (prods && prods.length > 0 && !selectedProductId) {
        setSelectedProductId(prods[0].id);
      }
    } catch (err) {
      console.error('Failed to load admin data:', err);
      setAlert({ type: 'error', message: err.message || 'Failed to load admin dashboard' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When selected product changes, load offers
  useEffect(() => {
    async function loadOffers() {
      if (!selectedProductId) return;
      try {
        const offList = await productsApi.getOffers(selectedProductId);
        setSelectedProductOffers(offList || []);
      } catch (err) {
        console.error('Failed to load product offers:', err);
      }
    }
    loadOffers();
  }, [selectedProductId]);

  // Product Handlers
  const handleToggleProductStatus = async (product) => {
    try {
      const updated = await adminApi.toggleProductStatus(product.id, !product.is_active);
      setAlert({
        type: 'success',
        message: `Product "${product.title}" is now ${updated.is_active ? 'Active' : 'Inactive'}.`,
      });
      loadData();
    } catch (err) {
      setAlert({ type: 'error', message: err.message || 'Failed to update status' });
    }
  };

  const handleOpenProductModal = (prod = null) => {
    if (prod) {
      setEditingProduct(prod);
      setProductForm({
        title: prod.title,
        description: prod.description || '',
        category: prod.category,
        brand: prod.brand,
        image_url: prod.image_url || '',
        is_active: prod.is_active,
      });
    } else {
      setEditingProduct(null);
      setProductForm({
        title: '',
        description: '',
        category: 'Electronics',
        brand: '',
        image_url: '',
        is_active: true,
      });
    }
    setShowProductModal(true);
  };

  const handleSaveProduct = async (e) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        await adminApi.updateProduct(editingProduct.id, productForm);
        setAlert({ type: 'success', message: 'Product updated successfully.' });
      } else {
        await adminApi.createProduct(productForm);
        setAlert({ type: 'success', message: 'New product created successfully.' });
      }
      setShowProductModal(false);
      loadData();
    } catch (err) {
      setAlert({ type: 'error', message: err.message || 'Failed to save product' });
    }
  };

  // Offer Handlers
  const handleToggleOfferStatus = async (offer) => {
    try {
      const updated = await adminApi.toggleOfferStatus(offer.id, !offer.is_active);
      setAlert({
        type: 'success',
        message: `Offer from "${offer.retailer_name}" is now ${updated.is_active ? 'Active' : 'Inactive'}.`,
      });
      const offList = await productsApi.getOffers(selectedProductId);
      setSelectedProductOffers(offList || []);
      loadData();
    } catch (err) {
      setAlert({ type: 'error', message: err.message || 'Failed to update offer status' });
    }
  };

  const handleOpenOfferModal = (off = null) => {
    if (off) {
      setEditingOffer(off);
      // Derive rupees string from paise
      const priceRupees = (off.product_price_paise / 100).toFixed(2);
      const shippingRupees = off.shipping_cost_paise !== null ? (off.shipping_cost_paise / 100).toFixed(2) : '0';
      setOfferForm({
        retailer_name: off.retailer_name,
        product_price: priceRupees,
        shipping_cost: shippingRupees,
        estimated_delivery_days: off.estimated_delivery_days,
        retailer_rating_tenth: off.retailer_rating_tenth,
        review_count: off.review_count,
        return_policy: off.return_policy || '14 days returnable',
        stock_status: off.stock_status,
        is_active: off.is_active,
      });
    } else {
      setEditingOffer(null);
      setOfferForm({
        retailer_name: '',
        product_price: '',
        shipping_cost: '0',
        estimated_delivery_days: 3,
        retailer_rating_tenth: 45,
        review_count: 100,
        return_policy: '14 days returnable',
        stock_status: 'in_stock',
        is_active: true,
      });
    }
    setShowOfferModal(true);
  };

  const handleSaveOffer = async (e) => {
    e.preventDefault();
    try {
      if (editingOffer) {
        await adminApi.updateOffer(editingOffer.id, offerForm);
        setAlert({ type: 'success', message: 'Offer updated successfully.' });
      } else {
        await adminApi.createOffer(selectedProductId, offerForm);
        setAlert({ type: 'success', message: 'Retailer offer added successfully.' });
      }
      setShowOfferModal(false);
      const offList = await productsApi.getOffers(selectedProductId);
      setSelectedProductOffers(offList || []);
      loadData();
    } catch (err) {
      setAlert({ type: 'error', message: err.message || 'Failed to save offer' });
    }
  };

  if (loading && !metrics) {
    return <LoadingSpinner text="Loading Admin Control Center..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200 uppercase tracking-wider inline-flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            Administrator Control Center
          </span>
          <h1 className="text-3xl font-extrabold text-slate-900 mt-1">SmartCart Management</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage product catalogue, competing retailer offers, and review live purchase metrics.
          </p>
        </div>
      </div>

      {alert && (
        <Alert
          type={alert.type}
          message={alert.message}
          onClose={() => setAlert(null)}
        />
      )}

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Catalogue Products</span>
          <div className="text-xl font-black text-slate-900 mt-1">
            {products.length} <span className="text-xs text-slate-400 font-normal">({products.filter((p) => p.is_active).length} active)</span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Retailer Offers</span>
          <div className="text-xl font-black text-slate-900 mt-1">
            {products.reduce((acc, p) => acc + (p.offer_count || 0), 0)} <span className="text-xs text-slate-400 font-normal">offers linked</span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Admin Session</span>
          <div className="text-sm font-bold text-slate-800 mt-1 truncate">
            {metrics?.admin?.email || 'Administrator'}
          </div>
          <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200 uppercase tracking-wider inline-block mt-0.5">
            Role: {metrics?.admin?.role || 'admin'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">System Status</span>
          <div className="text-sm font-bold text-emerald-600 mt-2 flex items-center gap-1">
            <Check className="w-4 h-4" /> Operational
          </div>
          <span className="text-[10px] text-slate-400 block mt-0.5">FastAPI + SQLite Paired</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-sm font-bold">
        <button
          onClick={() => setActiveTab('products')}
          className={`pb-3 transition relative ${
            activeTab === 'products'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Product Management ({products.length})
        </button>
        <button
          onClick={() => setActiveTab('offers')}
          className={`pb-3 transition relative ${
            activeTab === 'offers'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Retailer Offers Management
        </button>
      </div>

      {/* TAB 1: Products */}
      {activeTab === 'products' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Catalogue Products</h2>
            <button
              onClick={() => handleOpenProductModal(null)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 shadow-sm"
            >
              <Plus className="w-4 h-4" /> Add Product
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto shadow-sm">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Product Title</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Brand</th>
                  <th className="px-4 py-3">Lowest Landed Cost</th>
                  <th className="px-4 py-3">Offers</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900 max-w-[200px] truncate">
                      {p.title}
                    </td>
                    <td className="px-4 py-3">{p.category}</td>
                    <td className="px-4 py-3 font-medium text-slate-700">{p.brand}</td>
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {p.min_total_cost_formatted || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-medium">
                        {p.offer_count} offers
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleProductStatus(p)}
                        className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                          p.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-500 border border-slate-200'
                        }`}
                      >
                        {p.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleOpenProductModal(p)}
                        className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
                        title="Edit product"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Offers */}
      {activeTab === 'offers' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold text-slate-700 shrink-0">Select Product:</label>
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 max-w-xs"
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title} ({p.brand})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => handleOpenOfferModal(null)}
              disabled={!selectedProductId}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <Plus className="w-4 h-4" /> Add Retailer Offer
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto shadow-sm">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Retailer</th>
                  <th className="px-4 py-3">Sticker Price</th>
                  <th className="px-4 py-3">Shipping Cost</th>
                  <th className="px-4 py-3">True Landed Cost</th>
                  <th className="px-4 py-3">Delivery</th>
                  <th className="px-4 py-3">Rating</th>
                  <th className="px-4 py-3">Stock Status</th>
                  <th className="px-4 py-3">Active</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {selectedProductOffers.map((off) => (
                  <tr key={off.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900">{off.retailer_name}</td>
                    <td className="px-4 py-3">{off.product_price_formatted}</td>
                    <td className="px-4 py-3">{off.shipping_cost_formatted}</td>
                    <td className="px-4 py-3 font-black text-slate-900">{off.total_cost_formatted}</td>
                    <td className="px-4 py-3">{off.estimated_delivery_days} days</td>
                    <td className="px-4 py-3">{off.rating_float} ★</td>
                    <td className="px-4 py-3 font-medium capitalize">{off.stock_status}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleOfferStatus(off)}
                        className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                          off.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-500 border border-slate-200'
                        }`}
                      >
                        {off.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleOpenOfferModal(off)}
                        className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
                        title="Edit offer"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Product Create / Edit Modal */}
      {showProductModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">
                {editingProduct ? 'Edit Product' : 'Add New Product'}
              </h3>
              <button
                onClick={() => setShowProductModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProduct} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={productForm.title}
                  onChange={(e) => setProductForm({ ...productForm, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Brand</label>
                  <input
                    type="text"
                    required
                    value={productForm.brand}
                    onChange={(e) => setProductForm({ ...productForm, brand: e.target.value })}
                    className="w-full px-3 py-2 border rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <input
                    type="text"
                    required
                    value={productForm.category}
                    onChange={(e) => setProductForm({ ...productForm, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-xl"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Image URL</label>
                <input
                  type="text"
                  value={productForm.image_url}
                  onChange={(e) => setProductForm({ ...productForm, image_url: e.target.value })}
                  className="w-full px-3 py-2 border rounded-xl"
                />
              </div>

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 shadow-sm"
                >
                  Save Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Offer Create / Edit Modal */}
      {showOfferModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">
                {editingOffer ? 'Edit Retailer Offer' : 'Add Retailer Offer'}
              </h3>
              <button
                onClick={() => setShowOfferModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveOffer} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Retailer Name</label>
                <input
                  type="text"
                  required
                  value={offerForm.retailer_name}
                  onChange={(e) => setOfferForm({ ...offerForm, retailer_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Product Price (₹ INR)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={offerForm.product_price}
                    onChange={(e) => setOfferForm({ ...offerForm, product_price: e.target.value })}
                    className="w-full px-3 py-2 border rounded-xl"
                    placeholder="e.g. 2499.00"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Shipping Cost (₹ INR)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={offerForm.shipping_cost}
                    onChange={(e) => setOfferForm({ ...offerForm, shipping_cost: e.target.value })}
                    className="w-full px-3 py-2 border rounded-xl"
                    placeholder="0 for FREE delivery"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Est. Delivery (Days)</label>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    required
                    value={offerForm.estimated_delivery_days}
                    onChange={(e) => setOfferForm({ ...offerForm, estimated_delivery_days: parseInt(e.target.value) || 3 })}
                    className="w-full px-3 py-2 border rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Stock Status</label>
                  <select
                    value={offerForm.stock_status}
                    onChange={(e) => setOfferForm({ ...offerForm, stock_status: e.target.value })}
                    className="w-full px-3 py-2 border rounded-xl"
                  >
                    <option value="in_stock">In Stock</option>
                    <option value="low_stock">Low Stock</option>
                    <option value="out_of_stock">Out of Stock</option>
                  </select>
                </div>
              </div>

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowOfferModal(false)}
                  className="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 shadow-sm"
                >
                  Save Offer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
