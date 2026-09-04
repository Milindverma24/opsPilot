"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Cpu,
  Bot,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  Zap,
  Wrench,
  ChevronRight,
  RefreshCw,
  Sliders,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function AIEmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const res = await api.aiEmployees.list();
      setEmployees(res.data || []);
    } catch (err) {
      console.error("Failed to load AI employees:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleHeartbeat = async (id: string) => {
    setActingId(id);
    try {
      await api.aiEmployees.heartbeat(id, {
        current_task: "Manual heartbeat verification test",
        queue_size: 0,
      });
      await fetchEmployees();
    } catch (err: any) {
      alert("Heartbeat failed: " + err.message);
    } finally {
      setActingId(null);
    }
  };

  const handleRecover = async (id: string) => {
    setActingId(id);
    try {
      await api.aiEmployees.recover(id);
      await fetchEmployees();
    } catch (err: any) {
      alert("Recovery failed: " + err.message);
    } finally {
      setActingId(null);
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case "HEALTHY":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> HEALTHY
          </span>
        );
      case "DEGRADED":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 border border-amber-500/20 flex items-center gap-1.5 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span> DEGRADED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-600 border border-rose-500/20 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span> CRITICAL
          </span>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="AI Workforce Directory"
          subtitle="Autonomous digital workforce nodes powering UrbanThread e-commerce operations"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Controls */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <Cpu className="w-6 h-6 text-blue-600" />
                Active AI Employee Fleet
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Each AI employee is an autonomous specialist operating under strict RBAC, tool safety limits, and continuous health surveillance.
              </p>
            </div>
            <button
              onClick={fetchEmployees}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Telemetry</span>
            </button>
          </div>

          {/* AI Workforce Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {employees.map((emp) => (
              <div
                key={emp.id}
                className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-black text-base shadow-md shadow-blue-500/20">
                        {emp.name[0]}
                      </div>
                      <div>
                        <h2 className="font-bold text-slate-900 text-base">{emp.name}</h2>
                        <span className="text-[11px] font-mono text-slate-400">#{emp.id}</span>
                      </div>
                    </div>
                    {getHealthBadge(emp.health)}
                  </div>

                  <div className="inline-block px-2.5 py-0.5 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/60">
                    {emp.role}
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{emp.description}</p>

                  {/* Task & Queue */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between text-slate-500 text-[11px]">
                      <span>Current Operation:</span>
                      <span className="font-mono text-slate-700 font-bold">Queue: {emp.queue_size || 0}</span>
                    </div>
                    <div className="text-slate-800 font-medium truncate" title={emp.current_task}>
                      {emp.current_task || "Idle / Ready"}
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-2 pt-1 text-center">
                    <div className="p-2 bg-slate-50 rounded-lg">
                      <div className="text-[10px] text-slate-400">Success Rate</div>
                      <div className="text-sm font-bold text-emerald-600">{emp.success_rate || 98.5}%</div>
                    </div>
                    <div className="p-2 bg-slate-50 rounded-lg">
                      <div className="text-[10px] text-slate-400">Completed Tasks</div>
                      <div className="text-sm font-bold text-slate-800">{emp.completed_tasks || 0}</div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleHeartbeat(emp.id)}
                      disabled={actingId === emp.id}
                      className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1"
                    >
                      <Activity className="w-3 h-3 text-blue-600" />
                      <span>Ping</span>
                    </button>

                    {emp.health !== "HEALTHY" && (
                      <button
                        onClick={() => handleRecover(emp.id)}
                        disabled={actingId === emp.id}
                        className="px-2.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1"
                      >
                        <Wrench className="w-3 h-3" />
                        <span>Recover</span>
                      </button>
                    )}
                  </div>

                  <Link
                    href={`/ai/employees/${emp.id}`}
                    className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                  >
                    <span>Full Profile</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
