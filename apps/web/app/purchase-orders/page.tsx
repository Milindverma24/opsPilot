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
  Plus,
  X,
  CreditCard,
  DollarSign
} from "lucide-react";
import { api } from "@/lib/api";

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Create PO Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVendor, setNewVendor] = useState("LoomCraft Textiles");
  const [newDepartment, setNewDepartment] = useState("Inventory Restock");
  const [newTotal, setNewTotal] = useState("45000");
  const [createSubmitting, setCreateSubmitting] = useState(false);

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

  const handleApprovePO = async (id: string) => {
    setActionLoading(id);
    try {
      await api.purchaseOrders.approve(id);
      await fetchOrders();
    } catch (err: any) {
      alert(err.message || "Failed to approve purchase order");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateSubmitting(true);
    try {
      await api.purchaseOrders.create({
        vendor_name: newVendor,
        department: newDepartment,
        total: parseFloat(newTotal) || 10000
      });
      setShowCreateModal(false);
      await fetchOrders();
    } catch (err: any) {
      alert(err.message || "Failed to create purchase order");
    } finally {
      setCreateSubmitting(false);
    }
  };

  const filtered = orders.filter((o) => {
    if (filter === "ALL") return true;
    return o.status === filter;
  });

  const totalSpend = orders.reduce((sum, o) => sum + (o.total || 0), 0);
  const pendingCount = orders.filter((o) => o.status === "DRAFT" || o.status === "PENDING").length;
  const approvedCount = orders.filter((o) => o.status === "APPROVED").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Procurement & Purchase Orders"
          subtitle="Autonomous replenishment pipeline triggered by Inventory Operations AI upon low stock threshold"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total POs</span>
                <div className="text-2xl font-bold text-white mt-0.5">{orders.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Approval</span>
                <div className="text-2xl font-bold text-amber-400 mt-0.5">{pendingCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Approved POs</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">{approvedCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                <CreditCard className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Procurement Value</span>
                <div className="text-2xl font-bold text-white mt-0.5">₹{Math.round(totalSpend).toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* Action and Filter Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs overflow-x-auto w-full sm:w-auto">
              {["ALL", "DRAFT", "APPROVED", "FULFILLED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilter(st)}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    filter === st
                      ? "bg-slate-800 text-white font-bold shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {st === "ALL" ? "All Orders" : st}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              <Link
                href="/inventory"
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-colors flex items-center gap-1.5 shrink-0"
              >
                <Boxes className="w-3.5 h-3.5 text-blue-400" />
                View Stock Levels
              </Link>

              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5 shrink-0"
              >
                <Plus className="w-4 h-4" />
                Create Purchase Order
              </button>
            </div>
          </div>

          {/* PO List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">PO Number</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Vendor / Supplier</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Department</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Amount</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Status</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-16 text-center text-slate-500">
                        Loading purchase orders...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-16 text-center text-slate-500">
                        No purchase orders matching criteria.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((po) => (
                      <tr key={po.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <span className="font-mono text-xs font-bold text-white bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                            {po.po_number}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{po.vendor_name}</div>
                          <span className="text-[10px] text-slate-500">Apparel Supplier</span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-300">{po.department || "Inventory"}</td>
                        <td className="py-3.5 px-4 font-bold text-white font-mono">₹{po.total?.toLocaleString()}</td>
                        <td className="py-3.5 px-4">
                          {po.status === "APPROVED" ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Approved
                            </span>
                          ) : po.status === "DRAFT" ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              Draft Review
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                              {po.status}
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          {po.status === "DRAFT" ? (
                            <button
                              onClick={() => handleApprovePO(po.id)}
                              disabled={actionLoading === po.id}
                              className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
                            >
                              Approve
                            </button>
                          ) : (
                            <span className="text-[11px] text-slate-500">Approved</span>
                          )}
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

      {/* Create Purchase Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Create Purchase Order</h3>
                  <p className="text-xs text-slate-400">Procure fabric batches from verified suppliers</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePO} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Vendor / Mill Supplier</label>
                <input
                  type="text"
                  required
                  value={newVendor}
                  onChange={(e) => setNewVendor(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Department</label>
                <input
                  type="text"
                  value={newDepartment}
                  onChange={(e) => setNewDepartment(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Total Procurement Cost (₹) *</label>
                <input
                  type="number"
                  required
                  min="1000"
                  value={newTotal}
                  onChange={(e) => setNewTotal(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-600/20 disabled:opacity-50"
                >
                  {createSubmitting ? "Generating..." : "Submit PO"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
