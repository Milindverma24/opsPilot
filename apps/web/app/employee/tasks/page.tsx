"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  ClipboardList,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  CheckSquare,
  Package,
  ArrowRight,
  RefreshCw,
  UserCheck,
  Zap,
  Filter,
  Layers,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";

export default function EmployeeTasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"pending" | "completed">("pending");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [recoveringLeases, setRecoveringLeases] = useState(false);

  const fetchTasks = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    try {
      const res = await api.tasks.list({ limit: 100 });
      setTasks(res.tasks || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load employee tasks:", err);
    } finally {
      if (!isBackground) setLoading(false);
    }
  };

  // Real-time polling every 3 seconds (no manual refresh needed)
  useEffect(() => {
    fetchTasks();
    const interval = setInterval(() => {
      fetchTasks(true);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleClaim = async (taskId: string) => {
    setActionLoading(taskId);
    try {
      await api.tasks.claim(taskId);
      await fetchTasks(true);
    } catch (err: any) {
      alert(`Could not claim task: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleComplete = async (taskId: string) => {
    setActionLoading(taskId);
    try {
      await api.tasks.complete(taskId, "Pick & pack verified by warehouse staff", {
        verified_by: "warehouse_associate_01",
        packed_at: new Date().toISOString(),
      });
      await fetchTasks(true);
    } catch (err: any) {
      alert(`Could not complete task: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRecoverStale = async () => {
    setRecoveringLeases(true);
    try {
      const res = await api.tasks.recoverStale();
      alert(`Lease Recovery: ${res.recovered_count} stale leases recovered.`);
      await fetchTasks(true);
    } catch (err: any) {
      alert(`Error recovering leases: ${err.message}`);
    } finally {
      setRecoveringLeases(false);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (activeTab === "pending") {
      if (t.status === "COMPLETED" || t.status === "CANCELLED") return false;
    } else {
      if (t.status !== "COMPLETED" && t.status !== "CANCELLED") return false;
    }
    if (filter === "ALL") return true;
    return t.task_type === filter || t.priority === filter;
  });

  const pendingCount = tasks.filter(
    (t) => t.status !== "COMPLETED" && t.status !== "CANCELLED"
  ).length;
  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Warehouse & Operations Task Dispatcher"
          subtitle="Real-time employee execution queue dispatching autonomous AI workflow directives"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Real-time Status Banner */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <span className="flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                </span>
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  Live Dispatch Bus Connected
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    3s Polling Active
                  </span>
                </h2>
                <p className="text-xs text-slate-500">
                  New orders and AI workflow requirements populate automatically without page refresh. Last synced:{" "}
                  {lastUpdated.toLocaleTimeString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRecoverStale}
                disabled={recoveringLeases}
                className="px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition flex items-center gap-2 border border-slate-200 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${recoveringLeases ? "animate-spin" : ""}`} />
                Recover Stale Leases
              </button>
              <button
                onClick={() => fetchTasks()}
                className="px-3.5 py-2 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition flex items-center gap-2 border border-blue-200"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Force Refresh
              </button>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Pending Tasks
                </span>
                <span className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                  <Clock className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">{pendingCount}</span>
                <span className="text-xs font-medium text-amber-600">Requires Action</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Completed Today
                </span>
                <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                  <CheckCircle2 className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">{completedCount}</span>
                <span className="text-xs font-medium text-emerald-600">SLA 100%</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Pick & Pack Queue
                </span>
                <span className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <Package className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">
                  {tasks.filter((t) => t.task_type === "PICK_AND_PACK" && t.status !== "COMPLETED").length}
                </span>
                <span className="text-xs font-medium text-blue-600">Warehouse Tier 1</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  High Priority
                </span>
                <span className="p-2 bg-rose-50 text-rose-600 rounded-xl">
                  <ShieldAlert className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">
                  {tasks.filter((t) => (t.priority === "URGENT" || t.priority === "HIGH") && t.status !== "COMPLETED").length}
                </span>
                <span className="text-xs font-medium text-rose-600">Immediate</span>
              </div>
            </div>
          </div>

          {/* Filter & Tabs Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("pending")}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === "pending"
                    ? "bg-slate-900 text-white shadow-sm"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                <ClipboardList className="w-3.5 h-3.5" />
                Active Queue ({pendingCount})
              </button>
              <button
                onClick={() => setActiveTab("completed")}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === "completed"
                    ? "bg-slate-900 text-white shadow-sm"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                History ({completedCount})
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Filter:</span>
              {["ALL", "PICK_AND_PACK", "INVENTORY_VERIFICATION", "HIGH"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                    filter === f
                      ? "bg-blue-600 text-white"
                      : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {f.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          {/* Tasks List */}
          {loading ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-600">Loading task queue...</p>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
              <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-900">Task Queue Clear</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                No tasks matching the selected filter. As customer orders arrive or AI workflows require human touch, new tasks will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredTasks.map((t) => {
                const isClaimed = t.status === "CLAIMED" || t.status === "IN_PROGRESS";
                const isCompleted = t.status === "COMPLETED";
                const orderData = t.payload?.order;
                const items = t.payload?.items || (orderData?.items ? orderData.items : []);

                return (
                  <div
                    key={t.id}
                    className={`bg-white rounded-2xl border transition shadow-sm hover:shadow-md p-6 ${
                      t.priority === "URGENT"
                        ? "border-rose-300 bg-rose-50/20"
                        : t.priority === "HIGH"
                        ? "border-amber-300"
                        : "border-slate-200"
                    }`}
                  >
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                      {/* Left: Task Identity & Description */}
                      <div className="space-y-2 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                              t.status === "COMPLETED"
                                ? "bg-emerald-100 text-emerald-800"
                                : t.status === "IN_PROGRESS"
                                ? "bg-blue-100 text-blue-800"
                                : t.status === "CLAIMED"
                                ? "bg-indigo-100 text-indigo-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {t.status.replace("_", " ")}
                          </span>

                          <span
                            className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase ${
                              t.priority === "URGENT"
                                ? "bg-rose-100 text-rose-800"
                                : t.priority === "HIGH"
                                ? "bg-orange-100 text-orange-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {t.priority} Priority
                          </span>

                          <span className="text-xs font-mono text-slate-400">ID: {t.id.slice(0, 8)}</span>

                          {t.assigned_to && (
                            <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 flex items-center gap-1">
                              <UserCheck className="w-3 h-3 text-blue-600" />
                              Assigned
                            </span>
                          )}
                        </div>

                        <div>
                          <h3 className="text-base font-bold text-slate-900">{t.title}</h3>
                          <p className="text-xs text-slate-600 mt-0.5">{t.description}</p>
                        </div>

                        {/* Order & Items Details Breakdown */}
                        {items && items.length > 0 && (
                          <div className="mt-3 p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-1.5">
                            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                              Fulfillment Manifest:
                            </span>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {items.map((it: any, idx: number) => (
                                <div
                                  key={idx}
                                  className="text-xs bg-white p-2 rounded-lg border border-slate-200 flex items-center justify-between"
                                >
                                  <div>
                                    <span className="font-semibold text-slate-900">
                                      {it.product_name || it.title || "Catalog Item"}
                                    </span>
                                    <div className="text-[10px] text-slate-500">
                                      SKU: {it.sku || "N/A"} {it.size ? `| Size: ${it.size}` : ""} {it.color ? `| Color: ${it.color}` : ""}
                                    </div>
                                  </div>
                                  <span className="px-2 py-0.5 bg-blue-50 text-blue-700 font-bold rounded text-xs">
                                    Qty: {it.quantity || 1}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right: Actions */}
                      <div className="flex flex-col sm:flex-row lg:flex-col items-end gap-2 shrink-0">
                        {t.status === "CREATED" && (
                          <button
                            onClick={() => handleClaim(t.id)}
                            disabled={actionLoading === t.id}
                            className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center justify-center gap-2"
                          >
                            <Play className="w-3.5 h-3.5" />
                            Claim Task
                          </button>
                        )}

                        {isClaimed && (
                          <button
                            onClick={() => handleComplete(t.id)}
                            disabled={actionLoading === t.id}
                            className="w-full sm:w-auto px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center justify-center gap-2"
                          >
                            <CheckSquare className="w-3.5 h-3.5" />
                            Complete Pick & Pack
                          </button>
                        )}

                        <Link
                          href={`/employee/tasks/${t.id}`}
                          className="w-full sm:w-auto px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 border border-slate-200"
                        >
                          Step-by-Step View
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>

                    {/* Footer / Progress */}
                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-slate-400" />
                        Created {new Date(t.created_at).toLocaleString()}
                      </span>
                      {t.current_step && (
                        <span className="font-medium text-slate-700">
                          Active Step: <span className="font-mono text-blue-600">{t.current_step}</span>
                        </span>
                      )}
                      <span className="font-semibold text-slate-600">
                        Progress: {t.progress_percent || 0}%
                      </span>
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
