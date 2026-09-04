"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  Boxes, 
  AlertTriangle, 
  CheckCircle2, 
  Plus, 
  Minus, 
  RefreshCw,
  Search,
  Filter,
  Warehouse
} from "lucide-react";

export default function InventoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const res = await api.inventory.list({
        page,
        page_size: 50,
        low_stock_only: lowStockOnly || undefined
      });
      setItems(res.data || []);
      setTotal(res.meta?.total || 0);
    } catch (err) {
      console.error("Failed to load inventory:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [page, lowStockOnly]);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Boxes className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Warehouse Inventory</h1>
              <p className="text-sm text-slate-400">Multi-warehouse stock levels, reservations, and low-stock alerts.</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg">
            <input
              type="checkbox"
              checked={lowStockOnly}
              onChange={(e) => {
                setLowStockOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-700 text-blue-600 focus:ring-blue-500"
            />
            <span className="flex items-center gap-1 text-amber-400">
              <AlertTriangle className="w-3.5 h-3.5" /> Low Stock Alerts Only
            </span>
          </label>
          <button 
            onClick={fetchInventory}
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Product</th>
                <th className="px-6 py-3.5">Variant SKU</th>
                <th className="px-6 py-3.5">Size / Color</th>
                <th className="px-6 py-3.5">Warehouse</th>
                <th className="px-6 py-3.5 text-center">On Hand</th>
                <th className="px-6 py-3.5 text-center">Reserved</th>
                <th className="px-6 py-3.5 text-center">Available</th>
                <th className="px-6 py-3.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    Loading inventory records...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    No inventory records found.
                  </td>
                </tr>
              ) : (
                items.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">
                      <div>{inv.product_name}</div>
                      <div className="text-xs font-mono text-slate-400">{inv.product_sku}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-300">{inv.variant_sku}</td>
                    <td className="px-6 py-4 text-xs text-slate-300">{inv.size} • {inv.color}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <Warehouse className="w-3.5 h-3.5 text-slate-500" />
                        <span>{inv.warehouse_code}</span>
                      </div>
                      <div className="text-[11px] text-slate-500">{inv.warehouse_name}</div>
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-slate-300">{inv.quantity_on_hand}</td>
                    <td className="px-6 py-4 text-center font-mono text-amber-400">{inv.quantity_reserved}</td>
                    <td className="px-6 py-4 text-center font-mono font-bold text-white">
                      {inv.available_quantity}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {inv.status === "OUT_OF_STOCK" ? (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">
                          Out of Stock
                        </span>
                      ) : inv.status === "LOW_STOCK" ? (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-semibold flex items-center gap-1 justify-end">
                          <AlertTriangle className="w-3 h-3" /> Low Stock
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                          In Stock
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
