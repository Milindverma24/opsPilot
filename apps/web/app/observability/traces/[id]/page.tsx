"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Activity,
  CheckCircle2,
  Clock,
  ChevronLeft,
  RefreshCw,
  Layers,
  ShieldCheck,
  Zap,
  Info,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function TraceDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSpan, setSelectedSpan] = useState<any>(null);

  const fetchTrace = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.observability.trace(id);
      const data = res.data;
      setTrace(data);
      if (data?.spans && data.spans.length > 0) {
        setSelectedSpan(data.spans[0]);
      }
    } catch (err) {
      console.error("Failed to load trace detail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrace();
  }, [id]);

  if (loading && !trace) {
    return (
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Loading Trace Waterfall...</span>
          </div>
        </div>
      </div>
    );
  }

  const totalDuration = trace?.duration_ms || 1000;
  const spans = trace?.spans || [];

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title={`Trace Forensics • #${id}`}
          subtitle="Interactive execution span waterfall and sub-millisecond stage latency distribution"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header & Nav */}
          <div className="flex items-center justify-between">
            <Link
              href="/observability/traces"
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-xs transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back to Trace List</span>
            </Link>

            <button
              onClick={fetchTrace}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Trace</span>
            </button>
          </div>

          {/* Trace Metadata Overview */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <h1 className="text-xl font-black text-slate-900 tracking-tight">
                    {trace?.operation_name || "CUSTOMER_CHAT"}
                  </h1>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {trace?.status || "SUCCESS"}
                  </span>
                </div>
                <div className="text-xs text-slate-500 font-mono">
                  Trace ID: #{trace?.id} • Request ID: {trace?.request_id || "req-9912"}
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-[11px] text-slate-400">Total Latency</div>
                  <div className="text-xl font-black text-blue-600 font-mono">{trace?.duration_ms} ms</div>
                </div>
                <div className="text-right pl-4 border-l border-slate-200">
                  <div className="text-[11px] text-slate-400">Total Spans</div>
                  <div className="text-xl font-black text-slate-800">{spans.length}</div>
                </div>
              </div>
            </div>

            {/* Waterfall Container */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-wider px-2">
                <span>Execution Stage</span>
                <div className="flex items-center gap-8 font-mono text-[11px]">
                  <span>0ms</span>
                  <span>{Math.round(totalDuration * 0.25)}ms</span>
                  <span>{Math.round(totalDuration * 0.5)}ms</span>
                  <span>{Math.round(totalDuration * 0.75)}ms</span>
                  <span>{totalDuration}ms</span>
                </div>
              </div>

              {/* Spans Waterfall Bars */}
              <div className="space-y-2">
                {spans.map((span: any, idx: number) => {
                  const offsetPct = Math.min(100, Math.max(0, ((span.offset_ms || 0) / totalDuration) * 100));
                  const widthPct = Math.max(2, Math.min(100 - offsetPct, ((span.duration_ms || 10) / totalDuration) * 100));
                  const isSelected = selectedSpan?.name === span.name;

                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedSpan(span)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-blue-50/70 border-blue-300 shadow-xs"
                          : "bg-slate-50/70 hover:bg-slate-50 border-slate-200/70"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-2">
                        <span className="font-bold text-slate-900 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                          {span.name}
                        </span>
                        <div className="flex items-center gap-3 font-mono text-[11px]">
                          <span className="text-slate-500">+{span.offset_ms || 0}ms</span>
                          <span className="font-bold text-slate-800">{span.duration_ms}ms</span>
                        </div>
                      </div>

                      {/* Timeline Bar Track */}
                      <div className="relative w-full h-3 bg-slate-200/70 rounded-full overflow-hidden">
                        <div
                          className="absolute h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300"
                          style={{
                            left: `${offsetPct}%`,
                            width: `${widthPct}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Span Details Inspector */}
          {selectedSpan && (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-blue-600" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    Span Inspector: {selectedSpan.name}
                  </h3>
                </div>
                <span className="text-xs font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  {selectedSpan.duration_ms} ms
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="font-semibold text-slate-500">Execution Status</span>
                  <div className="font-bold text-emerald-600 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> {selectedSpan.status || "OK"}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="font-semibold text-slate-500">Timeline Offset</span>
                  <div className="font-mono text-slate-800">
                    Started at +{selectedSpan.offset_ms || 0} ms from request ingestion
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <span className="font-semibold text-slate-600 text-xs">Span Forensics & Payload:</span>
                <div className="p-3 mt-1.5 bg-slate-900 text-emerald-400 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed">
                  {selectedSpan.details || "Stage executed successfully without exceptions."}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
