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
} from "lucide-react";
import { api } from "@/lib/api";

export default function RefundsPage() {
  const [refunds, setRefunds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchRefunds = async () => {
    setLoading(true);
    try {
      const res = await api.refunds.list({ limit: 100 });
      setRefunds(res.items || res.refunds || []);
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
          subtitle="Human-in-the-loop financial governance: High-risk refunds &gt; ₹2,000 require dual approval"
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
                {refunds.filter((r) => r.status === "PENDING_APPROVAL" || r.status === "PENDING").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Executed</span>
              <div className="mt-2 text-3xl font-extrabold text-emerald-600">
                {refunds.filter((r) => r.status === "EXECUTED" || r.status === "COMPLETED").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Approval Policy</span>
              <div className="mt-2 text-sm font-bold text-slate-900">
                &gt; ₹2,000 <span className="text-rose-600 font-semibold">(High-Risk)</span>
              </div>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {["ALL", "PENDING_APPROVAL", "EXECUTED", "REJECTED"].map((st) => (
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

            <button
              onClick={fetchRefunds}
              className="p-2 text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-xl"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
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
                          {rf.order_id ? rf.order_id.slice(0, 8) : "N/A"}
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
                            {isHighRisk ? "HIGH RISK" : "NORMAL"}
                          </span>
                        </td>
                        <td className="p-4">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              rf.status === "EXECUTED" || rf.status === "COMPLETED"
                                ? "bg-emerald-100 text-emerald-800"
                                : rf.status === "PENDING_APPROVAL"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {rf.status}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          {rf.status === "PENDING_APPROVAL" && (
                            <button
                              onClick={() => handleApprove(rf.id)}
                              disabled={actionLoading === rf.id}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm"
                            >
                              Approve
                            </button>
                          )}
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
    </div>
  );
}
