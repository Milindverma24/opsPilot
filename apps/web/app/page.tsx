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

  useEffect(() => {
    // If not logged in, redirect to login
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }

    api.dashboard
      .get()
      .then((res) => setData(res))
      .catch((err) => console.error("Error fetching dashboard metrics:", err))
      .finally(() => setLoading(false));
  }, []);

  const metrics = data?.metrics || {
    total_operations: 34,
    ai_processed: 30,
    pending_approvals: 2,
    failed_workflows: 1,
    automation_rate: 88.2,
    human_intervention_rate: 11.8,
    average_processing_time_sec: 4.8,
    average_ai_latency_ms: 320,
    estimated_savings_inr: 42500,
    hours_saved: 85,
  };

  const charts = data?.charts || {
    operations_over_time: [
      { date: "Feb 23", invoices: 4, complaints: 2, pos: 3 },
      { date: "Feb 24", invoices: 6, complaints: 3, pos: 2 },
      { date: "Feb 25", invoices: 5, complaints: 4, pos: 4 },
      { date: "Feb 26", invoices: 8, complaints: 2, pos: 3 },
      { date: "Feb 27", invoices: 7, complaints: 5, pos: 5 },
      { date: "Feb 28", invoices: 9, complaints: 4, pos: 4 },
      { date: "Mar 01", invoices: 11, complaints: 3, pos: 6 },
    ],
    operations_by_type: [
      { name: "Invoices", value: 20, color: "#3B82F6" },
      { name: "Complaints", value: 15, color: "#EF4444" },
      { name: "Purchase Orders", value: 10, color: "#10B981" },
      { name: "General Ops", value: 5, color: "#8B5CF6" },
    ],
    risk_distribution: [
      { level: "LOW", count: 14, color: "#10B981" },
      { level: "MEDIUM", count: 8, color: "#F59E0B" },
      { level: "HIGH", count: 4, color: "#F97316" },
      { level: "CRITICAL", count: 2, color: "#EF4444" },
    ],
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Operations Command Center"
          subtitle="Real-time autonomous workload telemetry & multi-agent oversight"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Hero Banner with Primary Demo link */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-950 rounded-2xl p-6 text-white border border-slate-800 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold border border-blue-500/30">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Autonomous AI Fleet Active</span>
              </div>
              <h2 className="text-xl font-bold tracking-tight">
                OpsPilot is currently running at {metrics.automation_rate}% automation efficiency
              </h2>
              <p className="text-xs text-slate-300 max-w-2xl">
                11 specialized agents are continuously validating incoming documents, enforcing corporate compliance policies, evaluating risk, and queuing high-value operations for human review.
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Link
                href="/test-lab"
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-colors flex items-center gap-1.5"
              >
                <span>Interactive Test Lab</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/documents"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-md transition-colors flex items-center gap-1.5"
              >
                <span>Upload Invoice</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* KPI 1: Automation Rate */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Automation Rate
                </span>
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-black text-slate-900">
                  {metrics.automation_rate}%
                </div>
                <div className="text-xs text-emerald-600 font-medium mt-0.5 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>{metrics.ai_processed} operations fully automated</span>
                </div>
              </div>
            </div>

            {/* KPI 2: Pending Approvals */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Pending Approvals
                </span>
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-black text-slate-900">
                  {metrics.pending_approvals}
                </div>
                <Link
                  href="/approvals"
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-0.5 flex items-center gap-0.5"
                >
                  <span>Requires Manager Review</span>
                  <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {/* KPI 3: Average Cycle Time */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Avg Cycle Time
                </span>
                <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Activity className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-black text-slate-900">
                  {metrics.average_processing_time_sec}s
                </div>
                <div className="text-xs text-slate-500 font-medium mt-0.5">
                  Manual baseline was ~15 mins
                </div>
              </div>
            </div>

            {/* KPI 4: Estimated Business Value */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Est. Cost Savings
                </span>
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Coins className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-black text-slate-900">
                  {formatCurrency(metrics.estimated_savings_inr)}
                </div>
                <div className="text-xs text-emerald-600 font-medium mt-0.5">
                  Saved approx. {metrics.hours_saved} labor hours
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart 1: Operations Over Time */}
            <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Operations Processed Over Time
                  </h3>
                  <p className="text-xs text-slate-500">
                    Daily volume across Invoices, Complaints, and Purchase Orders
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-md">
                  Last 7 Days
                </span>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={charts.operations_over_time}>
                    <defs>
                      <linearGradient id="colorInv" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="colorComp" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderRadius: "8px",
                        color: "#fff",
                        fontSize: "12px",
                        border: "none",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="invoices"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorInv)"
                      name="Invoices"
                    />
                    <Area
                      type="monotone"
                      dataKey="complaints"
                      stroke="#EF4444"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorComp)"
                      name="Complaints"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Operations by Type */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Operations by Category
                </h3>
                <p className="text-xs text-slate-500">
                  Distribution of workload by business stream
                </p>
              </div>

              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={charts.operations_by_type}
                      innerRadius={55}
                      outerRadius={75}
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
                        borderRadius: "8px",
                        color: "#fff",
                        fontSize: "12px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                {charts.operations_by_type.map((item: any) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-slate-600 font-medium truncate">{item.name}</span>
                    <span className="font-bold text-slate-900 ml-auto">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick Shortcuts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/test-lab"
              className="p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-colors flex items-center gap-4 group"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Run Automated Test Lab</h4>
                <p className="text-[11px] text-slate-500">14 automated test scenarios including prompt injection and failure handling</p>
              </div>
            </Link>

            <Link
              href="/approvals"
              className="p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-colors flex items-center gap-4 group"
            >
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Review Pending Approvals</h4>
                <p className="text-[11px] text-slate-500">Inspect invoices exceeding ₹100,000 or customer refund requests</p>
              </div>
            </Link>

            <Link
              href="/agents"
              className="p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-colors flex items-center gap-4 group"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">View 11 AI Agents Fleet</h4>
                <p className="text-[11px] text-slate-500">Monitor Intake, Extraction, Risk, Planning, and Supervisor agents</p>
              </div>
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
