import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Filter, ArrowUpDown, X, Tag, Sparkles } from 'lucide-react';
import { productsApi } from '../api/products';
import { copilotApi } from '../api/copilot';
import ProductCard from '../components/ProductCard';
import AICopilotBar from '../components/AICopilotBar';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialCategory = searchParams.get('category') || '';
  const initialBrand = searchParams.get('brand') || '';
  const initialSort = searchParams.get('sort_by') || 'price_asc';
  const initialCopilotQuery = searchParams.get('copilot') || '';

  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState(initialCategory);
  const [brand, setBrand] = useState(initialBrand);
  const [sortBy, setSortBy] = useState(initialSort);

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Copilot State
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotData, setCopilotData] = useState(null);
  const [copilotError, setCopilotError] = useState(null);

  // Available categories & brands extracted dynamically from products
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);

  // Fetch catalogue products (when not filtered by copilot)
  useEffect(() => {
    async function fetchProducts() {
      if (copilotData) return; // Copilot controls product view when active

      try {
        setLoading(true);
        setError(null);

        let data;
        if (query.trim()) {
          data = await productsApi.searchProducts(query.trim());
          if (sortBy === 'price_asc') {
            data.sort((a, b) => (a.min_total_cost_paise || 0) - (b.min_total_cost_paise || 0));
          } else if (sortBy === 'price_desc') {
            data.sort((a, b) => (b.min_total_cost_paise || 0) - (a.min_total_cost_paise || 0));
          }
        } else {
          data = await productsApi.getProducts({
            category: category || undefined,
            brand: brand || undefined,
            sort_by: sortBy || undefined,
          });
        }

        setProducts(data || []);

        if (categories.length === 0 && data) {
          const cats = Array.from(new Set(data.map((p) => p.category))).filter(Boolean);
          const brs = Array.from(new Set(data.map((p) => p.brand))).filter(Boolean);
          setCategories(cats);
          setBrands(brs);
        }
      } catch (err) {
        console.error('Error fetching products:', err);
        setError(err.message || 'Failed to load products');
      } finally {
        setLoading(false);
      }
    }

    fetchProducts();
  }, [query, category, brand, sortBy, copilotData]);

  // Copilot handler
  const handleCopilotSearch = async (message) => {
    try {
      setCopilotLoading(true);
      setCopilotError(null);
      const result = await copilotApi.query(message);
      setCopilotData(result);
    } catch (err) {
      console.error('Copilot search error:', err);
      setCopilotError(err.message || 'AI Copilot search failed. Please try again.');
    } finally {
      setCopilotLoading(false);
    }
  };

  const handleCopilotReset = () => {
    setCopilotData(null);
    setCopilotError(null);
    const newParams = new URLSearchParams(searchParams);
    newParams.delete('copilot');
    setSearchParams(newParams);
  };

  // Trigger copilot on initial URL param if provided
  useEffect(() => {
    if (initialCopilotQuery && !copilotData) {
      handleCopilotSearch(initialCopilotQuery);
    }
  }, [initialCopilotQuery]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const newParams = new URLSearchParams(searchParams);
    if (query.trim()) {
      newParams.set('q', query.trim());
    } else {
      newParams.delete('q');
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setQuery('');
    setCategory('');
    setBrand('');
    setSortBy('price_asc');
    setCopilotData(null);
    setCopilotError(null);
    setSearchParams({});
  };

  const hasActiveFilters = Boolean(query || category || brand || sortBy !== 'price_asc');

  // Displayed products: Copilot matched products if active, else catalogue products
  const displayedProducts = copilotData ? copilotData.matched_products : products;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Catalogue & Price Comparison</span>
        <h1 className="text-3xl font-extrabold text-slate-900 mt-1">Simulated Product Catalogue</h1>
        <p className="text-slate-500 text-sm mt-1">
          Explore products and audit competing retailer offers ranked by true landed cost.
        </p>
      </div>

      {/* AI Shopping Copilot Interface */}
      <AICopilotBar
        onSearch={handleCopilotSearch}
        onReset={handleCopilotReset}
        loading={copilotLoading}
        copilotData={copilotData}
        error={copilotError}
      />

      {/* Manual Search & Filter Toolbar (hidden or secondary when Copilot is active) */}
      {!copilotData && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            {/* Search Bar */}
            <form onSubmit={handleSearchSubmit} className="flex-1 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search products by title, category, or keywords..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
              />
            </form>

            {/* Category Filter */}
            <div className="w-full md:w-48">
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  const p = new URLSearchParams(searchParams);
                  if (e.target.value) p.set('category', e.target.value);
                  else p.delete('category');
                  setSearchParams(p);
                }}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition text-slate-700"
              >
                <option value="">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Sort Selector */}
            <div className="w-full md:w-56">
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  const p = new URLSearchParams(searchParams);
                  p.set('sort_by', e.target.value);
                  setSearchParams(p);
                }}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition text-slate-700"
              >
                <option value="price_asc">Sort: Lowest Landed Cost</option>
                <option value="price_desc">Sort: Highest Landed Cost</option>
                <option value="title">Sort: Title (A-Z)</option>
              </select>
            </div>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition flex items-center justify-center gap-1.5 shrink-0"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>
      )}

      {error && <Alert type="error" message={error} />}

      {/* Product Results */}
      {loading && !copilotData ? (
        <LoadingSpinner text="Searching catalogue..." />
      ) : displayedProducts.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs text-slate-500 font-medium">
              {copilotData ? (
                <span className="flex items-center gap-1.5 text-indigo-700 font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  Showing <strong>{displayedProducts.length}</strong> AI matched catalogue {displayedProducts.length === 1 ? 'product' : 'products'}
                </span>
              ) : (
                <span>
                  Showing <strong>{displayedProducts.length}</strong> {displayedProducts.length === 1 ? 'product' : 'products'}
                </span>
              )}
            </div>

            {copilotData && (
              <button
                onClick={handleCopilotReset}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition flex items-center gap-1"
              >
                View Full Catalogue
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {displayedProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
          <Tag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-800 text-lg">No products found</h3>
          <p className="text-slate-500 text-xs mt-1">
            {copilotData
              ? 'No items in our catalogue matched your Copilot inquiry or budget constraint.'
              : 'No items matched your search query or selected filters.'}
          </p>
          <button
            onClick={clearFilters}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition"
          >
            Clear All Filters & Reset
          </button>
        </div>
      )}
    </div>
  );
}
