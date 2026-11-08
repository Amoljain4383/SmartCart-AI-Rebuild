import React from 'react';
import { Link } from 'react-router-dom';
import { Store, ArrowRight, Tag } from 'lucide-react';

export default function ProductCard({ product }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md hover:border-indigo-200 transition flex flex-col h-full overflow-hidden group">
      {/* Product Image & Badges */}
      <div className="relative bg-slate-100 aspect-[4/3] flex items-center justify-center p-6 overflow-hidden">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-full object-contain group-hover:scale-105 transition duration-300"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling.style.display = 'flex';
            }}
          />
        ) : null}
        <div
          className={`w-full h-full items-center justify-center text-slate-300 ${
            product.image_url ? 'hidden' : 'flex'
          }`}
        >
          <Tag className="w-16 h-16" />
        </div>

        {/* Demo pill */}
        {product.is_demo_data && (
          <span className="absolute top-3 left-3 bg-amber-100/90 backdrop-blur-sm text-amber-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border border-amber-200">
            Demo Item
          </span>
        )}

        {/* Brand */}
        <span className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm text-slate-700 text-xs font-semibold px-2.5 py-1 rounded-lg border border-slate-200/80 shadow-sm">
          {product.brand}
        </span>
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          <span className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider">
            {product.category}
          </span>
          <h3 className="font-bold text-slate-900 mt-1 line-clamp-2 group-hover:text-indigo-600 transition text-base">
            {product.title}
          </h3>
          <p className="text-slate-500 text-xs mt-1.5 line-clamp-2 leading-relaxed">
            {product.description}
          </p>
        </div>

        {/* Price & Action */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-end justify-between">
          <div>
            <span className="text-[10px] text-slate-400 font-medium block uppercase tracking-wider">
              Best Landed Cost
            </span>
            <div className="text-lg font-extrabold text-slate-900 leading-tight">
              {product.min_total_cost_formatted || 'Price on request'}
            </div>
            <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-0.5">
              <Store className="w-3 h-3 text-slate-400" />
              <span>{product.offer_count} retailer {product.offer_count === 1 ? 'offer' : 'offers'}</span>
            </div>
          </div>

          <Link
            to={`/products/${product.id}`}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold shadow-sm transition group/btn"
          >
            <span>Compare</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition" />
          </Link>
        </div>
      </div>
    </div>
  );
}
