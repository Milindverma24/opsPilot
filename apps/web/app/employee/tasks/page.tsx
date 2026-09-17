"use client";

import { useEffect, useState } from "react";
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
  Plus,
  X,
  Send,
  Sparkles,
  Scan,
} from "lucide-react";
import { api } from "@/lib/api";
import { BarcodeScannerModal } from "@/components/BarcodeScannerModal";

export default function EmployeeTasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"pending" | "completed">("pending");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [recoveringLeases, setRecoveringLeases] = useState(false);

  // Dispatch Task Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [taskType, setTaskType] = useState("PICK_AND_PACK");
  const [priority, setPriority] = useState("HIGH");
  const [assignedRole, setAssignedRole] = useState("WAREHOUSE_OPERATOR");
  const [orderId, setOrderId] = useState("");
  const [notes, setNotes] = useState("");

  // Barcode Scanner Modal & SSE
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scanningTask, setScanningTask] = useState<any | null>(null);
  const [sseConnected, setSseConnected] = useState(false);

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

  useEffect(() => {
    fetchTasks();

    let es: EventSource | null = null;
    try {
      es = new EventSource("http://localhost:8000/api/v1/events/stream");
      es.onopen = () => setSseConnected(true);
      es.addEventListener("task", () => fetchTasks(true));
      es.addEventListener("business_event", () => fetchTasks(true));
      es.onerror = () => setSseConnected(false);
    } catch (e) {
      console.warn("SSE stream unavailable, using fallback timer");
    }

    const interval = setInterval(() => {
      fetchTasks(true);
    }, 4000);

    return () => {
      clearInterval(interval);
      if (es) es.close();
    };
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
      alert(`Lease Recovery: ${res.recovered_count || 0} stale leases recovered.`);
      await fetchTasks(true);
    } catch (err: any) {
      alert(`Error recovering leases: ${err.message}`);
    } finally {
      setRecoveringLeases(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setCreating(true);
    try {
      await api.tasks.create({
        title: title.trim(),
        description: notes.trim() || undefined,
        task_type: taskType,
        priority,
        order_id: orderId.trim() || undefined,
        assigned_to: assignedRole,
      });
      setShowCreateModal(false);
      setTitle("");
      setOrderId("");
      setNotes("");
      await fetchTasks(true);
    } catch (err: any) {
      alert(`Error dispatching task: ${err.message || "Unknown error"}`);
    } finally {
      setCreating(false);
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
  const inProgressCount = tasks.filter((t) => t.status === "IN_PROGRESS" || t.status === "CLAIMED").length;

  const getPriorityBadge = (p: string) => {
    switch (p?.toUpperCase()) {
      case "CRITICAL":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            HIGH
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
            LOW
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "PENDING":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" /> PENDING
          </span>
        );
      case "CLAIMED":
      case "IN_PROGRESS":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1 animate-pulse">
            <Zap className="w-2.5 h-2.5" /> IN PROGRESS
          </span>
        );
      case "COMPLETED":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5" /> COMPLETED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Warehouse & Operations Task Dispatcher"
          subtitle="Real-time employee execution queue dispatching autonomous AI workflow directives"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Real-time Status Banner */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <span className="flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                </span>
              </div>
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  Live Dispatch Bus Connected
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-md border ${sseConnected ? "bg-emerald-950/60 text-emerald-400 border-emerald-800" : "bg-blue-950/60 text-blue-400 border-blue-800"}`}>
                    {sseConnected ? "⚡ SSE Real-Time Stream Active (<50ms)" : "3s Auto-Sync Active"}
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  New tasks stream automatically from AI agents into the fulfillment pipeline. Last synced:{" "}
                  {lastUpdated.toLocaleTimeString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRecoverStale}
                disabled={recoveringLeases}
                className="px-3 py-2 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-xl transition flex items-center gap-1.5 border border-slate-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${recoveringLeases ? "animate-spin" : ""}`} />
                <span>Recover Stale Leases</span>
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-blue-600/30 transition flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Dispatch Task</span>
              </button>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>Pending Queue</span>
                <Clock className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-1">{pendingCount}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Awaiting associate pick & pack</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>In Flight</span>
                <Zap className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-indigo-400 mt-1">{inProgressCount}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Currently leased by operators</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>Completed Tasks</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{completedCount}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Verified fulfillments today</div>
            </div>
          </div>

          {/* Tab Selection & Filter */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setActiveTab("pending")}
                className={`pb-2 text-sm font-semibold border-b-2 transition ${
                  activeTab === "pending"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Pending & In-Progress ({pendingCount})
              </button>
              <button
                onClick={() => setActiveTab("completed")}
                className={`pb-2 text-sm font-semibold border-b-2 transition ${
                  activeTab === "completed"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Completed Archive ({completedCount})
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Filter Type:</span>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="ALL">All Task Types</option>
                <option value="PICK_AND_PACK">Pick & Pack</option>
                <option value="INVENTORY_COUNT">Inventory Count</option>
                <option value="RETURN_INSPECTION">Return Inspection</option>
                <option value="CRITICAL">Critical Priority</option>
                <option value="HIGH">High Priority</option>
              </select>
            </div>
          </div>

          {/* Tasks List */}
          <div className="space-y-3">
            {filteredTasks.map((t) => (
              <div
                key={t.id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono text-xs text-indigo-400 font-bold">#{t.id.slice(0, 8)}</span>
                    <h3 className="text-sm font-semibold text-white truncate">{t.title}</h3>
                    {getStatusBadge(t.status)}
                    {getPriorityBadge(t.priority)}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-slate-500" />
                      Type: <strong className="text-slate-300">{t.task_type}</strong>
                    </span>
                    {t.claimed_by && (
                      <span className="flex items-center gap-1 text-indigo-300">
                        <UserCheck className="w-3.5 h-3.5" />
                        Claimed by: {t.claimed_by}
                      </span>
                    )}
                    {t.payload?.order_id && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <Package className="w-3.5 h-3.5 text-slate-500" />
                        Order: #{t.payload.order_id}
                      </span>
                    )}
                    <span className="text-slate-400">
                      Created: {new Date(t.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  {t.payload?.notes && (
                    <p className="text-xs text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60 mt-1">
                      {t.payload.notes}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 justify-end">
                  {t.status === "PENDING" && (
                    <button
                      onClick={() => handleClaim(t.id)}
                      disabled={actionLoading === t.id}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center gap-1"
                    >
                      <Play className="w-3 h-3" />
                      <span>{actionLoading === t.id ? "Claiming..." : "Claim Task"}</span>
                    </button>
                  )}

                  {(t.status === "CLAIMED" || t.status === "IN_PROGRESS") && (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => {
                          setScanningTask(t);
                          setScannerOpen(true);
                        }}
                        className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 rounded-lg text-xs font-semibold shadow-sm transition flex items-center gap-1"
                        title="Scan Garment Barcode before Packing"
                      >
                        <Scan className="w-3 h-3" />
                        <span>Scan Barcode</span>
                      </button>
                      <button
                        onClick={() => handleComplete(t.id)}
                        disabled={actionLoading === t.id}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center gap-1"
                      >
                        <CheckSquare className="w-3 h-3" />
                        <span>{actionLoading === t.id ? "Completing..." : "Complete Task"}</span>
                      </button>
                    </div>
                  )}

                  {t.status === "COMPLETED" && (
                    <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium bg-emerald-950/40 px-3 py-1 rounded-lg border border-emerald-900/50">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Fulfilled
                    </span>
                  )}
                </div>
              </div>
            ))}

            {filteredTasks.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
                <ClipboardList className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No tasks in this view</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Queue is clear or no tasks match your current filter criteria.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Dispatch Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center">
                  <Send className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Dispatch Operational Task</h3>
                  <p className="text-[11px] text-slate-400">Add a high-priority directive into the warehouse dispatch queue</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Task Title / Action Item
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Express Pick & Pack: Order #ORD-8821"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Task Category</label>
                  <select
                    value={taskType}
                    onChange={(e) => setTaskType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="PICK_AND_PACK">Pick & Pack</option>
                    <option value="INVENTORY_COUNT">Inventory Count</option>
                    <option value="RETURN_INSPECTION">Return Inspection</option>
                    <option value="RESTOCK_VERIFICATION">Restock Verification</option>
                    <option value="CARRIER_HANDOFF">Carrier Handoff</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Priority Level</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="CRITICAL">Critical (Immediate)</option>
                    <option value="HIGH">High (SLA &lt; 30m)</option>
                    <option value="MEDIUM">Medium (Normal)</option>
                    <option value="LOW">Low (Standard batch)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Assigned Role</label>
                  <select
                    value={assignedRole}
                    onChange={(e) => setAssignedRole(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="WAREHOUSE_OPERATOR">Warehouse Operator</option>
                    <option value="LOGISTICS_LEAD">Logistics Lead</option>
                    <option value="QUALITY_INSPECTOR">Quality Inspector</option>
                    <option value="SUPERVISOR">Operations Supervisor</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Related Order ID (Optional)</label>
                  <input
                    type="text"
                    value={orderId}
                    onChange={(e) => setOrderId(e.target.value)}
                    placeholder="e.g. ORD-9932"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Operational Instructions & Notes</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Specific aisle, box sizing, packaging fragile tags..."
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-600/30 transition disabled:opacity-50 flex items-center gap-2"
                >
                  {creating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  <span>{creating ? "Dispatching..." : "Dispatch Task"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Barcode Scanner Modal */}
      <BarcodeScannerModal
        isOpen={scannerOpen}
        onClose={() => {
          setScannerOpen(false);
          setScanningTask(null);
        }}
        expectedSku={scanningTask?.payload?.sku || "UT-JAC-DEN-01"}
        expectedTitle={scanningTask?.title || "Classic Denim Jacket"}
        onVerified={async () => {
          if (scanningTask) {
            await handleComplete(scanningTask.id);
          }
        }}
      />
    </div>
  );
}
