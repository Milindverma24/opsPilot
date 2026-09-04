"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Boxes,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  ShoppingBag,
  Building2,
  Layers,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api";

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await api.purchaseOrders.list();
      setOrders(res.purchase_orders || []);
    } catch (err) {
      console.error("Failed to load purchase orders:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const filtered = orders.filter((o) => {
    if (filter === "ALL") return true;
    return o.status === filter;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Procurement & Purchase Orders"
          subtitle="Autonomous replenishment pipeline triggered by Inventory Operations AI upon low stock threshold"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Total POs</span>
              <div className="mt-2 text-3xl font-extrabold text-slate-900">{orders.length}</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Active / Approved</span>
              <div className="mt-2 text-3xl font-extrabold text-blue-600">
                {orders.filter((o) => o.status === "APPROVED").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Fulfilled</span>
              <div className="mt-2 text-3xl font-extrabold text-emerald-600">
                {orders.filter((o) => o.status === "FULFILLED").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Replenishment Trigger</span>
              <div className="mt-2 text-sm font-bold text-slate-900">
                Inventory AI &lt; 20 units
              </div>
            </div>
          </div>

          {/* Action / Filter Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {["ALL", "APPROVED", "FULFILLED", "DRAFT"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilter(st)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition ${
                    filter === st
                      ? "bg-slate-900 text-white"
                      : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <button
              onClick={fetchOrders}
              className="p-2 text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-xl"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {/* Table */}
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase">
                  <th className="p-4">PO Number</th>
                  <th className="p-4">Vendor</th>
                  <th className="p-4">Department</th>
                  <th className="p-4">Items</th>
                  <th className="p-4">Total Amount</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      Loading purchase orders...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      No purchase orders recorded yet. As inventory levels dip below safe stock, Inventory AI automatically issues purchase orders.
                    </td>
                  </tr>
                ) : (
                  filtered.map((po) => (
                    <tr key={po.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-mono font-bold text-slate-900">{po.po_number}</td>
                      <td className="p-4 font-semibold text-slate-800">{po.vendor_name}</td>
                      <td className="p-4 text-slate-600">{po.department}</td>
                      <td className="p-4 font-bold text-blue-600">{po.items_count} items</td>
                      <td className="p-4 font-bold text-slate-900">
                        ₹{Number(po.total || 0).toLocaleString()}
                      </td>
                      <td className="p-4">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                            po.status === "FULFILLED"
                              ? "bg-emerald-100 text-emerald-800"
                              : po.status === "APPROVED"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {po.status}
                        </span>
                      </td>
                      <td className="p-4 text-right text-slate-500 font-mono text-[11px]">
                        {po.created_at ? new Date(po.created_at).toLocaleDateString() : "Today"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
