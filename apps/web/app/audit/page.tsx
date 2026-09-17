"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  History,
  Shield,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  Lock,
  RefreshCw,
  X,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPayload, setSelectedPayload] = useState<any>(null);
  const [search, setSearch] = useState("");

  const loadAuditLogs = () => {
    setLoading(true);
    api.audit
      .list()
      .then((res) => setLogs(res.audit_logs || []))
      .catch((err) => console.error("Error loading audit logs:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const filteredLogs = logs.filter((l) => {
    if (!search) return true;
    return (
      l.action?.toLowerCase().includes(search.toLowerCase()) ||
      l.actor_name?.toLowerCase().includes(search.toLowerCase()) ||
      l.resource_type?.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Immutable Audit Ledger"
          subtitle="Cryptographically sealed, append-only ledger of all AI operations, tool executions, and human decisions"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Immutability Banner */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-2xl">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Tamper-Proof Audit Logging Active</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Every tool execution, policy check, and manager sign-off is permanently recorded with actor identity, timestamp, and payload.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-3 py-1 rounded-full bg-slate-950 text-indigo-300 border border-slate-800 font-mono text-[11px]">
                Append-Only • Non-Repudiation
              </span>
              <button
                onClick={loadAuditLogs}
                disabled={loading}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex items-center justify-between gap-4">
            <div className="relative w-full sm:w-96">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Search by action, actor name, or resource type..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="text-xs text-slate-400 font-mono">
              {filteredLogs.length} Events Recorded
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950/80 text-slate-400 font-bold uppercase tracking-wider text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-3.5 px-4 pl-5">Timestamp</th>
                    <th className="py-3.5 px-4">Actor</th>
                    <th className="py-3.5 px-4">Action</th>
                    <th className="py-3.5 px-4">Resource Target</th>
                    <th className="py-3.5 px-4 text-center">Result</th>
                    <th className="py-3.5 px-4 text-right pr-5">Payload</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 pl-5 font-mono text-slate-400 text-[11px]">
                        {formatDate(log.timestamp)}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-bold text-white">{log.actor_name}</div>
                        <div className="text-[10px] text-indigo-400 font-mono">{log.actor_type}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-md font-mono text-[10px] bg-slate-950 text-indigo-300 border border-slate-800 font-bold">
                          {log.action}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 font-mono text-[11px] text-slate-300">
                        {log.resource_type}: {log.resource_id}
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
                            log.result === "SUCCESS"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                          }`}
                        >
                          {log.result}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right pr-5">
                        <button
                          onClick={() => setSelectedPayload(log.payload)}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition inline-flex items-center gap-1"
                          title="View Payload"
                        >
                          <Eye className="w-3.5 h-3.5 text-indigo-400" />
                          <span>View</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredLogs.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 p-8">
                <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No logs found</h3>
                <p className="text-xs text-slate-400 mt-1">No audit events match your search query.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Payload Modal */}
      {selectedPayload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl p-6 max-w-lg w-full shadow-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">Immutable Event Payload</h3>
              <button
                onClick={() => setSelectedPayload(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <pre className="p-4 bg-slate-950 text-emerald-400 rounded-xl overflow-x-auto font-mono text-[11px] border border-slate-800 max-h-96">
              {JSON.stringify(selectedPayload, null, 2)}
            </pre>
            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setSelectedPayload(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
