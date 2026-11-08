import React from 'react';
import { ShoppingCart, ShieldCheck, Heart, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 mt-20 border-t border-slate-800 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Col */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2 text-white">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <ShoppingCart className="w-4 h-4" />
              </div>
              <span className="font-bold text-lg tracking-tight">SmartCart AI</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed max-w-md">
              SmartCart AI solves online shopping deception by comparing total landed cost (item price + known shipping charges) across multiple retailers instead of surface sticker prices. Built with an offline, transparent deterministic recommendation engine.
            </p>
            <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Paise-precision monetary calculations & verified server-side PayPal Sandbox capture.</span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">Navigation</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/" className="hover:text-indigo-400 transition">Home</Link>
              </li>
              <li>
                <Link to="/products" className="hover:text-indigo-400 transition">Product Catalogue</Link>
              </li>
              <li>
                <Link to="/orders" className="hover:text-indigo-400 transition">Order History</Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-indigo-400 transition">Account Sign In</Link>
              </li>
            </ul>
          </div>

          {/* Hackathon Disclaimer */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-3">Hackathon Demo Notice</h4>
            <p className="text-[11px] leading-relaxed text-slate-400">
              This application is an educational prototype built for hackathon evaluation. Products, retailer offers, pricing, and shipping rates are simulated demonstration data. PayPal checkout operates strictly in the PayPal Sandbox environment.
            </p>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© 2026 SmartCart AI. Built for Smart Shopping Hackathon.</p>
          <p className="flex items-center gap-1 mt-2 sm:mt-0">
            Engineered with <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" /> using FastAPI, SQLite, React & Tailwind CSS.
          </p>
        </div>
      </div>
    </footer>
  );
}
