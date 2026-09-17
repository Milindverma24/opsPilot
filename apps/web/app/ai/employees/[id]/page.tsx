"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
  ChevronLeft,
  RefreshCw,
  Sliders,
  Sparkles,
  Terminal,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function AIEmployeeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [employee, setEmployee] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.aiEmployees.get(id);
      setEmployee(res.data);
    } catch (err) {
      console.error("Failed to load AI employee detail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleHeartbeat = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.aiEmployees.heartbeat(id, {
        current_task: "Manual telemetry diagnostic check",
        queue_size: 0,
      });
      await fetchDetail();
    } catch (err: any) {
      alert("Heartbeat failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecover = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.aiEmployees.recover(id);
      await fetchDetail();
    } catch (err: any) {
      alert("Recovery failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !employee) {
    return (
      <div className="flex h-screen bg-slate-950 text-slate-100">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-indigo-400 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Loading AI Employee profile...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="flex h-screen bg-slate-950 text-slate-100">
        <Sidebar />
        <div className="flex-1 p-8 space-y-4">
          <Link href="/ai/employees" className="flex items-center gap-1 text-sm text-indigo-400 font-semibold hover:text-indigo-300">
            <ChevronLeft className="w-4 h-4" /> Back to Fleet
          </Link>
          <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800">
            <h1 className="text-lg font-bold text-white">AI Employee Not Found</h1>
            <p className="text-xs text-slate-400 mt-1">The specified AI worker node could not be located.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title={`${employee.name} • Autonomous Agent Node`}
          subtitle="Real-time worker telemetry, execution history, configuration, and security sandbox policies"
        />

        <main className="p-6 space-y-6 max-w-6xl mx-auto w-full">
          {/* Back link & actions */}
          <div className="flex items-center justify-between">
            <Link
              href="/ai/employees"
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back to AI Workforce</span>
            </Link>

            <div className="flex items-center gap-2">
              <button
                onClick={handleHeartbeat}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs font-semibold text-slate-200 transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-indigo-400" />
                <span>Send Heartbeat</span>
              </button>

              <button
                onClick={handleRecover}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
              >
                <Wrench className="w-3.5 h-3.5" />
                <span>Trigger Recovery</span>
              </button>
            </div>
          </div>

          {/* Profile Overview Card */}
          <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl p-6 space-y-5 backdrop-blur-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-black text-2xl shadow-lg shadow-indigo-500/20">
                  {employee.name[0]}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-black text-white tracking-tight">{employee.name}</h1>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {employee.health}
                    </span>
                  </div>
                  <div className="text-xs text-indigo-300 font-mono mt-0.5">
                    ID: #{employee.id} • Role: {employee.role}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xs text-slate-400">Success Rate</div>
                  <div className="text-xl font-black text-emerald-400">{employee.success_rate || 99.2}%</div>
                </div>
                <div className="text-right pl-4 border-l border-slate-800">
                  <div className="text-xs text-slate-400">Total Tasks</div>
                  <div className="text-xl font-black text-white">
                    {(employee.completed_tasks || 0) + (employee.failed_tasks || 0)}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">{employee.description}</p>

            {/* Telemetry Snapshot */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400">Current Assigned Task</div>
                <div className="text-xs font-semibold text-white truncate">
                  {employee.current_task || "Idle"}
                </div>
              </div>
              <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400">Active Queue Depth</div>
                <div className="text-xs font-semibold text-indigo-300 font-mono">
                  {employee.queue_size || 0} tasks pending
                </div>
              </div>
              <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400">Last Telemetry Heartbeat</div>
                <div className="text-xs font-semibold text-slate-200 font-mono">
                  {employee.last_heartbeat_at ? new Date(employee.last_heartbeat_at).toLocaleTimeString() : "Just now"}
                </div>
              </div>
            </div>
          </div>

          {/* Permissions & Capabilities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                RBAC & Execution Permissions
              </h2>
              <p className="text-xs text-slate-400">Allowed actions strictly bounded by organization safety policies</p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {(employee.permissions || ["orders.read", "support.read", "knowledge.read"]).map(
                  (perm: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-indigo-300 font-medium"
                    >
                      {perm}
                    </span>
                  )
                )}
              </div>
            </div>

            <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                Worker Runtime Configuration
              </h2>
              <p className="text-xs text-slate-400">Model temperature, max step iterations, and safety sandbox flags</p>
              <pre className="p-3 bg-slate-950 text-indigo-300 border border-slate-800 rounded-xl text-xs font-mono overflow-x-auto">
                {JSON.stringify(
                  employee.configuration || {
                    runtime: "Python 3.12 Autonomous Daemon",
                    max_loop_iterations: 8,
                    escalate_on_consecutive_failures: 2,
                    timeout_seconds: 30,
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
