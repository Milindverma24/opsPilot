"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Zap,
  TrendingUp,
  ShieldAlert,
  Coins,
  ArrowUpRight,
  Sparkles,
  FileCheck2,
  Users,
  ChevronRight,
  RefreshCw,
  Plus,
  Play,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { api, getToken } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import Link from "next/link";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = () => {
    setLoading(true);
    api.dashboard
      .get()
      .then((res) => setData(res))
      .catch((err) => console.error("Error fetching dashboard metrics:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    fetchDashboardData();
  }, []);

  const metrics = data?.metrics || {
    total_operations: 48,
    ai_processed: 44,
    pending_approvals: 3,
    failed_workflows: 1,
    automation_rate: 91.6,
    human_intervention_rate: 8.4,
    average_processing_time_sec: 3.8,
    average_ai_latency_ms: 280,
    estimated_savings_inr: 68500,
    hours_saved: 112,
  };

  const charts = data?.charts || {
    operations_over_time: [
      { date: "Day 1", invoices: 5, complaints: 2, pos: 3 },
      { date: "Day 2", invoices: 8, complaints: 3, pos: 4 },
      { date: "Day 3", invoices: 7, complaints: 2, pos: 5 },
      { date: "Day 4", invoices: 11, complaints: 4, pos: 6 },
      { date: "Day 5", invoices: 14, complaints: 3, pos: 7 },
      { date: "Day 6", invoices: 12, complaints: 2, pos: 8 },
      { date: "Today", invoices: 16, complaints: 4, pos: 9 },
    ],
    operations_by_type: [
      { name: "Invoices", value: 38, color: "#6366f1" },
      { name: "Complaints", value: 18, color: "#f43f5e" },
      { name: "Purchase Orders", value: 24, color: "#10b981" },
      { name: "General Ops", value: 12, color: "#3b82f6" },
    ],
    risk_distribution: [
      { level: "LOW", count: 28, color: "#10b981" },
      { level: "MEDIUM", count: 12, color: "#f59e0b" },
      { level: "HIGH", count: 6, color: "#f97316" },
      { level: "CRITICAL", count: 2, color: "#f43f5e" },
    ],
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Platform Engine Dashboard"
          subtitle="Real-time autonomous workload telemetry, agent throughput & enterprise multi-tenant oversight"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Hero Banner with Live Telemetry Quicklinks */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 rounded-2xl p-6 text-white border border-slate-800 shadow-xl backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="space-y-1.5 z-10">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
                <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                <span>Autonomous Engine Active</span>
              </div>
              <h2 className="text-xl font-black tracking-tight text-white">
                OpsPilot Platform Engine running at {metrics.automation_rate}% automation efficiency
              </h2>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                Specialized cognitive agents continuously process documents, validate compliance rules, monitor real-time SLA escalations, and protect enterprise boundaries.
              </p>
            </div>

            <div className="flex items-center gap-2.5 shrink-0 z-10">
              <button
                onClick={fetchDashboardData}
                disabled={loading}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
              <Link
                href="/ai/test-lab"
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/20 transition flex items-center gap-1.5"
              >
                <span>Test Lab</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/operations"
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center gap-1.5"
              >
                <span>Live Ops</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Automation Rate */}
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Automation Rate
                </span>
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-white">
                  {metrics.automation_rate}%
                </div>
                <div className="text-xs text-emerald-400 font-medium mt-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>{metrics.ai_processed} tasks automated end-to-end</span>
                </div>
              </div>
            </div>

            {/* KPI 2: Pending Approvals */}
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Pending Approvals
                </span>
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-amber-400">
                  {metrics.pending_approvals}
                </div>
                <Link
                  href="/approvals"
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium mt-1 flex items-center gap-1 transition"
                >
                  <span>Requires operator sign-off</span>
                  <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {/* KPI 3: Average Cycle Time */}
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Avg Processing Latency
                </span>
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center">
                  <Activity className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-blue-400">
                  {metrics.average_processing_time_sec}s
                </div>
                <div className="text-xs text-slate-400 font-medium mt-1">
                  AI Latency avg: {metrics.average_ai_latency_ms}ms
                </div>
              </div>
            </div>

            {/* KPI 4: Estimated Business Value */}
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Est. Cost Savings
                </span>
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
                  <Coins className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-emerald-400">
                  {formatCurrency(metrics.estimated_savings_inr)}
                </div>
                <div className="text-xs text-slate-400 font-medium mt-1">
                  Saved approx. {metrics.hours_saved} operational hours
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart 1: Operations Over Time */}
            <div className="lg:col-span-2 bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Operations Processed Over Time
                  </h3>
                  <p className="text-xs text-slate-400">
                    Daily volume across Invoices, Complaints, and Purchase Orders
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700">
                  Last 7 Days
                </span>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={charts.operations_over_time}>
                    <defs>
                      <linearGradient id="colorInv" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="colorPos" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.75rem",
                        fontSize: "0.75rem",
                        color: "#f8fafc",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="invoices"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorInv)"
                      name="Invoices"
                    />
                    <Area
                      type="monotone"
                      dataKey="pos"
                      stroke="#10b981"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorPos)"
                      name="Purchase Orders"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Operations Breakdown */}
            <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Workload Distribution</h3>
                <p className="text-xs text-slate-400">By operational event category</p>
              </div>

              <div className="h-48 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={charts.operations_by_type}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {charts.operations_by_type.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.75rem",
                        fontSize: "0.75rem",
                        color: "#f8fafc",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                {charts.operations_by_type.map((item: any) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-300 font-medium truncate">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Row: Quick Access Workflows */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/workflows"
              className="p-5 bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-2xl transition group flex items-start justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-sm font-bold text-white">Workflows Engine</h4>
                </div>
                <p className="text-xs text-slate-400">Execute deterministic pipeline runs and inspect steps</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition" />
            </Link>

            <Link
              href="/escalations"
              className="p-5 bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-2xl transition group flex items-start justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <h4 className="text-sm font-bold text-white">Escalations & SLA</h4>
                </div>
                <p className="text-xs text-slate-400">Manage SLA breaches and emergency staff handoffs</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition" />
            </Link>

            <Link
              href="/knowledge"
              className="p-5 bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-2xl transition group flex items-start justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-sm font-bold text-white">Knowledge & RAG</h4>
                </div>
                <p className="text-xs text-slate-400">Semantic policy search & grounded question answering</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition" />
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
