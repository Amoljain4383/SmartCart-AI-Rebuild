import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Search,
  Tag,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  RotateCcw,
  Star,
  Truck,
  Award,
  AlertCircle,
  Cpu,
  SlidersHorizontal,
} from 'lucide-react';
import Alert from './Alert';

const PROMPT_SUGGESTIONS = [
  'Sony WH-1000XM5 under ₹28,000',
  'Apple Watch Series 9 under 45k',
  'Kindle Paperwhite under 15000',
  'Logitech wireless mouse under 9k',
  'Dyson cordless vacuum cleaner',
];

export default function AICopilotBar({
  onSearch,
  onReset,
  loading = false,
  copilotData = null,
  error = null,
}) {
  const [inputMessage, setInputMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !loading) {
      onSearch(inputMessage.trim());
    }
  };

  const handleChipClick = (suggestion) => {
    setInputMessage(suggestion);
    if (!loading) {
      onSearch(suggestion);
    }
  };

  const handleClear = () => {
    setInputMessage('');
    if (onReset) onReset();
  };

  const topOffer = copilotData?.top_recommendation;
  const intent = copilotData?.extracted_intent;

  return (
    <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-indigo-950/20 border border-indigo-700/40 relative overflow-hidden">
      {/* Background Glow Accents */}
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-indigo-400/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 bg-indigo-500/30 text-indigo-200 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-indigo-400/30 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            AI Shopping Copilot
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white">
            Find the Best Verified Deal in Plain English
          </h2>
          <p className="text-xs sm:text-sm text-indigo-200/80 mt-0.5">
            Describe what you need, your budget, or preferred features. Our AI extracts requirements while the backend audits True Landed Cost.
          </p>
        </div>

        {/* Engine mode pill */}
        {copilotData && (
          <div className="self-start sm:self-center shrink-0">
            {copilotData.copilot_mode === 'gemini_ai' ? (
              <span className="inline-flex items-center gap-1.5 bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 px-3 py-1.5 rounded-xl text-xs font-semibold shadow-sm">
                <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                Gemini 3.8 Flash
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 bg-indigo-400/20 text-indigo-200 border border-indigo-300/30 px-3 py-1.5 rounded-xl text-xs font-semibold shadow-sm" title="Operating via local deterministic regex parser">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-300" />
                Deterministic Local Engine
              </span>
            )}
          </div>
        )}
      </div>

      {/* Natural Language Search Input Form */}
      <form onSubmit={handleSubmit} className="relative z-10">
        <div className="flex flex-col sm:flex-row gap-2.5 bg-white/10 backdrop-blur-md p-2 rounded-2xl border border-white/20 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-500/30 transition">
          <div className="flex items-center flex-1 pl-3 text-indigo-200">
            <Search className="w-5 h-5 shrink-0 mr-2.5 text-indigo-300" />
            <input
              type="text"
              placeholder="e.g. 'Sony WH-1000XM5 headphones under ₹28,000 with long battery life'..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={loading}
              className="w-full bg-transparent text-sm text-white placeholder-indigo-200/60 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            {copilotData && (
              <button
                type="button"
                onClick={handleClear}
                disabled={loading}
                className="px-3 py-2 text-xs font-semibold text-indigo-200 hover:text-white bg-white/10 hover:bg-white/20 rounded-xl transition flex items-center gap-1 shrink-0"
                title="Reset Copilot search"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            )}

            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs sm:text-sm px-5 py-2.5 rounded-xl shadow-md transition flex items-center justify-center gap-2 shrink-0"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Ask Copilot</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Prompt Suggestion Chips */}
      <div className="relative z-10 mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold text-indigo-300/90 uppercase tracking-wider flex items-center gap-1">
          <SlidersHorizontal className="w-3 h-3" /> Try asking:
        </span>
        {PROMPT_SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => handleChipClick(suggestion)}
            disabled={loading}
            className="text-xs bg-white/10 hover:bg-white/20 active:bg-white/30 text-indigo-100 border border-white/15 px-3 py-1 rounded-full transition disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="relative z-10 mt-4">
          <Alert type="error" message={error} />
        </div>
      )}

      {/* Extracted Criteria & Top Recommendation Result View */}
      {copilotData && (
        <div className="relative z-10 mt-6 pt-6 border-t border-indigo-700/50 space-y-4">
          {/* Extracted Criteria Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-indigo-200 font-medium">Extracted Intent:</span>

            {intent?.search_query && (
              <span className="inline-flex items-center gap-1 bg-white/15 text-white text-xs px-2.5 py-1 rounded-lg border border-white/20">
                <Search className="w-3 h-3 text-indigo-300" />
                <span>{intent.search_query}</span>
              </span>
            )}

            {intent?.category && (
              <span className="inline-flex items-center gap-1 bg-white/15 text-white text-xs px-2.5 py-1 rounded-lg border border-white/20">
                <Tag className="w-3 h-3 text-indigo-300" />
                <span>Category: {intent.category}</span>
              </span>
            )}

            {intent?.brand && (
              <span className="inline-flex items-center gap-1 bg-white/15 text-white text-xs px-2.5 py-1 rounded-lg border border-white/20">
                <span>Brand: {intent.brand}</span>
              </span>
            )}

            {intent?.max_budget_rupees && (
              <span className="inline-flex items-center gap-1 bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 text-xs px-2.5 py-1 rounded-lg font-semibold">
                <CheckCircle2 className="w-3 h-3 text-emerald-300" />
                <span>Budget Cap: ₹{intent.max_budget_rupees.toLocaleString('en-IN')}</span>
              </span>
            )}

            {intent?.key_features?.map((feature) => (
              <span
                key={feature}
                className="bg-indigo-400/20 text-indigo-200 border border-indigo-300/30 text-xs px-2.5 py-1 rounded-lg"
              >
                {feature}
              </span>
            ))}
          </div>

          {/* Explanation Text */}
          {copilotData.explanation && (
            <p className="text-sm text-indigo-100/90 leading-relaxed bg-white/5 p-3.5 rounded-xl border border-white/10">
              {copilotData.explanation}
            </p>
          )}

          {/* Featured Top Recommendation Card */}
          {topOffer && (
            <div className="bg-white text-slate-900 rounded-2xl p-5 shadow-lg border border-indigo-200">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  {topOffer.is_shipping_known ? (
                    <span className="inline-flex items-center gap-1 bg-indigo-600 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-sm">
                      <Award className="w-3.5 h-3.5" />
                      AI Best Value — True Landed Cost
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 bg-amber-600 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-sm">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Simulated Offer — Unconfirmed Shipping
                    </span>
                  )}
                  <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
                    {topOffer.recommended_retailer}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-xs text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200/60">
                  <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                  <span className="font-semibold text-slate-800">{topOffer.retailer_rating}</span>
                  <span className="text-slate-400 text-[10px]">({topOffer.review_count})</span>
                </div>
              </div>

              {/* Product and Cost Breakdown Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100 my-3">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Recommended Product</span>
                  <h4 className="font-bold text-slate-900 text-sm mt-0.5 line-clamp-1">{topOffer.product_title}</h4>
                </div>

                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Landed Cost Audit</span>
                  <div className="text-sm font-semibold text-slate-800 mt-0.5">
                    {topOffer.product_price_formatted} +{' '}
                    {!topOffer.is_shipping_known ? (
                      <span className="text-amber-600 font-bold">Unconfirmed Shipping</span>
                    ) : topOffer.shipping_cost_formatted.includes('0.00') ? (
                      <span className="text-emerald-600 font-bold">FREE Delivery</span>
                    ) : (
                      topOffer.shipping_cost_formatted
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {topOffer.is_shipping_known ? 'Total Landed Cost' : 'Confirmed Landed Cost'}
                  </span>
                  <div
                    className={`text-base font-extrabold mt-0.5 ${
                      topOffer.is_shipping_known ? 'text-indigo-700' : 'text-amber-700'
                    }`}
                  >
                    {topOffer.is_shipping_known ? topOffer.landed_cost_formatted : 'Unconfirmed / Incomplete'}
                  </div>
                </div>
              </div>

              {/* Savings rationale & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                <div className="text-xs text-slate-600">
                  {!topOffer.is_shipping_known ? (
                    <span className="text-amber-700 font-semibold bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 inline-block">
                      Shipping cost is unconfirmed. Total landed cost cannot be guaranteed.
                    </span>
                  ) : topOffer.savings_explanation ? (
                    <span className="text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-100 inline-block">
                      {topOffer.savings_explanation}
                    </span>
                  ) : (
                    <span className="text-slate-500">
                      Estimated delivery in {topOffer.delivery_days} day(s) from {topOffer.recommended_retailer}.
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => navigate(`/products/${topOffer.product_id}`)}
                    className="px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-indigo-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
                  >
                    Compare All Offers
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate(`/checkout?offerId=${topOffer.offer_id}`)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow transition flex items-center gap-1.5"
                  >
                    <span>Select for Checkout</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Demo-data disclosure notice from backend response */}
          {copilotData.notice && (
            <div className="text-[11px] text-indigo-200/80 bg-white/5 px-3.5 py-2 rounded-xl border border-white/10 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 text-amber-300 shrink-0" />
              <span>{copilotData.notice}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
