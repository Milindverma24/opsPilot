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
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPayload, setSelectedPayload] = useState<any>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.audit
      .list()
      .then((res) => setLogs(res.audit_logs || []))
      .catch((err) => console.error("Error loading audit logs:", err))
      .finally(() => setLoading(false));
  }, []);

  const filteredLogs = logs.filter((l) => {
    if (!search) return true;
    return (
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.actor_name.toLowerCase().includes(search.toLowerCase()) ||
      l.resource_type.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Immutable Audit Trail"
          subtitle="Cryptographically sealed, append-only ledger of all AI operations and human decisions"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Immutability Banner */}
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-slate-800 text-emerald-400 rounded-xl">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold">Tamper-Proof Audit Logging Active</h3>
                <p className="text-xs text-slate-400">
                  Every tool execution, policy check, and manager sign-off is permanently recorded with actor identity, timestamp, and payload.
                </p>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full bg-slate-800 text-slate-300 font-mono text-[11px]">
              Append-Only • Read-Only
            </span>
          </div>

          {/* Audit Logs Table */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Resource Target</th>
                    <th className="py-3 px-4 text-center">Result</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                        {formatDate(log.timestamp)}
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{log.actor_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{log.actor_type}</div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 font-bold">
                          {log.action}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                        {log.resource_type}: {log.resource_id}
                      </td>

                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                          log.result === "SUCCESS"
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-rose-50 text-rose-700"
                        }`}>
                          {log.result}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedPayload(log.payload)}
                          className="p-1 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-800"
                          title="View Payload"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Payload Modal */}
      {selectedPayload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Audit Log Payload</h3>
              <button onClick={() => setSelectedPayload(null)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>
            <pre className="p-4 bg-slate-900 text-emerald-400 rounded-xl overflow-x-auto font-mono text-[11px] max-h-96">
              {JSON.stringify(selectedPayload, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
