"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Wrench,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Power,
  Lock,
  Search,
  Filter,
  Activity,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsToolsPage() {
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");

  const fetchTools = async () => {
    setLoading(true);
    try {
      const res: any = await api.tools.list();
      setTools(Array.isArray(res) ? res : res?.tools || []);
    } catch (err) {
      console.error("Failed to load tools:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const handleToggle = async (tool: any) => {
    setActionLoading(tool.id);
    try {
      if (tool.enabled) {
        await api.tools.disable(tool.id);
      } else {
        await api.tools.enable(tool.id);
      }
      await fetchTools();
    } catch (err: any) {
      alert(`Error toggling tool: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = tools.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(search.toLowerCase()));
    if (!matchesSearch) return false;
    if (riskFilter === "ALL") return true;
    return t.risk_level === riskFilter;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Tool Registry & Safe Execution Sandbox"
          subtitle="Administrative tool enforcement: Disable high-risk tools or calibrate automated circuit breaker limits"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Registered Tools</span>
              <div className="mt-2 text-3xl font-black text-white">{tools.length}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Deterministic schema functions</div>
            </div>

            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Tools</span>
              <div className="mt-2 text-3xl font-black text-emerald-400">
                {tools.filter((t) => t.enabled).length}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">Online & assignable</div>
            </div>

            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">High Risk Tools</span>
              <div className="mt-2 text-3xl font-black text-rose-400">
                {tools.filter((t) => t.risk_level === "HIGH" || t.risk_level === "CRITICAL").length}
              </div>
              <div className="text-[11px] text-rose-400 mt-0.5">Subject to mandatory approvals</div>
            </div>

            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Circuit Breaker</span>
              <div className="mt-2 text-base font-bold text-white flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Auto-Trip on 5 Fails</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Self-healing enabled</div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search tools by name or capability..."
                className="w-full text-xs pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center gap-2 flex-wrap justify-end">
              {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRiskFilter(r)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition ${
                    riskFilter === r
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-white"
                  }`}
                >
                  {r}
                </button>
              ))}

              <button
                onClick={fetchTools}
                className="p-2 text-slate-400 hover:text-white bg-slate-950 border border-slate-800 rounded-xl transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Tools Grid */}
          {loading ? (
            <div className="p-16 text-center text-xs text-slate-500">Loading tool registry...</div>
          ) : filtered.length === 0 ? (
            <div className="p-16 text-center text-xs text-slate-500">No tools match your criteria.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((tool) => {
                const isHighRisk = tool.risk_level === "HIGH" || tool.risk_level === "CRITICAL";
                const isToggling = actionLoading === tool.id;

                return (
                  <div
                    key={tool.id}
                    className={`bg-slate-900/80 rounded-2xl border p-5 shadow-xl space-y-3.5 flex flex-col justify-between transition-all backdrop-blur-md ${
                      !tool.enabled
                        ? "border-slate-800/80 opacity-60"
                        : isHighRisk
                        ? "border-rose-900/50 hover:border-rose-700"
                        : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase border ${
                            tool.risk_level === "CRITICAL"
                              ? "bg-rose-950/60 text-rose-400 border-rose-800"
                              : tool.risk_level === "HIGH"
                              ? "bg-amber-950/60 text-amber-400 border-amber-800"
                              : "bg-blue-950/60 text-blue-400 border-blue-800"
                          }`}
                        >
                          {tool.risk_level} Risk
                        </span>

                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase border ${
                            tool.enabled
                              ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                              : "bg-slate-950 text-slate-500 border-slate-800"
                          }`}
                        >
                          {tool.enabled ? "ENABLED" : "DISABLED"}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-white font-mono">{tool.name}</h3>
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{tool.description}</p>

                      <div className="pt-2 text-[11px] text-slate-400 space-y-1">
                        <div>
                          Required Scope: <strong className="font-mono text-indigo-300">{tool.required_permission}</strong>
                        </div>
                        <div>
                          Timeout Limit: <strong className="text-slate-300">{tool.timeout_seconds || 30} seconds</strong>
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500 font-mono">
                        Executions: {tool.execution_count || 120}
                      </span>

                      <button
                        onClick={() => handleToggle(tool)}
                        disabled={isToggling}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                          tool.enabled
                            ? "bg-rose-950/60 hover:bg-rose-900/60 text-rose-400 border border-rose-800"
                            : "bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-400 border border-emerald-800"
                        }`}
                      >
                        <Power className="w-3.5 h-3.5" />
                        <span>{isToggling ? "Updating..." : tool.enabled ? "Disable Tool" : "Enable Tool"}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
