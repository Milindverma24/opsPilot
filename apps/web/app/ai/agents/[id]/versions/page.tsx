"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  History,
  CheckCircle2,
  RotateCcw,
  RefreshCw,
  ArrowLeft,
  Cpu,
  Layers,
  Sparkles,
  Sliders,
  FileCode,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function AgentVersionsPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = (params?.id as string) || "aria-support-ai";

  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState<any>(null);

  const fetchVersions = async () => {
    setLoading(true);
    try {
      const res = await api.agentVersions.list(agentId);
      const list = res?.data || [];
      setVersions(list);
      if (list.length > 0 && !selectedVersion) {
        setSelectedVersion(list[0]);
      }
    } catch (err) {
      console.error("Failed to load prompt versions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVersions();
  }, [agentId]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 antialiased overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                  <History className="w-6 h-6 text-purple-400" />
                  <span>Version History — {agentId}</span>
                </h1>
                <p className="text-xs text-slate-400">
                  Track prompt iterations, behavioral rules, and model hyperparameters across releases
                </p>
              </div>
            </div>

            <button
              onClick={fetchVersions}
              className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition self-start sm:self-auto"
              title="Refresh"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Version List Sidebar */}
            <div className="lg:col-span-5 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Release History ({versions.length})
              </h3>

              <div className="space-y-2">
                {versions.map((ver) => {
                  const isSelected = selectedVersion?.id === ver.id;
                  const isActive = ver.status === "ACTIVE";
                  return (
                    <div
                      key={ver.id}
                      onClick={() => setSelectedVersion(ver)}
                      className={cn(
                        "p-4 rounded-xl border cursor-pointer transition flex items-center justify-between",
                        isSelected
                          ? "bg-purple-950/20 border-purple-500 shadow-md shadow-purple-950/30"
                          : "bg-slate-900/50 border-slate-800 hover:border-slate-700"
                      )}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white font-mono">{ver.version}</span>
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded text-[10px] font-bold border",
                              isActive
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-slate-800 text-slate-400 border-slate-700"
                            )}
                          >
                            {ver.status}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {ver.created_at ? new Date(ver.created_at).toLocaleString() : ""}
                        </div>
                      </div>

                      <div className="text-right text-[11px] font-mono text-slate-400">
                        <div>{ver.model || "gpt-4o-mini"}</div>
                        <div>temp {ver.temperature || 0.1}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Selected Version Detail Panel */}
            <div className="lg:col-span-7">
              {selectedVersion ? (
                <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-5">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-white font-mono">{selectedVersion.version}</span>
                        <span
                          className={cn(
                            "px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase",
                            selectedVersion.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          )}
                        >
                          {selectedVersion.status}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500 font-mono">Agent: {agentId}</span>
                    </div>

                    <div className="text-xs text-slate-400 font-mono">
                      <span>Model: <strong className="text-slate-200">{selectedVersion.model}</strong></span>
                      <span className="ml-3">Temp: <strong className="text-slate-200">{selectedVersion.temperature || 0.1}</strong></span>
                    </div>
                  </div>

                  {/* System Prompt View */}
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      <FileCode className="w-3.5 h-3.5 text-purple-400" />
                      <span>System Prompt Instructions</span>
                    </span>
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
                      {selectedVersion.system_prompt}
                    </div>
                  </div>

                  {/* Behavior Rules */}
                  {selectedVersion.behavior_rules && selectedVersion.behavior_rules.length > 0 && (
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span>Behavior Constraints & Policy Rules</span>
                      </span>
                      <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                        {selectedVersion.behavior_rules.map((r: string, idx: number) => (
                          <div key={idx} className="text-xs text-purple-300 font-mono flex items-start gap-2">
                            <span className="text-purple-500 font-bold">{idx + 1}.</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-slate-800 text-xs text-slate-500 font-mono">
                    Created {selectedVersion.created_at ? new Date(selectedVersion.created_at).toLocaleString() : ""}
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500 text-xs">
                  Select a version on the left to inspect its prompt configuration.
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
