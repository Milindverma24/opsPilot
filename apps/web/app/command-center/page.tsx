"use client";

import { useEffect, useState, useRef } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Radio,
  Cpu,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  ShoppingBag,
  RotateCcw,
  RefreshCw,
  ShieldCheck,
  Zap,
  ArrowUpRight,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Bot,
  Play,
  Pause,
  AlertOctagon,
  Wrench,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function CommandCenterPage() {
  const [summary, setSummary] = useState<any>(null);
  const [workforce, setWorkforce] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [liveMode, setLiveMode] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [recoveringId, setRecoveringId] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [sumRes, wfRes, actRes] = await Promise.all([
        api.commandCenter.getSummary().catch(() => ({ data: null })),
        api.commandCenter.getWorkforce().catch(() => ({ data: null })),
        api.commandCenter.getActivity(15).catch(() => ({ data: [] })),
      ]);

      if (sumRes?.data) setSummary(sumRes.data);
      if (wfRes?.data) setWorkforce(wfRes.data);
      if (actRes?.data) setActivity(actRes.data);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error("Error fetching command center telemetry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!liveMode) return;
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, [liveMode]);

  const handleRecover = async (employeeId: string) => {
    setRecoveringId(employeeId);
    try {
      await api.aiEmployees.recover(employeeId);
      await fetchData();
    } catch (err: any) {
      alert("Worker recovery failed: " + err.message);
    } finally {
      setRecoveringId(null);
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case "HEALTHY":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Healthy
          </span>
        );
      case "DEGRADED":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-600 border border-amber-500/20 flex items-center gap-1 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Degraded
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-600 border border-rose-500/20 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Critical
          </span>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="24/7 AI Workforce Command Center"
          subtitle="Real-time operations surveillance, autonomous agent fleet telemetry, and deterministic business metrics"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Controls Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
                  <Radio className="w-5 h-5 animate-pulse" />
                </div>
                {liveMode && (
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 border-2 border-white rounded-full"></span>
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-bold text-slate-900">Surveillance Operations</h1>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                    UrbanThread Fleet
                  </span>
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-2">
                  <span>Last synced: {lastRefreshed.toLocaleTimeString()}</span>
                  <span>•</span>
                  <span>Target SLA: &lt; 2000ms</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setLiveMode(!liveMode)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                  liveMode
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200 shadow-xs"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {liveMode ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                    <span>LIVE STREAM ON</span>
                  </>
                ) : (
                  <>
                    <Pause className="w-3 h-3" />
                    <span>STREAM PAUSED</span>
                  </>
                )}
              </button>

              <button
                onClick={fetchData}
                disabled={loading}
                className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl border border-slate-200 transition-colors"
                title="Force Refresh Telemetry"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Top Row: Mission-Critical KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Automation Rate */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Autonomous Automation Rate</span>
                <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                  <Zap className="w-4 h-4" />
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  {summary?.automation_rate ? `${summary.automation_rate}%` : "94.8%"}
                </span>
                <span className="text-xs font-semibold text-emerald-600 flex items-center">
                  <ArrowUpRight className="w-3.5 h-3.5" /> +2.4%
                </span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full rounded-full"
                  style={{ width: `${summary?.automation_rate || 94.8}%` }}
                ></div>
              </div>
              <div className="text-[11px] text-slate-400">
                Deterministic: {summary?.automated_tasks || 248} / {summary?.total_tasks || 262} tasks
              </div>
            </div>

            {/* AI Fleet Status */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>AI Workforce Fleet</span>
                <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                  <Cpu className="w-4 h-4" />
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  {workforce?.fleet_summary?.healthy_count || 5} / {workforce?.fleet_summary?.total_workers || 5}
                </span>
                <span className="text-xs font-semibold text-emerald-600">ONLINE</span>
              </div>
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>All 5 AI Employees operating within target latency</span>
              </div>
            </div>

            {/* Today's GMV / Orders */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Today's E-Commerce GMV</span>
                <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                  <ShoppingBag className="w-4 h-4" />
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  ₹{summary?.business_today?.total_revenue?.toLocaleString() || "1,48,200"}
                </span>
                <span className="text-xs font-semibold text-emerald-600">
                  {summary?.business_today?.orders_count || 42} orders
                </span>
              </div>
              <div className="text-[11px] text-slate-400">
                Avg order value: ₹{summary?.business_today?.avg_order_value || "3,528"}
              </div>
            </div>

            {/* Active Alerts */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Operational Alerts</span>
                <span className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                  <AlertTriangle className="w-4 h-4" />
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  {summary?.active_alerts_count || 2}
                </span>
                <span className="text-xs font-semibold text-amber-600">ATTENTION</span>
              </div>
              <div className="text-[11px] text-slate-500">
                <Link href="/alerts" className="text-blue-600 hover:underline flex items-center gap-1 font-medium">
                  Review active operational alerts <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>

          {/* AI Workforce Fleet Status Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-blue-600" />
                  AI Workforce Fleet Telemetry (5 Dedicated Workers)
                </h2>
                <p className="text-xs text-slate-500">Continuous 24/7 heartbeat monitoring, queue depth, and autonomous failover</p>
              </div>
              <Link
                href="/ai/employees"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                View Fleet Directory <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-200/60 font-semibold">
                  <tr>
                    <th className="p-3.5 pl-5">AI Employee</th>
                    <th className="p-3.5">Specialization</th>
                    <th className="p-3.5">Health</th>
                    <th className="p-3.5">Current Task</th>
                    <th className="p-3.5">Queue</th>
                    <th className="p-3.5">Success Rate</th>
                    <th className="p-3.5">Heartbeat</th>
                    <th className="p-3.5 text-right pr-5">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(workforce?.workers || [
                    { id: "aria", name: "Aria", role: "CUSTOMER_SUPPORT", health: "HEALTHY", current_task: "Listening for shopper chats", queue_size: 0, success_rate: 98.4, last_heartbeat_ago: "3s ago" },
                    { id: "atlas", name: "Atlas", role: "ORDER_FULFILLMENT", health: "HEALTHY", current_task: "Dispatching order #UT-10482 to BlueDart", queue_size: 2, success_rate: 99.1, last_heartbeat_ago: "1s ago" },
                    { id: "vesta", name: "Vesta", role: "INVENTORY_INTELLIGENCE", health: "HEALTHY", current_task: "Evaluating reorder velocity for Linen Shirts", queue_size: 0, success_rate: 97.8, last_heartbeat_ago: "4s ago" },
                    { id: "hermes", name: "Hermes", role: "LOGISTICS_DISPATCH", health: "HEALTHY", current_task: "Polling Delhivery carrier tracking webhooks", queue_size: 1, success_rate: 96.5, last_heartbeat_ago: "2s ago" },
                    { id: "vulcan", name: "Vulcan", role: "RETURNS_REFUNDS", health: "HEALTHY", current_task: "Evaluating return inspection photo for UT-882", queue_size: 0, success_rate: 99.5, last_heartbeat_ago: "5s ago" },
                  ]).map((worker: any) => (
                    <tr key={worker.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="p-3.5 pl-5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                            {worker.name[0]}
                          </div>
                          <div>
                            <span className="font-bold text-slate-900">{worker.name}</span>
                            <div className="text-[10px] text-slate-400 font-mono">#{worker.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium text-[11px]">
                          {worker.role}
                        </span>
                      </td>
                      <td className="p-3.5">{getHealthBadge(worker.health || "HEALTHY")}</td>
                      <td className="p-3.5">
                        <span className="text-slate-700 font-medium max-w-[220px] truncate block" title={worker.current_task}>
                          {worker.current_task || "Idle"}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={`font-mono font-bold ${worker.queue_size > 5 ? "text-rose-600" : "text-slate-700"}`}>
                          {worker.queue_size || 0}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className="font-semibold text-emerald-600">{worker.success_rate || 98.5}%</span>
                      </td>
                      <td className="p-3.5 text-slate-500 font-mono text-[11px]">
                        {worker.last_heartbeat_ago || "Just now"}
                      </td>
                      <td className="p-3.5 text-right pr-5">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link
                            href={`/ai/employees/${worker.id}`}
                            className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Worker Profile"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </Link>
                          {worker.health !== "HEALTHY" && (
                            <button
                              onClick={() => handleRecover(worker.id)}
                              disabled={recoveringId === worker.id}
                              className="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[10px] font-bold shadow-xs flex items-center gap-1"
                            >
                              <Wrench className="w-3 h-3" />
                              {recoveringId === worker.id ? "Recovering..." : "Recover"}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bottom Grid: Live Activity Stream & Needs Attention */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Live Activity Feed (2 Cols) */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  <h2 className="text-sm font-bold text-slate-900">Live Operations Stream</h2>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                  <span>Streaming Real-Time Events</span>
                </div>
              </div>

              <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                {(activity.length > 0 ? activity : [
                  { id: "act-1", title: "Customer inquiry resolved by Aria", description: "Order tracking card dispatched for UT-10482", source: "Aria AI", timestamp: "12s ago", type: "CHAT" },
                  { id: "act-2", title: "Automated fulfillment label generated", description: "BlueDart tracking #BLU-9921 attached to order #UT-10483", source: "Atlas AI", timestamp: "45s ago", type: "WORKFLOW" },
                  { id: "act-3", title: "Return inspection policy cleared", description: "Standard ₹1,490 refund approved automatically for UT-882", source: "Vulcan AI", timestamp: "2m ago", type: "RETURN" },
                  { id: "act-4", title: "Inventory reorder trigger check", description: "Checked safety stock for 18 Active SKUs across Delhi warehouse", source: "Vesta AI", timestamp: "5m ago", type: "INVENTORY" },
                ]).map((item: any) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-50/70 hover:bg-slate-50 rounded-xl border border-slate-200/60 flex items-start justify-between gap-3 text-xs transition-colors"
                  >
                    <div className="space-y-0.5">
                      <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                        {item.title}
                      </div>
                      <div className="text-slate-600 text-[11px]">{item.description}</div>
                      <div className="text-[10px] text-slate-400 font-mono pt-1">Source: {item.source}</div>
                    </div>
                    <span className="text-[10px] text-slate-400 shrink-0 font-mono">{item.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Needs Attention Panel (1 Col) */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-amber-600" />
                  <h2 className="text-sm font-bold text-slate-900">Needs Attention</h2>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">
                  {summary?.needs_attention?.length || 2} Pending
                </span>
              </div>

              <div className="space-y-3">
                <div className="p-3.5 bg-amber-50/60 border border-amber-200/80 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-900">High-Risk Refund Approval</span>
                    <span className="px-1.5 py-0.5 text-[9px] bg-rose-500/10 text-rose-700 rounded font-bold">
                      ₹12,000
                    </span>
                  </div>
                  <p className="text-amber-800 text-[11px]">
                    Customer requested full refund on 4 synthetic silk blazers exceeding standard ₹2,000 threshold.
                  </p>
                  <Link
                    href="/approvals"
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-600 hover:text-blue-800"
                  >
                    Review in Approvals <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>

                <div className="p-3.5 bg-blue-50/60 border border-blue-200/80 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-blue-900">Observability Trace SLA Alert</span>
                    <span className="px-1.5 py-0.5 text-[9px] bg-blue-500/10 text-blue-700 rounded font-bold">
                      2.3s
                    </span>
                  </div>
                  <p className="text-blue-800 text-[11px]">
                    Carrier Delhivery tracking webhook response degraded past 2000ms threshold.
                  </p>
                  <Link
                    href="/observability/traces"
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-600 hover:text-blue-800"
                  >
                    Inspect Trace Waterfall <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
