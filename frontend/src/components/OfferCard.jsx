import React from 'react';
import { Star, Truck, CheckCircle2, AlertTriangle, ArrowRight, Shield, Award } from 'lucide-react';

export default function OfferCard({ offer, isRecommended, onSelect }) {
  const isBestCost = offer.comparison_rank === 1;

  return (
    <div
      className={`rounded-2xl border transition relative overflow-hidden bg-white p-5 ${
        isRecommended
          ? 'border-indigo-400 ring-2 ring-indigo-500/20 shadow-md'
          : isBestCost
          ? 'border-emerald-300 shadow-sm'
          : 'border-slate-200/80 hover:border-slate-300'
      }`}
    >
      {/* Top Ribbons */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-900 text-base">{offer.retailer_name}</span>
          {isRecommended && (
            <span className="inline-flex items-center gap-1 bg-indigo-600 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-sm">
              <Award className="w-3 h-3" />
              AI Best Value
            </span>
          )}
          {!isRecommended && isBestCost && (
            <span className="inline-flex items-center gap-1 bg-emerald-600 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-sm">
              <CheckCircle2 className="w-3 h-3" />
              Lowest Total Cost
            </span>
          )}
        </div>

        {/* Rating */}
        <div className="flex items-center gap-1 text-xs text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200/60">
          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
          <span className="font-semibold text-slate-800">{offer.rating_float}</span>
          <span className="text-slate-400 text-[10px]">({offer.review_count})</span>
        </div>
      </div>

      {/* Breakdown Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-4 p-4 rounded-xl bg-slate-50/70 border border-slate-100">
        <div>
          <span className="text-[11px] font-medium text-slate-400 block uppercase tracking-wider">Item Price</span>
          <div className="text-base font-semibold text-slate-800 mt-0.5">
            {offer.product_price_formatted}
          </div>
        </div>

        <div>
          <span className="text-[11px] font-medium text-slate-400 block uppercase tracking-wider">Shipping Fee</span>
          <div className="text-base font-semibold text-slate-800 mt-0.5">
            {offer.shipping_cost_paise === 0 ? (
              <span className="text-emerald-600 font-bold">FREE Delivery</span>
            ) : (
              offer.shipping_cost_formatted
            )}
          </div>
        </div>

        <div>
          <span className="text-[11px] font-bold text-indigo-700 block uppercase tracking-wider">True Landed Cost</span>
          <div className="text-xl font-extrabold text-slate-900 mt-0.5">
            {offer.total_cost_formatted}
          </div>
        </div>
      </div>

      {/* Delivery & Policies */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 pt-2 border-t border-slate-100">
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1.5 text-slate-600">
            <Truck className="w-4 h-4 text-slate-400" />
            <span>Est. delivery: <strong>{offer.estimated_delivery_days} days</strong></span>
          </span>

          <span className="flex items-center gap-1.5 text-slate-600">
            <Shield className="w-4 h-4 text-slate-400" />
            <span>{offer.return_policy || 'Standard Returns'}</span>
          </span>

          {offer.stock_status === 'in_stock' ? (
            <span className="text-emerald-600 font-medium flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> In Stock
            </span>
          ) : (
            <span className="text-amber-600 font-medium flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> {offer.stock_status}
            </span>
          )}
        </div>

        <button
          onClick={() => onSelect(offer)}
          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition shadow-sm ${
            isRecommended
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
              : 'bg-slate-900 hover:bg-slate-800 text-white'
          }`}
        >
          <span>Select for Checkout</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Explanation footnote */}
      {offer.rank_explanation && (
        <div className="mt-3 pt-2 text-[11px] text-slate-400 border-t border-slate-100/60 italic">
          {offer.rank_explanation}
        </div>
      )}
    </div>
  );
}
