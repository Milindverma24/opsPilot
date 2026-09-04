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
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Tool Registry & Security Governance"
          subtitle="Administrative tool enforcement: Disable dangerous tools or set circuit breaker limits"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Registered Tools</span>
              <div className="mt-2 text-3xl font-extrabold text-slate-900">{tools.length}</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Active Tools</span>
              <div className="mt-2 text-3xl font-extrabold text-emerald-600">
                {tools.filter((t) => t.enabled).length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">High Risk Tools</span>
              <div className="mt-2 text-3xl font-extrabold text-rose-600">
                {tools.filter((t) => t.risk_level === "HIGH" || t.risk_level === "CRITICAL").length}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase">Circuit Breaker</span>
              <div className="mt-2 text-sm font-bold text-slate-900">
                Trip on 5 Consecutive Fails
              </div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search tools by name or purpose..."
                className="w-full text-xs pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center gap-2">
              {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRiskFilter(r)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition ${
                    riskFilter === r
                      ? "bg-slate-900 text-white"
                      : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {r}
                </button>
              ))}

              <button
                onClick={fetchTools}
                className="p-2 text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-xl"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Tools Grid */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">Loading tool registry...</div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-slate-400">No tools match criteria.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((tool) => {
                const isHighRisk = tool.risk_level === "HIGH" || tool.risk_level === "CRITICAL";
                const isToggling = actionLoading === tool.id;

                return (
                  <div
                    key={tool.id}
                    className={`bg-white rounded-2xl border p-5 shadow-sm space-y-3 flex flex-col justify-between transition ${
                      !tool.enabled
                        ? "border-slate-200 bg-slate-50/50 opacity-70"
                        : isHighRisk
                        ? "border-rose-200"
                        : "border-slate-200"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                            tool.risk_level === "CRITICAL"
                              ? "bg-rose-100 text-rose-800"
                              : tool.risk_level === "HIGH"
                              ? "bg-orange-100 text-orange-800"
                              : "bg-blue-50 text-blue-700"
                          }`}
                        >
                          {tool.risk_level} Risk
                        </span>

                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                            tool.enabled
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-200 text-slate-600"
                          }`}
                        >
                          {tool.enabled ? "ENABLED" : "DISABLED"}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-900 font-mono">{tool.name}</h3>
                      <p className="text-xs text-slate-500 line-clamp-2">{tool.description}</p>

                      <div className="pt-2 text-[11px] text-slate-400 space-y-1">
                        <div>
                          Permission: <strong className="font-mono text-slate-600">{tool.required_permission}</strong>
                        </div>
                        <div>
                          Approval Mode: <strong className="text-slate-600">{tool.approval_mode}</strong>
                        </div>
                        <div>
                          Timeout: <strong>{tool.timeout_seconds || 30}s</strong> | Retries: <strong>{tool.max_retries || 2}</strong>
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                      <span className="text-[11px] text-slate-400">
                        Failures: {tool.failure_count || 0}/5
                      </span>

                      <button
                        onClick={() => handleToggle(tool)}
                        disabled={isToggling}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                          tool.enabled
                            ? "bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200"
                            : "bg-emerald-600 text-white hover:bg-emerald-700"
                        }`}
                      >
                        <Power className="w-3.5 h-3.5" />
                        {tool.enabled ? "Disable Tool" : "Enable Tool"}
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
