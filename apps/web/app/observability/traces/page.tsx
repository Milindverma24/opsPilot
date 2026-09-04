"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Activity,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  Search,
  ChevronRight,
  Zap,
  AlertCircle,
  XCircle,
  Sliders,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function ObservabilityTracesPage() {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [operationFilter, setOperationFilter] = useState<string>("");

  const fetchTraces = async () => {
    setLoading(true);
    try {
      const res = await api.observability.traces({
        status: statusFilter || undefined,
        operation: operationFilter || undefined,
      });
      setTraces(res.data || []);
    } catch (err) {
      console.error("Failed to load traces:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraces();
  }, [statusFilter, operationFilter]);

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> SUCCESS
          </span>
        );
      case "DEGRADED":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> DEGRADED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-600 border border-rose-500/20 flex items-center gap-1">
            <XCircle className="w-3 h-3" /> FAILED
          </span>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Observability & Trace Waterfalls"
          subtitle="End-to-end execution spans, stage latencies, security gate audits, and tool execution forensics"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <Activity className="w-6 h-6 text-blue-600" />
                Operational Execution Traces
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Sub-millisecond waterfall telemetry tracing customer requests through reasoning, retrieval, verification, and action execution.
              </p>
            </div>

            <button
              onClick={fetchTraces}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Traces</span>
            </button>
          </div>

          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-slate-500">Operation:</span>
              <select
                value={operationFilter}
                onChange={(e) => setOperationFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-medium focus:outline-none"
              >
                <option value="">All Operations</option>
                <option value="CUSTOMER_CHAT">Customer Chat</option>
                <option value="ORDER_FULFILLMENT">Order Fulfillment</option>
                <option value="RETURN_PROCESSING">Return Processing</option>
                <option value="SHIPMENT_DELAY_RESOLUTION">Shipment Delay Resolution</option>
              </select>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <span className="text-xs font-semibold text-slate-500">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-medium focus:outline-none"
              >
                <option value="">All Statuses</option>
                <option value="SUCCESS">Success</option>
                <option value="DEGRADED">Degraded</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
          </div>

          {/* Traces Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-200/60 font-semibold">
                  <tr>
                    <th className="p-3.5 pl-5">Trace ID</th>
                    <th className="p-3.5">Operation Name</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Duration</th>
                    <th className="p-3.5">Spans</th>
                    <th className="p-3.5">Timestamp</th>
                    <th className="p-3.5 text-right pr-5">Inspection</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {traces.map((trace) => (
                    <tr key={trace.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="p-3.5 pl-5 font-mono font-bold text-slate-900">
                        <div className="flex items-center gap-2">
                          <Layers className="w-4 h-4 text-blue-500" />
                          <span>#{trace.id}</span>
                        </div>
                      </td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-semibold text-[11px] border border-blue-200/60">
                          {trace.operation_name}
                        </span>
                      </td>
                      <td className="p-3.5">{getStatusBadge(trace.status)}</td>
                      <td className="p-3.5 font-mono font-semibold text-slate-800">
                        {trace.duration_ms} ms
                      </td>
                      <td className="p-3.5">
                        <span className="text-slate-600 font-medium">
                          {trace.stages_count || 6} spans
                        </span>
                      </td>
                      <td className="p-3.5 text-slate-500 font-mono text-[11px]">
                        {trace.created_at ? new Date(trace.created_at).toLocaleTimeString() : "Just now"}
                      </td>
                      <td className="p-3.5 text-right pr-5">
                        <Link
                          href={`/observability/traces/${trace.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                        >
                          <span>Waterfall</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
