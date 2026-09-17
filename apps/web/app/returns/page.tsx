"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { 
  RotateCcw, 
  CreditCard, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  RefreshCw,
  Search,
  Filter,
  Plus,
  ShieldCheck,
  Package,
  BookOpen,
  X,
  ChevronRight,
  Truck
} from "lucide-react";
import { api } from "@/lib/api";

export default function ReturnsPage() {
  const [activeTab, setActiveTab] = useState<"returns" | "refunds">("returns");
  const [returnsList, setReturnsList] = useState<any[]>([]);
  const [refundsList, setRefundsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRagModal, setShowRagModal] = useState(false);
  const [ragQuery, setRagQuery] = useState("30 day return window and reverse pickup policy");
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [ragLoading, setRagLoading] = useState(false);

  // New Return Form State
  const [newOrderId, setNewOrderId] = useState("");
  const [newCustomerId, setNewCustomerId] = useState("");
  const [newReason, setNewReason] = useState("Wrong size (Size exchange requested)");
  const [createSubmitting, setCreateSubmitting] = useState(false);

  const fetchReturnsAndRefunds = async () => {
    setLoading(true);
    try {
      const [retRes, refRes] = await Promise.all([
        api.returns.list({ status: statusFilter === "ALL" ? undefined : statusFilter }),
        api.refunds.list()
      ]);
      setReturnsList(retRes.data || []);
      setRefundsList(refRes.data || refRes.refunds || []);
    } catch (err) {
      console.error("Failed to load returns/refunds:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturnsAndRefunds();
  }, [statusFilter]);

  const handleApproveReturn = async (id: string) => {
    setActionLoading(id);
    try {
      await api.returns.approve(id);
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert(err.message || "Failed to approve return.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectReturn = async (id: string) => {
    setActionLoading(id);
    try {
      await api.returns.reject(id);
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert(err.message || "Failed to reject return.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecuteRefund = async (id: string) => {
    setActionLoading(id);
    try {
      await api.refunds.execute(id);
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert(err.message || "Failed to execute refund.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrderId.trim()) return;
    setCreateSubmitting(true);
    try {
      await api.returns.request({
        order_id: newOrderId.trim(),
        customer_id: newCustomerId.trim() || "cust-001",
        items: [{ order_item_id: "itm-001", quantity: 1, reason: newReason }],
        reason: newReason
      });
      setShowCreateModal(false);
      setNewOrderId("");
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert("Failed to initiate return: " + err.message);
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleInspectRag = async () => {
    setRagLoading(true);
    setShowRagModal(true);
    try {
      const res = await api.knowledge.search(ragQuery);
      setRagResults(res.results || []);
    } catch (err) {
      console.error("RAG search failed:", err);
    } finally {
      setRagLoading(false);
    }
  };

  const filteredReturns = returnsList.filter((r) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (r.return_number || "").toLowerCase().includes(q) ||
      (r.order_number || "").toLowerCase().includes(q) ||
      (r.customer_name || "").toLowerCase().includes(q) ||
      (r.reason || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100 selection:bg-blue-600 selection:text-white">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Returns & Reverse Logistics"
          subtitle="Policy inspection approvals, automated courier pickup dispatch, and RAG return policy validation."
        />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Return Requests</span>
              <div className="text-2xl font-black text-white">{returnsList.length}</div>
              <div className="text-[11px] text-blue-400">Doorstep reverse courier tracking</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Inspection</span>
              <div className="text-2xl font-black text-amber-400">
                {returnsList.filter((r) => r.status === "REQUESTED").length}
              </div>
              <div className="text-[11px] text-amber-300/80">Requires QA condition signoff</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Approved Returns</span>
              <div className="text-2xl font-black text-emerald-400">
                {returnsList.filter((r) => r.status === "APPROVED").length}
              </div>
              <div className="text-[11px] text-emerald-300/80">Dispatched for warehouse intake</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Disbursed Refunds</span>
              <div className="text-2xl font-black text-indigo-400">{refundsList.length}</div>
              <div className="text-[11px] text-indigo-300/80">Automated UPI / Card reversal</div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-4 rounded-2xl backdrop-blur-md">
            {/* Search & Tabs */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Tab Selector */}
              <div className="flex bg-slate-950 border border-slate-800 rounded-xl p-1">
                <button
                  onClick={() => setActiveTab("returns")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === "returns"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Return Requests ({returnsList.length})
                </button>
                <button
                  onClick={() => setActiveTab("refunds")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === "refunds"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Disbursed Refunds ({refundsList.length})
                </button>
              </div>

              {/* Status Filter */}
              {activeTab === "returns" && (
                <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1 text-xs">
                  {["ALL", "REQUESTED", "APPROVED", "REJECTED"].map((st) => (
                    <button
                      key={st}
                      onClick={() => setStatusFilter(st)}
                      className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                        statusFilter === st
                          ? "bg-slate-800 text-white"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              )}

              {/* Search */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search returns or buyer..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2.5">
              <button
                onClick={handleInspectRag}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2"
                title="Verify Return Policy via RAG vector search"
              >
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                <span>Inspect RAG Return SOP</span>
              </button>

              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-md shadow-blue-600/20 flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Initiate Return</span>
              </button>

              <button
                onClick={fetchReturnsAndRefunds}
                className="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Refresh Table"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Main Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            {activeTab === "returns" ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3.5">Return #</th>
                      <th className="px-6 py-3.5">Order</th>
                      <th className="px-6 py-3.5">Customer</th>
                      <th className="px-6 py-3.5">Reason & Inspection</th>
                      <th className="px-6 py-3.5">Status</th>
                      <th className="px-6 py-3.5">Requested At</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {loading ? (
                      <tr><td colSpan={7} className="px-6 py-12 text-center text-slate-400 font-sans">Loading return records...</td></tr>
                    ) : filteredReturns.length === 0 ? (
                      <tr><td colSpan={7} className="px-6 py-12 text-center text-slate-400 font-sans">No returns match the current criteria.</td></tr>
                    ) : filteredReturns.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-6 py-4 font-bold text-white">{r.return_number}</td>
                        <td className="px-6 py-4 text-blue-400">{r.order_number || "—"}</td>
                        <td className="px-6 py-4 font-sans text-slate-200">{r.customer_name || "Buyer"}</td>
                        <td className="px-6 py-4 font-sans text-slate-300 max-w-xs truncate">{r.reason}</td>
                        <td className="px-6 py-4 font-sans">
                          <span className={`px-2.5 py-1 text-[10px] font-bold rounded-full ${
                            r.status === "APPROVED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : r.status === "REJECTED"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}>
                            {r.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-500 text-[11px]">
                          {r.requested_at ? new Date(r.requested_at).toLocaleDateString() : "—"}
                        </td>
                        <td className="px-6 py-4 text-right font-sans">
                          {r.status === "REQUESTED" ? (
                            <div className="inline-flex items-center gap-2">
                              <button
                                onClick={() => handleApproveReturn(r.id)}
                                disabled={actionLoading === r.id}
                                className="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-semibold disabled:opacity-50"
                              >
                                {actionLoading === r.id ? "..." : "Approve"}
                              </button>
                              <button
                                onClick={() => handleRejectReturn(r.id)}
                                disabled={actionLoading === r.id}
                                className="px-2.5 py-1 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-semibold disabled:opacity-50"
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span className="text-[11px] text-slate-500">Processed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3.5">Refund #</th>
                      <th className="px-6 py-3.5">Order</th>
                      <th className="px-6 py-3.5">Amount</th>
                      <th className="px-6 py-3.5">Reason</th>
                      <th className="px-6 py-3.5">Status</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {loading ? (
                      <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400 font-sans">Loading refunds...</td></tr>
                    ) : refundsList.length === 0 ? (
                      <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400 font-sans">No refunds on record.</td></tr>
                    ) : refundsList.map((rf) => (
                      <tr key={rf.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-6 py-4 font-bold text-white">{rf.refund_number || `RF-${rf.id.slice(0, 8)}`}</td>
                        <td className="px-6 py-4 text-blue-400">{rf.order_number || rf.order_id?.slice(0, 8) || "—"}</td>
                        <td className="px-6 py-4 font-bold text-emerald-400 font-sans">₹{rf.amount}</td>
                        <td className="px-6 py-4 font-sans text-slate-300">{rf.reason}</td>
                        <td className="px-6 py-4 font-sans">
                          <span className={`px-2.5 py-1 text-[10px] font-bold rounded-full ${
                            rf.status === "COMPLETED" || rf.status === "EXECUTED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          }`}>
                            {rf.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-sans">
                          {(rf.status === "APPROVED" || rf.status === "PENDING") && (
                            <button
                              onClick={() => handleExecuteRefund(rf.id)}
                              disabled={actionLoading === rf.id}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
                            >
                              {actionLoading === rf.id ? "Processing..." : "Execute Payout"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Modal: Initiate Return */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-white text-base">Initiate Return Request</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateReturn} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Order ID or Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ord-001 or ORD-648291"
                  value={newOrderId}
                  onChange={(e) => setNewOrderId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Customer ID (Optional)</label>
                <input
                  type="text"
                  placeholder="cust-001"
                  value={newCustomerId}
                  onChange={(e) => setNewCustomerId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Reason for Return</label>
                <select
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white"
                >
                  <option value="Wrong size (Size exchange requested)">Wrong size (Size exchange requested)</option>
                  <option value="Fit too tight in chest/shoulders">Fit too tight in chest/shoulders</option>
                  <option value="Color nuance different from photos">Color nuance different from photos</option>
                  <option value="Fabric defect or stitching issue">Fabric defect or stitching issue</option>
                  <option value="Changed mind / Unwanted gift">Changed mind / Unwanted gift</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold disabled:opacity-50"
                >
                  {createSubmitting ? "Submitting..." : "Submit Return"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: RAG SOP Inspector */}
      {showRagModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-5 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-white text-base">RAG Return Policy Inspector</h3>
              </div>
              <button
                onClick={() => setShowRagModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                placeholder="Ask RAG about return windows, condition rules..."
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
              <button
                onClick={handleInspectRag}
                disabled={ragLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold disabled:opacity-50"
              >
                {ragLoading ? "Searching..." : "Evaluate RAG"}
              </button>
            </div>

            <div className="space-y-3">
              {ragResults.length === 0 && !ragLoading ? (
                <div className="p-6 text-center text-xs text-slate-400">No RAG policy chunks matched query.</div>
              ) : (
                ragResults.map((r, i) => (
                  <div key={i} className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-indigo-400">{r.document_title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                        Score: {r.score}
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed">{r.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
