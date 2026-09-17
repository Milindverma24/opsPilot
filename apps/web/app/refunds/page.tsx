"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Search,
  Filter,
  CreditCard,
  DollarSign,
  Plus,
  BookOpen,
  X
} from "lucide-react";
import { api } from "@/lib/api";

export default function RefundsPage() {
  const [refunds, setRefunds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRagModal, setShowRagModal] = useState(false);
  const [ragQuery, setRagQuery] = useState("financial approval policy for refunds over 2000 INR");
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [ragLoading, setRagLoading] = useState(false);

  // Form State
  const [orderId, setOrderId] = useState("");
  const [amount, setAmount] = useState(1499);
  const [reason, setReason] = useState("Customer Return QA Passed (Size adjustment)");
  const [submitting, setSubmitting] = useState(false);

  const fetchRefunds = async () => {
    setLoading(true);
    try {
      const res = await api.refunds.list({ limit: 100 });
      setRefunds(res.data || res.items || res.refunds || []);
    } catch (err) {
      console.error("Failed to load refunds:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRefunds();
  }, []);

  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await api.refunds.approve(id);
      await fetchRefunds();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecute = async (id: string) => {
    setActionLoading(id);
    try {
      await api.refunds.execute(id);
      await fetchRefunds();
    } catch (err: any) {
      alert(`Execute error: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateRefund = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderId.trim()) return;
    setSubmitting(true);
    try {
      await api.refunds.request({
        order_id: orderId.trim(),
        amount: Number(amount),
        reason: reason.trim()
      });
      setShowCreateModal(false);
      setOrderId("");
      await fetchRefunds();
    } catch (err: any) {
      alert("Failed to submit refund: " + err.message);
    } finally {
      setSubmitting(false);
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

  const filtered = refunds.filter((r) => {
    if (statusFilter === "ALL") return true;
    return r.status === statusFilter;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Refunds & Financial Operations"
          subtitle="Human-in-the-loop financial governance: High-risk refunds > ₹2,000 require dual approval"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Total Refunds</span>
              <div className="mt-2 text-3xl font-extrabold text-slate-900">{refunds.length}</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Pending Approval</span>
              <div className="mt-2 text-3xl font-extrabold text-amber-600">
                {refunds.filter((r) => r.status === "PENDING_APPROVAL" || r.status === "PENDING" || r.status === "REQUESTED").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Executed / Paid</span>
              <div className="mt-2 text-3xl font-extrabold text-emerald-600">
                {refunds.filter((r) => r.status === "EXECUTED" || r.status === "COMPLETED").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Approval Policy</span>
              <div className="mt-2 text-sm font-bold text-slate-900">
                &gt; ₹2,000 <span className="text-rose-600 font-semibold">(Dual Approver)</span>
              </div>
            </div>
          </div>

          {/* Filter Bar & Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {["ALL", "PENDING_APPROVAL", "APPROVED", "EXECUTED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition ${
                    statusFilter === st
                      ? "bg-slate-900 text-white"
                      : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {st.replace("_", " ")}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleInspectRag}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition flex items-center gap-1.5"
              >
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <span>RAG Financial Policy</span>
              </button>

              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Request Refund</span>
              </button>

              <button
                onClick={fetchRefunds}
                className="p-2 text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-xl"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Refunds Table */}
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase">
                  <th className="p-4">Refund ID</th>
                  <th className="p-4">Order ID</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Reason</th>
                  <th className="p-4">Risk Level</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      Loading refund requests...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      No refunds found matching the criteria.
                    </td>
                  </tr>
                ) : (
                  filtered.map((rf) => {
                    const isHighRisk = (rf.amount || 0) > 2000;
                    return (
                      <tr key={rf.id} className="hover:bg-slate-50 transition">
                        <td className="p-4 font-mono font-bold text-slate-900">
                          {rf.refund_number || rf.id.slice(0, 8)}
                        </td>
                        <td className="p-4 font-mono text-slate-600">
                          {rf.order_id ? rf.order_id.slice(0, 8) : (rf.order_number || "N/A")}
                        </td>
                        <td className="p-4 font-bold text-slate-900">
                          ₹{Number(rf.amount || 0).toLocaleString()}
                        </td>
                        <td className="p-4 text-slate-600 max-w-xs truncate">
                          {rf.reason || "Customer Return Request"}
                        </td>
                        <td className="p-4">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              isHighRisk
                                ? "bg-rose-100 text-rose-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {isHighRisk ? "HIGH RISK (>₹2K)" : "NORMAL"}
                          </span>
                        </td>
                        <td className="p-4">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              rf.status === "EXECUTED" || rf.status === "COMPLETED"
                                ? "bg-emerald-100 text-emerald-800"
                                : rf.status === "PENDING_APPROVAL" || rf.status === "PENDING"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {rf.status}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="inline-flex items-center gap-2">
                            {(rf.status === "PENDING_APPROVAL" || rf.status === "PENDING" || rf.status === "REQUESTED") && (
                              <button
                                onClick={() => handleApprove(rf.id)}
                                disabled={actionLoading === rf.id}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm"
                              >
                                {actionLoading === rf.id ? "..." : "Approve"}
                              </button>
                            )}

                            {(rf.status === "APPROVED" || rf.status === "PENDING") && (
                              <button
                                onClick={() => handleExecute(rf.id)}
                                disabled={actionLoading === rf.id}
                                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm"
                              >
                                {actionLoading === rf.id ? "..." : "Execute Payout"}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>

      {/* Modal: Request Refund */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white rounded-3xl p-6 space-y-5 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-base">Issue Customer Refund</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateRefund} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-600 font-semibold">Order ID / Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ord-001 or ORD-648291"
                  value={orderId}
                  onChange={(e) => setOrderId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-600 font-semibold">Refund Amount (₹ INR)</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900 font-bold"
                />
                {amount > 2000 && (
                  <p className="text-[11px] text-rose-600 font-medium flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Amount exceeds ₹2,000. Dual manager approval will be enforced.
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-slate-600 font-semibold">Reason for Refund</label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-slate-900"
                >
                  <option value="Customer Return QA Passed (Size adjustment)">Customer Return QA Passed (Size adjustment)</option>
                  <option value="Parcel Damaged in Transit">Parcel Damaged in Transit</option>
                  <option value="Order Cancelled Prior to Dispatch">Order Cancelled Prior to Dispatch</option>
                  <option value="Goodwill Courtesy Credit">Goodwill Courtesy Credit</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Submit Refund"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: RAG Policy Inspector */}
      {showRagModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-white rounded-3xl p-6 space-y-5 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-base">RAG Financial Policy Inspector</h3>
              </div>
              <button
                onClick={() => setShowRagModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                placeholder="Search financial governance policies..."
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900"
              />
              <button
                onClick={handleInspectRag}
                disabled={ragLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold disabled:opacity-50"
              >
                {ragLoading ? "Searching..." : "Evaluate RAG"}
              </button>
            </div>

            <div className="space-y-3">
              {ragResults.length === 0 && !ragLoading ? (
                <div className="p-6 text-center text-xs text-slate-400">No policy chunks found for this query.</div>
              ) : (
                ragResults.map((r, i) => (
                  <div key={i} className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-indigo-700">{r.document_title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                        Score: {r.score}
                      </span>
                    </div>
                    <p className="text-slate-700 leading-relaxed">{r.content}</p>
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
