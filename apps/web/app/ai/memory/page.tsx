"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Brain,
  User,
  Cpu,
  Trash2,
  RefreshCw,
  Plus,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Filter,
  Search,
  Layers,
  Database,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function MemoryPage() {
  const [activeTab, setActiveTab] = useState<"customer" | "agent">("customer");
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [customerIdSearch, setCustomerIdSearch] = useState("");

  // Add memory modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [target, setTarget] = useState("CUSTOMER");
  const [targetCustomerId, setTargetCustomerId] = useState("cust-001");
  const [agentId, setAgentId] = useState("aria-support-ai");
  const [memoryType, setMemoryType] = useState("PREFERENCE");
  const [memoryKey, setMemoryKey] = useState("");
  const [memoryValue, setMemoryValue] = useState("");
  const [ttlDays, setTtlDays] = useState(90);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const res = await api.memory.list({
        target: activeTab === "customer" ? "CUSTOMER" : "AGENT",
        customer_id: activeTab === "customer" && customerIdSearch ? customerIdSearch : undefined,
      });
      setMemories(res?.data || []);
    } catch (err) {
      console.error("Failed to load memories:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [activeTab]);

  const handleDelete = async (id: string) => {
    try {
      await api.memory.delete(id);
      await fetchMemories();
    } catch (err) {
      console.error("Failed to delete memory:", err);
    }
  };

  const handleAddMemory = async () => {
    if (!memoryKey.trim() || !memoryValue.trim()) return;
    try {
      let parsedValue: any = memoryValue;
      try {
        parsedValue = JSON.parse(memoryValue);
      } catch {
        parsedValue = memoryValue;
      }

      await api.memory.store({
        target,
        customer_id: target === "CUSTOMER" ? targetCustomerId : undefined,
        agent_id: target === "AGENT" ? agentId : undefined,
        memory_type: memoryType,
        key: memoryKey,
        value: parsedValue,
        ttl_days: ttlDays,
      });
      setShowAddModal(false);
      setMemoryKey("");
      setMemoryValue("");
      await fetchMemories();
    } catch (err) {
      console.error("Failed to store memory:", err);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 antialiased overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                  <Brain className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">AI Memory Store</h1>
                  <p className="text-xs text-slate-400">
                    Multi-layer persistent context: Customer preferences, agent operational evidence, and conflict detection
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchMemories}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                title="Refresh"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-900/30"
              >
                <Plus className="w-4 h-4" />
                <span>Store Memory Entry</span>
              </button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab("customer")}
              className={cn(
                "px-5 py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition",
                activeTab === "customer"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              )}
            >
              <User className="w-4 h-4" />
              <span>Customer Personalization Memory</span>
            </button>

            <button
              onClick={() => setActiveTab("agent")}
              className={cn(
                "px-5 py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition",
                activeTab === "agent"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              )}
            >
              <Cpu className="w-4 h-4" />
              <span>Agent Operational Knowledge</span>
            </button>
          </div>

          {/* Customer Search Bar if in customer tab */}
          {activeTab === "customer" && (
            <div className="flex items-center gap-3">
              <div className="relative flex-1 max-w-sm">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={customerIdSearch}
                  onChange={(e) => setCustomerIdSearch(e.target.value)}
                  placeholder="Filter by Customer ID (e.g. cust-001)..."
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                />
              </div>
              <button
                onClick={fetchMemories}
                className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
              >
                Apply
              </button>
            </div>
          )}

          {/* Memory Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {memories.map((mem) => (
              <div
                key={mem.id}
                className={cn(
                  "p-4 rounded-xl border bg-slate-900/50 flex flex-col justify-between gap-3 transition",
                  mem.is_conflicted
                    ? "border-amber-500/40 bg-amber-950/10"
                    : "border-slate-800 hover:border-slate-700"
                )}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 uppercase">
                      {mem.memory_type}
                    </span>
                    {mem.is_conflicted && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        Conflicted
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-white mt-2 font-mono">{mem.key}</h3>

                  <div className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 break-all max-h-32 overflow-y-auto">
                    {typeof mem.value === "object" ? JSON.stringify(mem.value, null, 2) : String(mem.value)}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                  <div className="space-y-0.5">
                    {mem.customer_id && <div>Customer: <span className="text-slate-300">{mem.customer_id}</span></div>}
                    {mem.evidence_count !== undefined && <div>Evidence: <span className="text-slate-300 font-bold">{mem.evidence_count}x</span> observations</div>}
                    {mem.expires_at && <div>TTL: <span className="text-slate-400">{new Date(mem.expires_at).toLocaleDateString()}</span></div>}
                  </div>

                  <button
                    onClick={() => handleDelete(mem.id)}
                    className="p-1.5 rounded-md hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition"
                    title="Forget / Delete Memory"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}

            {memories.length === 0 && !loading && (
              <div className="col-span-full p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 space-y-2">
                <Brain className="w-8 h-8 text-slate-500 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-300">No memories recorded yet</h4>
                <p className="text-xs text-slate-500">
                  Customer memories are dynamically extracted during chat sessions or can be stored manually.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-purple-400" />
              <span>Store Persistent Memory</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Target Layer</label>
                  <select
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="CUSTOMER">Customer Memory</option>
                    <option value="AGENT">Agent Operational Memory</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Memory Type</label>
                  <select
                    value={memoryType}
                    onChange={(e) => setMemoryType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="PREFERENCE">PREFERENCE</option>
                    <option value="SIZE_PROFILE">SIZE_PROFILE</option>
                    <option value="FABRIC_ALLERGY">FABRIC_ALLERGY</option>
                    <option value="COMMON_INQUIRY">COMMON_INQUIRY</option>
                    <option value="TOOL_HINT">TOOL_HINT</option>
                  </select>
                </div>
              </div>

              {target === "CUSTOMER" ? (
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Customer ID</label>
                  <input
                    type="text"
                    value={targetCustomerId}
                    onChange={(e) => setTargetCustomerId(e.target.value)}
                    placeholder="cust-001"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                  />
                </div>
              ) : (
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Agent ID</label>
                  <input
                    type="text"
                    value={agentId}
                    onChange={(e) => setAgentId(e.target.value)}
                    placeholder="aria-support-ai"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                  />
                </div>
              )}

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Memory Key</label>
                <input
                  type="text"
                  value={memoryKey}
                  onChange={(e) => setMemoryKey(e.target.value)}
                  placeholder="e.g. preferred_fabric or sizing_shirt"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Memory Value (String or JSON)</label>
                <textarea
                  rows={3}
                  value={memoryValue}
                  onChange={(e) => setMemoryValue(e.target.value)}
                  placeholder="e.g. Cotton and Linen only, no synthetic blends"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">TTL Expiration (Days)</label>
                <input
                  type="number"
                  value={ttlDays}
                  onChange={(e) => setTtlDays(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleAddMemory}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
              >
                Store Memory
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
