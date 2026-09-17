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
  X,
  Eye,
  Shield,
  Server,
  ArrowRight,
} from "lucide-react";
import { api } from "@/lib/api";

export default function ObservabilityTracesPage() {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [operationFilter, setOperationFilter] = useState<string>("");
  const [selectedTrace, setSelectedTrace] = useState<any | null>(null);

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
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shadow-sm shadow-emerald-500/10">
            <CheckCircle2 className="w-3 h-3" /> SUCCESS
          </span>
        );
      case "DEGRADED":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 animate-pulse">
            <AlertCircle className="w-3 h-3" /> DEGRADED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <XCircle className="w-3 h-3" /> FAILED
          </span>
        );
    }
  };

  const avgDuration = traces.length
    ? Math.round(traces.reduce((acc, t) => acc + (t.duration_ms || 0), 0) / traces.length)
    : 0;
  const successRate = traces.length
    ? Math.round((traces.filter((t) => t.status === "SUCCESS").length / traces.length) * 100)
    : 100;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Observability & Trace Forensics"
          subtitle="End-to-end execution spans, stage latencies, security gate audits, and tool execution forensics"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Total Recorded Traces</span>
                <Activity className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">{traces.length}</div>
              <div className="text-[11px] text-slate-400 mt-1">Multi-span telemetry events</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Avg Execution Latency</span>
                <Clock className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-blue-400 mt-2">{avgDuration} ms</div>
              <div className="text-[11px] text-slate-400 mt-1">Ingestion to action delivery</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Success Rate</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-2">{successRate}%</div>
              <div className="text-[11px] text-slate-400 mt-1">0 fatal kernel crashes</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Tracing Engine</span>
                <Server className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">OpenTelemetry</div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Span profiler live
              </div>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-wrap w-full md:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Operation:</span>
                <select
                  value={operationFilter}
                  onChange={(e) => setOperationFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">All Operations</option>
                  <option value="CUSTOMER_CHAT">Customer Chat</option>
                  <option value="ORDER_FULFILLMENT">Order Fulfillment</option>
                  <option value="RETURN_PROCESSING">Return Processing</option>
                  <option value="SHIPMENT_DELAY_RESOLUTION">Shipment Delay Resolution</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">All Statuses</option>
                  <option value="SUCCESS">Success</option>
                  <option value="DEGRADED">Degraded</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto justify-end">
              <button
                onClick={fetchTraces}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh Traces</span>
              </button>
            </div>
          </div>

          {/* Traces Table */}
          <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="p-3.5 pl-5">Trace / Request ID</th>
                    <th className="p-3.5">Operation Name</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Duration</th>
                    <th className="p-3.5">Spans Breakdown</th>
                    <th className="p-3.5">Timestamp</th>
                    <th className="p-3.5 text-right pr-5">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {traces.map((trace) => (
                    <tr
                      key={trace.id}
                      onClick={() => setSelectedTrace(trace)}
                      className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                    >
                      <td className="p-3.5 pl-5 font-mono text-indigo-400 font-semibold">
                        {trace.request_id || trace.trace_id}
                      </td>
                      <td className="p-3.5 font-medium text-white">
                        <span className="px-2 py-0.5 rounded-md bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 font-mono text-[11px]">
                          {trace.operation_name}
                        </span>
                      </td>
                      <td className="p-3.5">{getStatusBadge(trace.status)}</td>
                      <td className="p-3.5 font-mono font-bold text-slate-200">
                        {trace.duration_ms} ms
                      </td>
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5 max-w-[200px]">
                          {Array.isArray(trace.spans) ? (
                            <div className="flex items-center gap-1">
                              <span className="text-slate-300 font-semibold">{trace.spans.length} spans:</span>
                              <div className="flex gap-0.5 h-2 w-24 bg-slate-800 rounded-full overflow-hidden">
                                {trace.spans.map((s: any, idx: number) => (
                                  <div
                                    key={idx}
                                    style={{
                                      width: `${Math.max(5, (s.duration_ms / (trace.duration_ms || 1)) * 100)}%`,
                                    }}
                                    className={`h-full ${
                                      idx % 3 === 0
                                        ? "bg-indigo-500"
                                        : idx % 3 === 1
                                        ? "bg-blue-500"
                                        : "bg-emerald-500"
                                    }`}
                                    title={`${s.name}: ${s.duration_ms}ms`}
                                  />
                                ))}
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-500">1 root span</span>
                          )}
                        </div>
                      </td>
                      <td className="p-3.5 text-slate-400">
                        {new Date(trace.created_at).toLocaleTimeString()}
                      </td>
                      <td className="p-3.5 text-right pr-5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTrace(trace);
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-indigo-400 group-hover:text-white rounded-lg text-xs font-semibold border border-slate-700 transition flex items-center gap-1 ml-auto"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Inspect Waterfall</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {traces.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 p-8">
                <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No traces found</h3>
                <p className="text-xs text-slate-400 mt-1">No execution spans recorded matching current filters.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Waterfall Drawer / Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">
                      Trace: {selectedTrace.request_id || selectedTrace.trace_id}
                    </h3>
                    {getStatusBadge(selectedTrace.status)}
                  </div>
                  <p className="text-xs text-slate-400">
                    Operation: <span className="text-indigo-300 font-semibold">{selectedTrace.operation_name}</span> | Total Latency:{" "}
                    <span className="text-white font-bold">{selectedTrace.duration_ms} ms</span>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Waterfall Timeline Spans */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Execution Span Waterfall ({Array.isArray(selectedTrace.spans) ? selectedTrace.spans.length : 1} Stages)
              </h4>

              {Array.isArray(selectedTrace.spans) && selectedTrace.spans.length > 0 ? (
                <div className="space-y-2 bg-slate-950 p-4 rounded-xl border border-slate-800">
                  {selectedTrace.spans.map((span: any, idx: number) => {
                    const total = selectedTrace.duration_ms || 1;
                    const offsetPct = Math.min(95, ((span.offset_ms || 0) / total) * 100);
                    const widthPct = Math.max(5, Math.min(100 - offsetPct, ((span.duration_ms || 1) / total) * 100));

                    return (
                      <div key={idx} className="space-y-1 text-xs">
                        <div className="flex items-center justify-between text-slate-300">
                          <span className="font-semibold flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                            {span.name}
                          </span>
                          <div className="flex items-center gap-2 font-mono text-[11px]">
                            <span className="text-slate-400">offset +{span.offset_ms || 0}ms</span>
                            <span className="text-indigo-300 font-bold">{span.duration_ms} ms</span>
                          </div>
                        </div>

                        {/* Bar */}
                        <div className="h-3 bg-slate-900 rounded-md overflow-hidden relative border border-slate-800/80">
                          <div
                            style={{ left: `${offsetPct}%`, width: `${widthPct}%` }}
                            className="absolute top-0 bottom-0 bg-gradient-to-r from-indigo-500 to-blue-500 rounded"
                          />
                        </div>

                        {span.details && (
                          <div className="text-[11px] text-slate-400 pl-3 border-l-2 border-slate-800">
                            {span.details}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs text-slate-400">
                  Root execution completed in {selectedTrace.duration_ms}ms with no sub-span anomalies.
                </div>
              )}
            </div>

            {/* Trace Metadata */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Trace Context & Security</h4>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                <div>Trace ID: {selectedTrace.trace_id}</div>
                <div>Created At: {new Date(selectedTrace.created_at).toISOString()}</div>
                <div>Engine: OpsPilot Deterministic Governor v2.4</div>
              </div>
            </div>

            <div className="pt-2 flex justify-end border-t border-slate-800">
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition"
              >
                Close Forensics
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
