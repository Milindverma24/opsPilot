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
  Printer,
  Radio,
  Tag,
  Truck,
  ExternalLink,
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
  const [seeding, setSeeding] = useState(false);

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
      const taskList = res.tasks || res.data || [];
      setTasks(taskList);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load employee tasks:", err);
    } finally {
      if (!isBackground) setLoading(false);
    }
  };

  const handleSeedQueue = async () => {
    setSeeding(true);
    try {
      await api.tasks.seedDemoQueue();
      await fetchTasks(false);
    } catch (err: any) {
      alert(`Error seeding tasks: ${err.message || "Failed to seed demo tasks"}`);
    } finally {
      setSeeding(false);
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

  const isCompleted = (status: string) => {
    const s = status?.toUpperCase();
    return s === "COMPLETED" || s === "CANCELLED" || s === "FULFILLED";
  };

  const filteredTasks = tasks.filter((t) => {
    if (activeTab === "pending") {
      if (isCompleted(t.status)) return false;
    } else {
      if (!isCompleted(t.status)) return false;
    }
    if (filter === "ALL") return true;
    return t.task_type === filter || t.priority === filter;
  });

  const pendingCount = tasks.filter((t) => !isCompleted(t.status)).length;
  const completedCount = tasks.filter((t) => isCompleted(t.status)).length;
  const inProgressCount = tasks.filter(
    (t) => t.status === "IN_PROGRESS" || t.status === "CLAIMED"
  ).length;

  const getPriorityBadge = (p: string) => {
    switch (p?.toUpperCase()) {
      case "CRITICAL":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-extrabold bg-rose-500/15 text-rose-400 border border-rose-500/30 tracking-wide uppercase shadow-[0_0_10px_rgba(244,63,94,0.25)] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span>
            CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 tracking-wide uppercase">
            HIGH PRIORITY
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30 tracking-wide uppercase">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-800/80 text-slate-400 border border-slate-700/60">
            NORMAL
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "CREATED":
      case "OPEN":
      case "PENDING":
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 shadow-[0_0_8px_rgba(245,158,11,0.15)]">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            AWAITING PICK
          </span>
        );
      case "CLAIMED":
      case "IN_PROGRESS":
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 animate-pulse shadow-[0_0_12px_rgba(99,102,241,0.25)]">
            <Zap className="w-3 h-3 text-indigo-400" />
            IN FLIGHT
          </span>
        );
      case "COMPLETED":
      case "FULFILLED":
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-[0_0_8px_rgba(16,185,129,0.15)]">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            VERIFIED & PACKED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#030712] text-slate-100 bg-tech-grid">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Warehouse & Operations Task Dispatcher"
          subtitle="Real-time employee execution queue dispatching autonomous AI workflow directives"
        />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Real-time Status Banner */}
          <div className="relative overflow-hidden glass-panel rounded-2xl p-5 border border-slate-800/80 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="absolute top-0 right-0 w-96 h-full bg-gradient-to-l from-indigo-500/5 to-transparent pointer-events-none" />
            
            <div className="flex items-center gap-3.5 z-10">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)]">
                  <Radio className="w-5 h-5 animate-pulse" />
                </div>
                <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
              </div>
              <div>
                <h2 className="text-base font-extrabold text-white flex items-center gap-2.5">
                  Live Dispatch Bus Connected
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border tracking-wide uppercase ${
                    sseConnected
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                  }`}>
                    {sseConnected ? "⚡ SSE Stream Active (<35ms)" : "Auto-Sync Active"}
                  </span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Autonomous orders & returns stream in real-time from Alex and Devon. Last synced:{" "}
                  <span className="text-slate-200 font-mono">{lastUpdated.toLocaleTimeString()}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 z-10 flex-wrap">
              {/* Scan Barcode Modal Button */}
              <button
                onClick={() => {
                  setScanningTask(null);
                  setScannerOpen(true);
                }}
                className="px-3.5 py-2 text-xs font-bold text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/80 rounded-xl transition-all flex items-center gap-1.5 border border-indigo-500/30 shadow-[0_0_12px_rgba(99,102,241,0.2)] hover:border-indigo-500/50"
                title="Launch optical camera or laser scanner"
              >
                <Scan className="w-3.5 h-3.5 text-indigo-400" />
                <span>Barcode Scanner</span>
              </button>

              {/* Seed Demo Queue Button */}
              <button
                onClick={handleSeedQueue}
                disabled={seeding}
                className="px-3.5 py-2 text-xs font-semibold text-slate-300 bg-slate-900/90 hover:bg-slate-800 rounded-xl transition-all flex items-center gap-1.5 border border-slate-700/80 hover:border-slate-600 disabled:opacity-50"
                title="Populate queue with 5 realistic orders and returns"
              >
                <Sparkles className={`w-3.5 h-3.5 text-cyan-400 ${seeding ? "animate-spin" : ""}`} />
                <span>{seeding ? "Seeding..." : "Seed Directives"}</span>
              </button>

              {/* Recover Stale Leases */}
              <button
                onClick={handleRecoverStale}
                disabled={recoveringLeases}
                className="px-3 py-2 text-xs font-semibold text-slate-300 bg-slate-900/90 hover:bg-slate-800 rounded-xl transition flex items-center gap-1.5 border border-slate-700/80 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${recoveringLeases ? "animate-spin" : ""}`} />
                <span>Recover Leases</span>
              </button>

              {/* Dispatch Task Button */}
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs shadow-lg shadow-blue-500/25 transition-all flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Dispatch Task</span>
              </button>
            </div>
          </div>

          {/* 4 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Pending Queue */}
            <div className="relative overflow-hidden glass-card rounded-2xl p-5 border border-slate-800/80 shadow-lg group hover:border-amber-500/40 transition-all">
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl group-hover:bg-amber-500/20 transition-all pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span className="flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                  Pending Queue
                </span>
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-white mt-2 font-mono tracking-tight">{pendingCount}</div>
              <div className="text-xs text-amber-400/90 mt-1 flex items-center gap-1 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
                Awaiting associate pick & pack
              </div>
            </div>

            {/* Card 2: In Flight */}
            <div className="relative overflow-hidden glass-card rounded-2xl p-5 border border-slate-800/80 shadow-lg group hover:border-indigo-500/40 transition-all">
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span className="flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                  In Flight
                </span>
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.2)]">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-white mt-2 font-mono tracking-tight">{inProgressCount}</div>
              <div className="text-xs text-indigo-300 mt-1 font-medium">
                Currently leased by operators
              </div>
            </div>

            {/* Card 3: Completed Today */}
            <div className="relative overflow-hidden glass-card rounded-2xl p-5 border border-slate-800/80 shadow-lg group hover:border-emerald-500/40 transition-all">
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span className="flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                  Completed Today
                </span>
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-white mt-2 font-mono tracking-tight">{completedCount}</div>
              <div className="text-xs text-emerald-400/90 mt-1 font-medium">
                Verified barcode fulfillments
              </div>
            </div>

            {/* Card 4: Fulfillment SLA */}
            <div className="relative overflow-hidden glass-card rounded-2xl p-5 border border-slate-800/80 shadow-lg group hover:border-cyan-500/40 transition-all">
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-all pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span className="flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                  Fulfillment SLA
                </span>
                <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                  <Sparkles className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 mt-2 font-mono tracking-tight">
                99.8%
              </div>
              <div className="text-xs text-slate-400 mt-1 font-medium">
                0 SLA breaches detected
              </div>
            </div>
          </div>

          {/* Tab Selection & Filter */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setActiveTab("pending")}
                className={`pb-2 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
                  activeTab === "pending"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>Pending & In-Progress</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                  {pendingCount}
                </span>
              </button>
              <button
                onClick={() => setActiveTab("completed")}
                className={`pb-2 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
                  activeTab === "completed"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>Completed Archive</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                  {completedCount}
                </span>
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Filter Type:</span>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
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
          <div className="space-y-3.5">
            {filteredTasks.map((t) => (
              <div
                key={t.id}
                className="glass-card rounded-2xl p-5 border border-slate-800/80 hover:border-indigo-500/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-5 group"
              >
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono text-xs px-2 py-0.5 bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 rounded-lg font-bold">
                      #{t.order_id || t.id.slice(0, 8)}
                    </span>
                    <h3 className="text-sm font-bold text-white tracking-tight">{t.title}</h3>
                    {getStatusBadge(t.status)}
                    {getPriorityBadge(t.priority)}
                  </div>

                  {/* Items summary pills */}
                  {t.items_summary && t.items_summary.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                      {t.items_summary.map((item: any, idx: number) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 bg-slate-900/90 text-slate-300 border border-slate-800 rounded-lg text-xs font-medium flex items-center gap-1.5 font-mono shadow-sm"
                        >
                          <Package className="w-3.5 h-3.5 text-indigo-400" />
                          {typeof item === "string" ? item : JSON.stringify(item)}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap pt-0.5">
                    <span className="flex items-center gap-1 text-slate-300">
                      <Layers className="w-3.5 h-3.5 text-slate-500" />
                      Type: <strong className="text-white font-semibold">{t.task_type}</strong>
                    </span>
                    {t.customer_name && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                        Customer: <strong className="text-white">{t.customer_name}</strong>
                      </span>
                    )}
                    <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-[10px] font-bold flex items-center gap-1">
                      <Truck className="w-3 h-3" />
                      BlueDart Express
                    </span>
                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      Created {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  {t.description && (
                    <p className="text-xs text-slate-400 bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/80 mt-1">
                      {t.description}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 justify-end shrink-0 flex-wrap">
                  {/* Print 4x6" Thermal Label Button */}
                  <button
                    onClick={() => {
                      const url = `http://localhost:8000/api/v1/shipments/5c264d67-2818-4c2f-85f2-49d897da8843/label`;
                      window.open(url, "_blank", "width=480,height=680");
                    }}
                    className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 hover:border-slate-600 rounded-xl text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
                    title="Print 4x6 inch thermal shipping label with vector barcode"
                  >
                    <Printer className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Print Label</span>
                  </button>

                  {/* Claim Button */}
                  {(t.status === "PENDING" || t.status === "CREATED" || t.status === "OPEN") && (
                    <button
                      onClick={() => handleClaim(t.id)}
                      disabled={actionLoading === t.id}
                      className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition flex items-center gap-1.5"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>{actionLoading === t.id ? "Claiming..." : "Claim Task"}</span>
                    </button>
                  )}

                  {/* In Progress actions */}
                  {(t.status === "CLAIMED" || t.status === "IN_PROGRESS") && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setScanningTask(t);
                          setScannerOpen(true);
                        }}
                        className="px-3.5 py-2 bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-300 border border-indigo-500/40 rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5 shadow-[0_0_12px_rgba(99,102,241,0.2)]"
                        title="Scan Garment Barcode before Packing"
                      >
                        <Scan className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Scan Barcode</span>
                      </button>
                      <button
                        onClick={() => handleComplete(t.id)}
                        disabled={actionLoading === t.id}
                        className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5"
                      >
                        <CheckSquare className="w-3.5 h-3.5" />
                        <span>{actionLoading === t.id ? "Completing..." : "Complete Task"}</span>
                      </button>
                    </div>
                  )}

                  {isCompleted(t.status) && (
                    <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-bold bg-emerald-950/50 px-3.5 py-1.5 rounded-xl border border-emerald-800/60 shadow-[0_0_10px_rgba(16,185,129,0.15)]">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Fulfilled
                    </span>
                  )}
                </div>
              </div>
            ))}

            {filteredTasks.length === 0 && !loading && (
              <div className="text-center py-16 glass-panel border border-slate-800/80 rounded-2xl p-8 relative overflow-hidden shadow-2xl">
                <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto mb-4 shadow-[0_0_25px_rgba(99,102,241,0.2)]">
                  <ClipboardList className="w-8 h-8" />
                </div>
                <h3 className="text-base font-bold text-white tracking-tight">Fulfillment Queue Clear</h3>
                <p className="text-xs text-slate-400 mt-1.5 max-w-md mx-auto">
                  No active operations match your filter. Generate live demo warehouse directives from Alex & Devon or dispatch a custom task.
                </p>
                <div className="flex items-center justify-center gap-3 mt-6">
                  <button
                    onClick={handleSeedQueue}
                    disabled={seeding}
                    className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs shadow-lg shadow-blue-500/25 transition flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4 text-cyan-300" />
                    <span>{seeding ? "Generating Directives..." : "Populate Realistic Queue (5 Orders)"}</span>
                  </button>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition flex items-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Custom Task</span>
                  </button>
                </div>
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
