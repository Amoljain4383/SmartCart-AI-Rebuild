import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Sparkles, ShieldCheck, TrendingDown, ArrowRight, Truck, Store, CheckCircle2 } from 'lucide-react';
import { productsApi } from '../api/products';
import ProductCard from '../components/ProductCard';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadFeatured() {
      try {
        const data = await productsApi.getProducts({ limit: 4, sort_by: 'title' });
        setFeaturedProducts(data || []);
      } catch (err) {
        console.error('Failed to load featured products:', err);
      } finally {
        setLoading(false);
      }
    }
    loadFeatured();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/products');
    }
  };

  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50/70 via-white to-slate-50 pt-16 pb-20 border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider mb-6 border border-indigo-200/60 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            Hackathon Winner Prototype: True Landed Cost Intelligence
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight sm:leading-none">
            Stop Falling for <span className="text-indigo-600">Sticker Price</span> Deceptions.
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Other comparison tools show misleading item prices that double at checkout. SmartCart AI audits
            <strong> item price + verified shipping fees</strong> across competing retailers to reveal the true lowest total cost.
          </p>

          {/* Quick Search Bar */}
          <form
            onSubmit={handleSearchSubmit}
            className="mt-8 max-w-2xl mx-auto flex items-center bg-white p-2 rounded-2xl shadow-lg shadow-indigo-100/50 border border-slate-200 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-100 transition"
          >
            <div className="pl-3 text-slate-400">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              placeholder="Search products or ask AI (e.g., 'Headphones under ₹28,000')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none bg-transparent"
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs px-5 py-3 rounded-xl shadow transition shrink-0 flex items-center gap-1.5"
            >
              <span>Search Deals</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* AI Copilot Suggestion Chips */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> Try Copilot:
            </span>
            {['Sony WH-1000XM5 under ₹28,000', 'Apple Watch Series 9 under 45k', 'Kindle Paperwhite under 15k', 'Logitech mouse under 9k'].map((prompt) => (
              <button
                key={prompt}
                onClick={() => navigate(`/products?copilot=${encodeURIComponent(prompt)}`)}
                className="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full border border-indigo-200/80 transition shadow-sm"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Value Badges */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> True Landed Cost Calculation
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Free Deterministic AI Recommendations
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Integer Paise Precision (0% Float Drift)
            </span>
          </div>
        </div>
      </section>

      {/* 3 Pillars of SmartCart */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-slate-900">Why Surface Price Comparison Fails</h2>
          <p className="text-slate-500 text-sm mt-2">
            Most platforms rank Retailer A as cheapest because of a low sticker price, ignoring a hefty ₹300 shipping charge added in final checkout.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
              <TrendingDown className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">True Landed Cost</h3>
            <p className="text-slate-500 text-xs mt-2 leading-relaxed">
              We compute <code className="text-indigo-600 font-bold">Total = Price + Shipping</code> for every offer. An offer with ₹1,999 + ₹250 shipping is correctly ranked lower than ₹2,100 with free delivery.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Free Offline AI Engine</h3>
            <p className="text-slate-500 text-xs mt-2 leading-relaxed">
              Zero paid AI dependencies. Our deterministic rule-based ranking engine provides instant, transparent recommendations with clear mathematical savings explanations.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Paise Precision Financials</h3>
            <p className="text-slate-500 text-xs mt-2 leading-relaxed">
              All financial values are stored in integer paise. No IEEE-754 floating-point rounding errors or lost fractions in database, cart, or PayPal Sandbox transactions.
            </p>
          </div>
        </div>
      </section>

      {/* Featured Catalogue Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-8">
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Simulated Demo Catalogue</span>
            <h2 className="text-2xl font-bold text-slate-900 mt-0.5">Featured Demo Products</h2>
            <p className="text-slate-500 text-xs mt-1">
              Explore multi-retailer offers and test true landed cost calculations.
            </p>
          </div>
          <Link
            to="/products"
            className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-3.5 py-2 rounded-xl transition"
          >
            <span>View All Products</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <LoadingSpinner text="Loading demo products..." />
        ) : featuredProducts.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        ) : (
          <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-500 text-sm">
            No products found. Please seed demo catalogue.
          </div>
        )}
      </section>

      {/* Demo Callout Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-3xl p-8 sm:p-10 shadow-xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl">
            <span className="bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 text-[11px] font-bold uppercase tracking-wider px-3 py-1 rounded-full inline-block mb-4">
              Hackathon Evaluation Guide
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Test Real-Time Multi-Retailer Comparison & PayPal Sandbox Capture
            </h2>
            <p className="text-slate-300 text-sm mt-3 leading-relaxed">
              Sign in with demo credentials or register a test account. Compare multi-retailer offers with different shipping costs, generate deterministic recommendations, and complete a simulated purchase through PayPal Sandbox.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link
                to="/products"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-5 py-3 rounded-xl transition shadow-sm"
              >
                Browse Catalogue
              </Link>
              <Link
                to="/login"
                className="bg-white/10 hover:bg-white/20 text-white font-bold text-xs px-5 py-3 rounded-xl transition border border-white/10"
              >
                Sign In to Test Checkout
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
