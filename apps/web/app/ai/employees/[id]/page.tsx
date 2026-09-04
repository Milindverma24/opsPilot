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
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Loading AI Employee profile...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 p-8 space-y-4">
          <Link href="/ai/employees" className="flex items-center gap-1 text-sm text-blue-600 font-semibold">
            <ChevronLeft className="w-4 h-4" /> Back to Fleet
          </Link>
          <div className="p-6 bg-white rounded-2xl border border-slate-200">
            <h1 className="text-lg font-bold text-slate-800">AI Employee Not Found</h1>
            <p className="text-xs text-slate-500 mt-1">The specified AI worker node could not be located.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title={`${employee.name} • AI Employee Profile`}
          subtitle="Real-time worker telemetry, execution history, configuration, and security sandbox policies"
        />

        <main className="p-6 space-y-6 max-w-6xl mx-auto w-full">
          {/* Back link & actions */}
          <div className="flex items-center justify-between">
            <Link
              href="/ai/employees"
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-xs transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back to AI Workforce</span>
            </Link>

            <div className="flex items-center gap-2">
              <button
                onClick={handleHeartbeat}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-xs transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-blue-600" />
                <span>Send Heartbeat</span>
              </button>

              <button
                onClick={handleRecover}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors"
              >
                <Wrench className="w-3.5 h-3.5" />
                <span>Trigger Recovery</span>
              </button>
            </div>
          </div>

          {/* Profile Overview Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-black text-2xl shadow-lg shadow-blue-500/20">
                  {employee.name[0]}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-black text-slate-900 tracking-tight">{employee.name}</h1>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {employee.health}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">
                    ID: {employee.id} • Role: {employee.role}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs text-slate-400">Success Rate</div>
                  <div className="text-xl font-black text-emerald-600">{employee.success_rate}%</div>
                </div>
                <div className="text-right pl-4 border-l border-slate-200">
                  <div className="text-xs text-slate-400">Total Tasks</div>
                  <div className="text-xl font-black text-slate-800">
                    {(employee.completed_tasks || 0) + (employee.failed_tasks || 0)}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed max-w-3xl">{employee.description}</p>

            {/* Telemetry Snapshot */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/60 space-y-1">
                <div className="text-xs text-slate-500">Current Assigned Task</div>
                <div className="text-xs font-semibold text-slate-900 truncate">
                  {employee.current_task || "Idle"}
                </div>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/60 space-y-1">
                <div className="text-xs text-slate-500">Active Queue Depth</div>
                <div className="text-xs font-semibold text-slate-900 font-mono">
                  {employee.queue_size || 0} tasks pending
                </div>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/60 space-y-1">
                <div className="text-xs text-slate-500">Last Telemetry Heartbeat</div>
                <div className="text-xs font-semibold text-slate-900 font-mono">
                  {employee.last_heartbeat_at ? new Date(employee.last_heartbeat_at).toLocaleTimeString() : "Just now"}
                </div>
              </div>
            </div>
          </div>

          {/* Permissions & Capabilities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600" />
                RBAC & Execution Permissions
              </h2>
              <p className="text-xs text-slate-500">Allowed actions strictly bounded by organization safety policies</p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {(employee.permissions || ["order.read", "shipment.track", "customer.chat"]).map(
                  (perm: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-xs font-mono text-slate-700 font-medium"
                    >
                      {perm}
                    </span>
                  )
                )}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Worker Runtime Configuration
              </h2>
              <p className="text-xs text-slate-500">Model temperature, max step iterations, and safety sandbox flags</p>
              <pre className="p-3 bg-slate-900 text-blue-300 rounded-xl text-xs font-mono overflow-x-auto">
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
