"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  RotateCcw, 
  CreditCard, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  RefreshCw
} from "lucide-react";

export default function ReturnsPage() {
  const [activeTab, setActiveTab] = useState<"returns" | "refunds">("returns");
  const [returnsList, setReturnsList] = useState<any[]>([]);
  const [refundsList, setRefundsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReturnsAndRefunds = async () => {
    setLoading(true);
    try {
      const [retRes, refRes] = await Promise.all([
        api.returns.list(),
        api.refunds.list()
      ]);
      setReturnsList(retRes.data || []);
      setRefundsList(refRes.data || []);
    } catch (err) {
      console.error("Failed to load returns/refunds:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturnsAndRefunds();
  }, []);

  const handleApproveReturn = async (id: string) => {
    try {
      await api.returns.approve(id);
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert(err.message || "Failed to approve return.");
    }
  };

  const handleExecuteRefund = async (id: string) => {
    try {
      await api.refunds.execute(id);
      await fetchReturnsAndRefunds();
    } catch (err: any) {
      alert(err.message || "Failed to execute refund.");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <RotateCcw className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Returns & Refunds</h1>
              <p className="text-sm text-slate-400">Policy return inspection approvals and payment reversals.</p>
            </div>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => setActiveTab("returns")}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-colors ${activeTab === 'returns' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            Return Requests ({returnsList.length})
          </button>
          <button
            onClick={() => setActiveTab("refunds")}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-colors ${activeTab === 'refunds' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            Disbursed Refunds ({refundsList.length})
          </button>
        </div>
      </div>

      {/* Content Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {activeTab === "returns" ? (
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Return #</th>
                <th className="px-6 py-3.5">Order</th>
                <th className="px-6 py-3.5">Customer</th>
                <th className="px-6 py-3.5">Reason</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">Loading returns...</td></tr>
              ) : returnsList.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">No return requests found.</td></tr>
              ) : returnsList.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-white">{r.return_number}</td>
                  <td className="px-6 py-4 font-mono text-xs text-blue-400">{r.order_number || "—"}</td>
                  <td className="px-6 py-4 text-slate-200">{r.customer_name || "Buyer"}</td>
                  <td className="px-6 py-4 text-xs text-slate-400">{r.reason}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${r.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {r.status === "REQUESTED" && (
                      <button
                        onClick={() => handleApproveReturn(r.id)}
                        className="px-3 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-semibold"
                      >
                        Approve Return
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Refund #</th>
                <th className="px-6 py-3.5">Order</th>
                <th className="px-6 py-3.5">Amount</th>
                <th className="px-6 py-3.5">Reason</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">Loading refunds...</td></tr>
              ) : refundsList.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">No refunds found.</td></tr>
              ) : refundsList.map((rf) => (
                <tr key={rf.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-white">{rf.refund_number}</td>
                  <td className="px-6 py-4 font-mono text-xs text-blue-400">{rf.order_number || "—"}</td>
                  <td className="px-6 py-4 font-bold text-emerald-400">₹{rf.amount}</td>
                  <td className="px-6 py-4 text-xs text-slate-400">{rf.reason}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${rf.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'}`}>
                      {rf.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {rf.status === "APPROVED" && (
                      <button
                        onClick={() => handleExecuteRefund(rf.id)}
                        className="px-3 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded-lg text-xs font-semibold"
                      >
                        Execute Payout
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
