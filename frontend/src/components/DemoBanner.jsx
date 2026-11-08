import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function DemoBanner() {
  return (
    <aside aria-label="Demo Notice" className="bg-amber-500/10 border-b border-amber-500/20 text-amber-900 px-4 py-2 text-xs font-medium">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-center">
        <AlertCircle className="w-4 h-4 text-amber-700 shrink-0" />
        <span>
          <strong>SmartCart AI Demo:</strong> All catalogue products, retailer prices, and stock statuses are simulated for demonstration purposes. PayPal checkout operates in PayPal Sandbox and represents a simulated purchase.
        </span>
      </div>
    </aside>
  );
}
