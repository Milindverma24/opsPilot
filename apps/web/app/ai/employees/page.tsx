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
  Plus,
  X,
  Server,
  Terminal,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function AIEmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"ALL" | "HEALTHY" | "DEGRADED" | "CRITICAL">("ALL");

  // Deploy Modal
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("Customer Experience Specialist");
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("gpt-4o-mini");
  const [permissions, setPermissions] = useState<string[]>([
    "orders.read",
    "support.read",
    "knowledge.read",
  ]);

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
        current_task: "Realtime diagnostic ping verification test",
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

  const handleDeployEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setDeploying(true);
    try {
      await api.aiEmployees.create({
        name: name.trim(),
        role: role.trim(),
        description: description.trim() || `Autonomous AI agent handling ${role}`,
        llm_model: model,
        permissions,
      });
      setShowDeployModal(false);
      setName("");
      setDescription("");
      await fetchEmployees();
    } catch (err: any) {
      alert("Deployment failed: " + (err.message || "Unknown error"));
    } finally {
      setDeploying(false);
    }
  };

  const filteredEmployees = employees.filter((emp) => {
    if (filter === "ALL") return true;
    return emp.health?.toUpperCase() === filter;
  });

  const getHealthBadge = (health: string) => {
    switch (health?.toUpperCase()) {
      case "HEALTHY":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm shadow-emerald-500/10">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> HEALTHY
          </span>
        );
      case "DEGRADED":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 animate-pulse shadow-sm shadow-amber-500/10">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span> DEGRADED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1.5 shadow-sm shadow-rose-500/10">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span> CRITICAL
          </span>
        );
    }
  };

  const healthyCount = employees.filter((e) => e.health === "HEALTHY").length;
  const degradedCount = employees.filter((e) => e.health === "DEGRADED").length;
  const criticalCount = employees.filter((e) => e.health === "CRITICAL").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="AI Workforce Directory"
          subtitle="Autonomous digital workforce nodes powering UrbanThread e-commerce operations"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Banner & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Fleet Nodes</span>
                <Cpu className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">{employees.length}</div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {healthyCount} online & operational
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Degraded Nodes</span>
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-2">{degradedCount}</div>
              <div className="text-[11px] text-slate-400 mt-1">Requiring supervisor inspection</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Total Tasks Handled</span>
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">
                {employees.reduce((sum, e) => sum + (e.completed_tasks || 0), 0)}
              </div>
              <div className="text-[11px] text-blue-400 mt-1">Autonomous executions</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Surveillance Status</span>
                <Shield className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-2">Active</div>
              <div className="text-[11px] text-slate-400 mt-1">Heartbeat guardrails online</div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => setFilter("ALL")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  filter === "ALL"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-800/70 text-slate-400 hover:text-white"
                }`}
              >
                All Fleet ({employees.length})
              </button>
              <button
                onClick={() => setFilter("HEALTHY")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  filter === "HEALTHY"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "bg-slate-800/70 text-slate-400 hover:text-white"
                }`}
              >
                Healthy ({healthyCount})
              </button>
              <button
                onClick={() => setFilter("DEGRADED")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  filter === "DEGRADED"
                    ? "bg-amber-600 text-white shadow-md shadow-amber-600/30"
                    : "bg-slate-800/70 text-slate-400 hover:text-white"
                }`}
              >
                Degraded ({degradedCount})
              </button>
              {criticalCount > 0 && (
                <button
                  onClick={() => setFilter("CRITICAL")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    filter === "CRITICAL"
                      ? "bg-rose-600 text-white shadow-md shadow-rose-600/30"
                      : "bg-slate-800/70 text-slate-400 hover:text-white"
                  }`}
                >
                  Critical ({criticalCount})
                </button>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchEmployees}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh Telemetry</span>
              </button>
              <button
                onClick={() => setShowDeployModal(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-indigo-600/30 transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Deploy AI Employee</span>
              </button>
            </div>
          </div>

          {/* AI Workforce Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredEmployees.map((emp) => (
              <div
                key={emp.id}
                className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 flex flex-col justify-between space-y-4 hover:border-slate-700 hover:shadow-xl hover:shadow-indigo-950/30 transition-all relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-all pointer-events-none" />

                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-black text-base shadow-lg shadow-indigo-500/20">
                        {emp.name[0]}
                      </div>
                      <div>
                        <h2 className="font-bold text-white text-base">{emp.name}</h2>
                        <span className="text-[11px] font-mono text-slate-400">ID: #{emp.id}</span>
                      </div>
                    </div>
                    {getHealthBadge(emp.health)}
                  </div>

                  <div className="inline-block px-2.5 py-0.5 rounded-lg bg-indigo-950/60 text-indigo-300 text-xs font-semibold border border-indigo-800/50">
                    {emp.role}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed min-h-[36px]">
                    {emp.description}
                  </p>

                  {/* Task & Queue */}
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span className="flex items-center gap-1">
                        <Terminal className="w-3 h-3 text-indigo-400" /> Current Operation:
                      </span>
                      <span className="font-mono text-indigo-300 font-bold">
                        Queue: {emp.queue_size || 0}
                      </span>
                    </div>
                    <div className="text-slate-200 font-medium truncate" title={emp.current_task}>
                      {emp.current_task || "Idle — Ready for assignment"}
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-2 pt-1 text-center">
                    <div className="p-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl">
                      <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Success Rate</div>
                      <div className="text-sm font-bold text-emerald-400 mt-0.5">
                        {emp.success_rate ? `${emp.success_rate}%` : "99.2%"}
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl">
                      <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Completed</div>
                      <div className="text-sm font-bold text-slate-100 mt-0.5">
                        {emp.completed_tasks || 0} tasks
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleHeartbeat(emp.id)}
                      disabled={actingId === emp.id}
                      className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1.5 border border-slate-700"
                    >
                      <Activity className={`w-3 h-3 text-indigo-400 ${actingId === emp.id ? "animate-spin" : ""}`} />
                      <span>Ping</span>
                    </button>

                    {emp.health !== "HEALTHY" && (
                      <button
                        onClick={() => handleRecover(emp.id)}
                        disabled={actingId === emp.id}
                        className="px-2.5 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1.5"
                      >
                        <Wrench className="w-3 h-3" />
                        <span>Recover</span>
                      </button>
                    )}
                  </div>

                  <Link
                    href={`/ai/employees/${emp.id}`}
                    className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    <span>Inspect Profile</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {filteredEmployees.length === 0 && !loading && (
            <div className="text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
              <Bot className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No AI employees matching filter</h3>
              <p className="text-xs text-slate-400 mt-1">Try switching filter tabs or deploy a new node into the fleet.</p>
            </div>
          )}
        </main>
      </div>

      {/* Deploy AI Employee Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Deploy Autonomous AI Employee</h3>
                  <p className="text-[11px] text-slate-400">Initialize a new cognitive agent node with scoped tool access</p>
                </div>
              </div>
              <button
                onClick={() => setShowDeployModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleDeployEmployee} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Employee Codename / Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Orion, Nova, Chronos"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Role / Function</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Customer Experience Specialist">Customer Experience</option>
                    <option value="Inventory Logistics Director">Inventory Logistics</option>
                    <option value="Risk & Security Gatekeeper">Risk & Security</option>
                    <option value="Fulfillment Orchestrator">Fulfillment Orchestrator</option>
                    <option value="Returns & Refunds Manager">Returns & Refunds</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Foundation Model</label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="gpt-4o-mini">gpt-4o-mini (Fast & Efficient)</option>
                    <option value="gpt-4o">gpt-4o (High Reasoning)</option>
                    <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                    <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Mission Directive & Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the operational goals, safety boundary rules, and target SLA..."
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">RBAC Permissions & Tool Scopes</label>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {["orders.read", "orders.write", "support.read", "inventory.write", "coupons.read", "knowledge.read"].map((perm) => (
                    <label key={perm} className="flex items-center gap-2 p-2 bg-slate-950/70 border border-slate-800 rounded-lg cursor-pointer hover:border-slate-700">
                      <input
                        type="checkbox"
                        checked={permissions.includes(perm)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPermissions([...permissions, perm]);
                          } else {
                            setPermissions(permissions.filter((p) => p !== perm));
                          }
                        }}
                        className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                      />
                      <span className="font-mono text-[11px] text-slate-300">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowDeployModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deploying}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition disabled:opacity-50 flex items-center gap-2"
                >
                  {deploying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>{deploying ? "Deploying Node..." : "Confirm & Deploy"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
