import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Store,
  Truck,
  ShieldCheck,
  Star,
  ArrowLeft,
  Award,
  AlertCircle,
  CheckCircle2,
  Tag,
  Clock
} from 'lucide-react';
import { productsApi } from '../api/products';
import { recommendationsApi } from '../api/recommendations';
import { useAuth } from '../context/AuthContext';
import OfferCard from '../components/OfferCard';
import LoadingSpinner from '../components/LoadingSpinner';
import Alert from '../components/Alert';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [product, setProduct] = useState(null);
  const [offers, setOffers] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const prodData = await productsApi.getProduct(id);
        setProduct(prodData);

        const offersData = await productsApi.getOffers(id, { sort_by: 'total_cost' });
        setOffers(offersData || []);

        // Load AI recommendation if user is authenticated
        if (isAuthenticated) {
          setRecommendationLoading(true);
          try {
            const recData = await recommendationsApi.getRecommendation({ product_id: id });
            setRecommendation(recData);
          } catch (recErr) {
            console.warn('AI recommendation unavailable:', recErr);
          } finally {
            setRecommendationLoading(false);
          }
        }
      } catch (err) {
        console.error('Error loading product details:', err);
        setError(err.message || 'Failed to load product details');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [id, isAuthenticated]);

  const handleSelectOffer = (offer) => {
    navigate(`/checkout?offerId=${offer.id}`);
  };

  if (loading) {
    return <LoadingSpinner text="Analyzing retailer offers & landed costs..." />;
  }

  if (error || !product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Alert type="error" message={error || 'Product not found'} />
        <Link to="/products" className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 mt-4">
          <ArrowLeft className="w-4 h-4" /> Back to catalogue
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Back button */}
      <Link
        to="/products"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to catalogue
      </Link>

      {/* Product Overview Header */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Image */}
          <div className="lg:col-span-5 bg-slate-50 rounded-2xl border border-slate-100 p-8 flex items-center justify-center aspect-[4/3] relative">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.title}
                className="max-h-64 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling.style.display = 'flex';
                }}
              />
            ) : null}
            <div className={`w-full h-full items-center justify-center text-slate-300 ${product.image_url ? 'hidden' : 'flex'}`}>
              <Tag className="w-20 h-20" />
            </div>

            {product.is_demo_data && (
              <span className="absolute top-4 left-4 bg-amber-100 text-amber-800 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border border-amber-200">
                Demo Item
              </span>
            )}
          </div>

          {/* Specs & Pricing Summary */}
          <div className="lg:col-span-7 flex flex-col justify-between h-full space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                  {product.category}
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-semibold text-slate-600">{product.brand}</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {product.title}
              </h1>

              <p className="text-slate-600 text-sm mt-3 leading-relaxed">
                {product.description}
              </p>
            </div>

            {/* Quick Landed Cost Summary Callout */}
            <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200/70 flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                  Best Confirmed Landed Cost
                </span>
                <div className="text-2xl font-black text-slate-900 mt-0.5">
                  {product.min_total_cost_formatted}
                </div>
                <span className="text-xs text-slate-500">
                  Calculated from <strong>{offers.length} competing retailers</strong>
                </span>
              </div>

              {offers.length > 0 && (
                <button
                  onClick={() => handleSelectOffer(offers[0])}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-3 rounded-xl shadow-sm transition"
                >
                  Buy Best Value ({offers[0].retailer_name})
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* SmartCart AI Recommendation Engine */}
      {recommendation ? (
        <div className="bg-gradient-to-r from-indigo-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg relative overflow-hidden border border-indigo-800">
          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/30 border border-indigo-400/40 flex items-center justify-center text-indigo-300">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-base tracking-tight text-white flex items-center gap-2">
                    SmartCart AI Recommendation
                    <span className="text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                      Deterministic Offline Engine
                    </span>
                  </h3>
                  <p className="text-xs text-indigo-200">
                    Transparent rule-based math without paid external AI models
                  </p>
                </div>
              </div>

              {recommendation.savings_explanation && (
                <div className="bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 px-3 py-1 rounded-xl text-xs font-bold">
                  {recommendation.savings_explanation}
                </div>
              )}
            </div>

            <div className="bg-white/10 rounded-2xl p-5 border border-white/10 backdrop-blur-sm grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300 block">Recommended Retailer</span>
                <span className="text-lg font-black text-white">{recommendation.recommended_offer?.retailer_name}</span>
                <span className="text-xs text-indigo-200 block mt-0.5">
                  Est. delivery: {recommendation.recommended_offer?.estimated_delivery_days} days
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300 block">Best Landed Cost</span>
                <span className="text-2xl font-black text-white">{recommendation.best_confirmed_total_cost_formatted}</span>
                <span className="text-xs text-indigo-200 block mt-0.5">
                  (Item: {recommendation.recommended_offer?.product_price_formatted} + Shipping: {recommendation.recommended_offer?.shipping_cost_formatted})
                </span>
              </div>

              <div className="flex justify-start md:justify-end">
                <button
                  onClick={() => handleSelectOffer(recommendation.recommended_offer)}
                  className="bg-white hover:bg-slate-100 text-indigo-900 font-extrabold text-xs px-6 py-3 rounded-xl shadow-md transition"
                >
                  Proceed with Recommended Offer
                </button>
              </div>
            </div>

            {recommendation.recommendation_summary && (
              <p className="text-xs text-indigo-100 leading-relaxed bg-black/20 p-3.5 rounded-xl border border-white/5">
                💡 <strong>Decision Logic:</strong> {recommendation.recommendation_summary}
              </p>
            )}
          </div>
        </div>
      ) : !isAuthenticated ? (
        <div className="bg-indigo-50/70 border border-indigo-200/80 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-indigo-600 shrink-0" />
            <div>
              <p className="text-xs font-bold text-slate-800">Unlock SmartCart AI Recommendation & Savings Breakdown</p>
              <p className="text-xs text-slate-500">Sign in to view offline deterministic ranking explanations and automated savings calculations.</p>
            </div>
          </div>
          <Link
            to="/login"
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 transition shrink-0"
          >
            Sign In to Unlock AI
          </Link>
        </div>
      ) : null}

      {/* Competing Retailer Landed Cost Table */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Competing Retailer Offers ({offers.length})
            </h2>
            <p className="text-xs text-slate-500">
              Ranked strictly by verified Landed Cost (Item Price + Shipping). No hidden delivery fee surprises.
            </p>
          </div>
        </div>

        {offers.length > 0 ? (
          <div className="space-y-4">
            {offers.map((offer) => (
              <OfferCard
                key={offer.id}
                offer={offer}
                isRecommended={recommendation?.recommended_offer?.id === offer.id}
                onSelect={handleSelectOffer}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-500 text-xs">
            No active retailer offers available for this product.
          </div>
        )}
      </div>
    </div>
  );
}
