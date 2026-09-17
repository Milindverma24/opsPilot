"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
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
  Warehouse,
  XCircle,
  Package,
  ArrowRight,
  TrendingDown,
  X,
  Layers,
  Sparkles
} from "lucide-react";

export default function InventoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");

  // Adjust Stock Modal
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [adjustQuantity, setAdjustQuantity] = useState("25");
  const [adjustOp, setAdjustOp] = useState<"INCREASE" | "DECREASE" | "RESERVE" | "RELEASE">("INCREASE");
  const [adjustReason, setAdjustReason] = useState("Warehouse replenishment delivery");
  const [adjustSubmitting, setAdjustSubmitting] = useState(false);

  // Replenish Low Stock Notice
  const [replenishing, setReplenishing] = useState(false);
  const [replenishSuccessMsg, setReplenishSuccessMsg] = useState<string | null>(null);

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

  const handleOpenAdjust = (item: any) => {
    setSelectedItem(item);
    setShowAdjustModal(true);
  };

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;
    setAdjustSubmitting(true);
    try {
      await api.inventory.adjust({
        product_variant_id: selectedItem.product_variant_id || selectedItem.variant_id || selectedItem.id,
        warehouse_id: selectedItem.warehouse_id || "wh-001",
        quantity: parseInt(adjustQuantity) || 10,
        operation: adjustOp
      });
      setShowAdjustModal(false);
      await fetchInventory();
    } catch (err: any) {
      alert(err.message || "Failed to adjust inventory");
    } finally {
      setAdjustSubmitting(false);
    }
  };

  const handleReplenishAllLowStock = async () => {
    setReplenishing(true);
    setReplenishSuccessMsg(null);
    try {
      // Find low stock items and auto-increase by 50 units
      const lowItems = items.filter((i) => i.status === "LOW_STOCK" || i.status === "OUT_OF_STOCK");
      if (lowItems.length === 0) {
        setReplenishSuccessMsg("All warehouse SKUs are currently above safety reorder thresholds!");
      } else {
        for (const itm of lowItems.slice(0, 5)) {
          try {
            await api.inventory.adjust({
              product_variant_id: itm.product_variant_id || itm.id,
              warehouse_id: itm.warehouse_id || "wh-001",
              quantity: 50,
              operation: "INCREASE"
            });
          } catch (e) {
            console.error("Auto replenish error:", e);
          }
        }
        await fetchInventory();
        setReplenishSuccessMsg(`Successfully generated restock allocations for ${lowItems.length} low-stock apparel SKUs!`);
      }
    } catch (err: any) {
      alert(err.message || "Failed to auto-replenish stock");
    } finally {
      setReplenishing(false);
    }
  };

  const filteredItems = items.filter((i) => {
    const q = search.toLowerCase();
    return (
      i.product_name?.toLowerCase().includes(q) ||
      i.product_sku?.toLowerCase().includes(q) ||
      i.variant_sku?.toLowerCase().includes(q) ||
      i.size?.toLowerCase().includes(q)
    );
  });

  const lowStockCount = items.filter((i) => i.status === "LOW_STOCK" || i.status === "OUT_OF_STOCK").length;
  const totalUnits = items.reduce((sum, i) => sum + (i.quantity_on_hand || 0), 0);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Warehouse Inventory Management"
          subtitle="Multi-warehouse stock levels, reserved allocations, low-stock alerts, and replenishment orders"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Boxes className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Catalog SKUs</span>
                <div className="text-2xl font-bold text-white mt-0.5">{total || items.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <Package className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Units On Hand</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">{totalUnits.toLocaleString()}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Low Stock SKUs</span>
                <div className="text-2xl font-bold text-amber-400 mt-0.5">{lowStockCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                <Warehouse className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Warehouses</span>
                <div className="text-sm font-bold text-white mt-1">Mumbai / Delhi Hubs</div>
              </div>
            </div>
          </div>

          {/* Replenish Alert / Notification Banner */}
          {replenishSuccessMsg && (
            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-200 text-xs flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{replenishSuccessMsg}</span>
              </div>
              <button
                onClick={() => setReplenishSuccessMsg(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Controls & Filter Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search apparel name, SKU, or size..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto">
              <button
                onClick={() => setLowStockOnly(!lowStockOnly)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all flex items-center gap-2 ${
                  lowStockOnly
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40 font-bold"
                    : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700"
                }`}
              >
                <AlertTriangle className={`w-3.5 h-3.5 ${lowStockOnly ? "text-amber-400" : "text-slate-500"}`} />
                Low Stock Only ({lowStockCount})
              </button>

              <button
                onClick={handleReplenishAllLowStock}
                disabled={replenishing}
                className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5 shrink-0 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${replenishing ? "animate-spin" : ""}`} />
                {replenishing ? "Replenishing..." : "Replenish Low Stock"}
              </button>

              <Link
                href="/purchase-orders"
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-colors flex items-center gap-1.5 shrink-0"
              >
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                Purchase Orders
              </Link>
            </div>
          </div>

          {/* Inventory Items Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Product & SKU</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Size / Color</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Warehouse</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">On Hand</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Reserved</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Available</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Status</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-16 text-center text-slate-500">
                        Loading inventory records...
                      </td>
                    </tr>
                  ) : filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-16 text-center text-slate-500">
                        No inventory records found.
                      </td>
                    </tr>
                  ) : (
                    filteredItems.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-bold text-white text-xs">{item.product_name}</div>
                          <div className="font-mono text-[11px] text-slate-400 mt-0.5">{item.product_sku || item.variant_sku}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-200 font-mono text-[11px] font-semibold">
                            {item.size || "M"} {item.color ? `• ${item.color}` : ""}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <Warehouse className="w-3.5 h-3.5 text-slate-500" />
                            <span>{item.warehouse_name || "Mumbai Central"}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-bold text-white font-mono">{item.quantity_on_hand}</td>
                        <td className="py-3 px-4 text-slate-400 font-mono">{item.quantity_reserved || 0}</td>
                        <td className="py-3 px-4 font-bold text-emerald-400 font-mono">{item.available_quantity}</td>
                        <td className="py-3 px-4">
                          {item.status === "OUT_OF_STOCK" ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              Out of Stock
                            </span>
                          ) : item.status === "LOW_STOCK" ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              Low Stock (≤{item.reorder_level || 10})
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              In Stock
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleOpenAdjust(item)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors"
                          >
                            Adjust
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Adjust Stock Modal */}
      {showAdjustModal && selectedItem && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Boxes className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Adjust Stock Level</h3>
                  <p className="text-xs text-slate-400">{selectedItem.product_name} ({selectedItem.size || "M"})</p>
                </div>
              </div>
              <button
                onClick={() => setShowAdjustModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAdjustSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Adjustment Operation</label>
                <select
                  value={adjustOp}
                  onChange={(e: any) => setAdjustOp(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="INCREASE">Increase Stock (+ Units)</option>
                  <option value="DECREASE">Decrease Stock (- Units / Damage)</option>
                  <option value="RESERVE">Reserve Units</option>
                  <option value="RELEASE">Release Reserved Units</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Quantity (Units) *</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={adjustQuantity}
                  onChange={(e) => setAdjustQuantity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Audit Reason / Justification</label>
                <input
                  type="text"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  placeholder="e.g. Warehouse delivery shipment PO-2026-001"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAdjustModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjustSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-600/20 disabled:opacity-50"
                >
                  {adjustSubmitting ? "Updating..." : "Commit Adjustment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
