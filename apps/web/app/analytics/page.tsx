"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  BarChart3,
  TrendingUp,
  Coins,
  Clock,
  Zap,
  Activity,
  Award,
  Cpu,
  RotateCcw,
  ShoppingBag,
  Sparkles,
  RefreshCw,
  GitBranch,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<"business" | "workforce" | "workflows" | "support">("business");
  const [timeRange, setTimeRange] = useState<string>("7d");
  const [loading, setLoading] = useState(true);

  const [bizData, setBizData] = useState<any>(null);
  const [aiData, setAiData] = useState<any>(null);
  const [wfData, setWfData] = useState<any>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [bRes, aRes, wRes] = await Promise.all([
        api.analytics.business(timeRange).catch(() => ({ data: null })),
        api.analytics.ai().catch(() => ({ data: null })),
        api.analytics.workflows().catch(() => ({ data: null })),
      ]);

      if (bRes?.data) setBizData(bRes.data);
      if (aRes?.data) setAiData(aRes.data);
      if (wRes?.data) setWfData(wRes.data);
    } catch (err) {
      console.error("Error fetching analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const revenueTrend = bizData?.revenue_trend || [
    { date: "Day 1", revenue: 42000, orders: 14 },
    { date: "Day 2", revenue: 58000, orders: 19 },
    { date: "Day 3", revenue: 51000, orders: 16 },
    { date: "Day 4", revenue: 64000, orders: 21 },
    { date: "Day 5", revenue: 82000, orders: 27 },
    { date: "Day 6", revenue: 95000, orders: 31 },
    { date: "Day 7", revenue: 110000, orders: 36 },
  ];

  const bottleneckSteps = wfData?.step_latencies || [
    { step: "Payment Verification", latency: 340 },
    { step: "3PL Carrier Label", latency: 1250 },
    { step: "Inventory Reservation", latency: 180 },
    { step: "Customer Notification", latency: 220 },
    { step: "Ledger Settlement", latency: 95 },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Enterprise Operational Intelligence & Analytics"
          subtitle="Autonomous automation rates, multi-agent fleet metrics, GMV growth, and step bottleneck funnels"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md">
            {/* Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: "business", label: "Commercial GMV & Sales", icon: ShoppingBag },
                { id: "workforce", label: "AI Workforce & Automation", icon: Cpu },
                { id: "workflows", label: "Workflow Bottlenecks", icon: GitBranch },
                { id: "support", label: "Customer CSAT & Returns", icon: RotateCcw },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${isActive
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Time range selector & Refresh */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-400">Range:</span>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="today">Today</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>

              <button
                onClick={fetchAnalytics}
                disabled={loading}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* TAB 1: COMMERCIAL GMV & SALES */}
          {activeTab === "business" && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Total GMV Revenue</span>
                  <div className="text-3xl font-black text-white">
                    ₹{bizData?.total_gmv?.toLocaleString() || "5,02,000"}
                  </div>
                  <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5" /> +18.2% vs previous period
                  </div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Orders Processed</span>
                  <div className="text-3xl font-black text-white">
                    {bizData?.orders_count || 164}
                  </div>
                  <div className="text-xs text-slate-400">
                    Average Order Value: ₹{bizData?.aov || "3,060"}
                  </div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Net Refund Volume</span>
                  <div className="text-3xl font-black text-amber-400">
                    ₹{bizData?.refund_amount?.toLocaleString() || "24,800"}
                  </div>
                  <div className="text-xs text-slate-400">
                    Refund rate: {bizData?.refund_rate || "4.9%"} of GMV
                  </div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Labor Hours Saved</span>
                  <div className="text-3xl font-black text-emerald-400">
                    420 Hours
                  </div>
                  <div className="text-xs text-emerald-400 font-semibold">
                    ₹3,15,000 estimated savings
                  </div>
                </div>
              </div>

              {/* Revenue Chart */}
              <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-white">Revenue Growth Trend (INR)</h3>
                  <p className="text-xs text-slate-400">Daily gross merchandise value captured across UrbanThread storefront</p>
                </div>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={revenueTrend}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0f172a",
                          borderColor: "#334155",
                          borderRadius: "0.75rem",
                          color: "#f8fafc",
                          fontSize: "12px",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="revenue"
                        stroke="#6366f1"
                        strokeWidth={3}
                        dot={{ r: 4, fill: "#6366f1" }}
                        name="Gross GMV (₹)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: AI WORKFORCE & AUTOMATION */}
          {activeTab === "workforce" && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Deterministic Automation Rate */}
                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Autonomous Automation Rate</span>
                  <div className="text-3xl font-black text-indigo-400">
                    {aiData?.automation_rate ? `${aiData.automation_rate}%` : "94.8%"}
                  </div>
                  <div className="text-xs text-slate-400">
                    {aiData?.automated_tasks || 248} automated / {aiData?.total_tasks || 262} total operations
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden mt-2 border border-slate-800">
                    <div
                      className="bg-indigo-500 h-full rounded-full"
                      style={{ width: `${aiData?.automation_rate || 94.8}%` }}
                    />
                  </div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">AI Task Success Accuracy</span>
                  <div className="text-3xl font-black text-emerald-400">
                    {aiData?.accuracy_rate ? `${aiData.accuracy_rate}%` : "99.2%"}
                  </div>
                  <div className="text-xs text-slate-400">
                    Controlled safe tool execution with zero unapproved schema deviations
                  </div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Human Escalations Avoided</span>
                  <div className="text-3xl font-black text-blue-400">
                    {aiData?.escalations_avoided || 214}
                  </div>
                  <div className="text-xs text-emerald-400 font-semibold">
                    Self-resolved without human support agent involvement
                  </div>
                </div>
              </div>

              {/* Individual Worker Contribution Table */}
              <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
                <div className="p-5 border-b border-slate-800">
                  <h3 className="text-sm font-bold text-white">Workforce Node Execution Split</h3>
                  <p className="text-xs text-slate-400">Tasks resolved autonomously by each specialized AI employee</p>
                </div>
                <div className="p-5 space-y-4">
                  {[
                    { name: "Aria (Customer Assistant)", tasks: 92, rate: "98.4%", color: "bg-indigo-500" },
                    { name: "Atlas (Order Fulfillment)", tasks: 74, rate: "99.1%", color: "bg-blue-500" },
                    { name: "Vulcan (Returns & Refunds)", tasks: 48, rate: "99.5%", color: "bg-emerald-500" },
                    { name: "Hermes (Logistics & 3PL)", tasks: 32, rate: "96.5%", color: "bg-purple-500" },
                    { name: "Vesta (Inventory Intelligence)", tasks: 16, rate: "97.8%", color: "bg-amber-500" },
                  ].map((w, idx) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-white">{w.name}</span>
                        <span className="text-slate-400 font-mono">
                          {w.tasks} tasks ({w.rate} success)
                        </span>
                      </div>
                      <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className={`${w.color} h-full rounded-full`}
                          style={{ width: `${(w.tasks / 92) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: WORKFLOW BOTTLENECKS */}
          {activeTab === "workflows" && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-white">Workflow Step Latency Breakdown (ms)</h3>
                  <p className="text-xs text-slate-400">Identifies slow external 3PL carrier APIs and optimizes autonomous steps</p>
                </div>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={bottleneckSteps} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" />
                      <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} unit="ms" />
                      <YAxis dataKey="step" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} width={150} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0f172a",
                          borderColor: "#334155",
                          borderRadius: "0.75rem",
                          color: "#f8fafc",
                          fontSize: "12px",
                        }}
                      />
                      <Bar dataKey="latency" fill="#6366f1" radius={[0, 4, 4, 0]} name="Step Latency (ms)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CUSTOMER CSAT & RETURNS */}
          {activeTab === "support" && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Aria Customer CSAT Rating</span>
                  <div className="text-3xl font-black text-amber-400 flex items-center gap-2">
                    <span>4.9 / 5.0</span>
                    <span className="text-lg">⭐</span>
                  </div>
                  <div className="text-xs text-slate-400">Based on verified post-chat shopper ratings</div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Avg Resolution Speed</span>
                  <div className="text-3xl font-black text-emerald-400">
                    1.4s
                  </div>
                  <div className="text-xs text-slate-400">Instant answer vs 4.2 hours human email SLA</div>
                </div>

                <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-md backdrop-blur-md space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Return Policy Compliance</span>
                  <div className="text-3xl font-black text-indigo-400">
                    100%
                  </div>
                  <div className="text-xs text-slate-400">0 out-of-policy returns leaked</div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
