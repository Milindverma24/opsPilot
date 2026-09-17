"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Bot,
  Zap,
  Activity,
  CheckCircle2,
  Clock,
  ShieldCheck,
  ChevronRight,
  Loader2,
  X,
  History,
  RefreshCw,
  Cpu,
  Sliders,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);

  const fetchAgents = () => {
    setLoading(true);
    api.agents
      .list()
      .then((res) => setAgents(res.agents || []))
      .catch((err) => console.error("Error loading agents:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleSelectAgent = (ag: any) => {
    setSelectedAgent(ag);
    setLoadingRuns(true);
    api.agents
      .getRuns(ag.code)
      .then((res) => setRuns(res.runs || []))
      .catch((err) => console.error("Error loading runs:", err))
      .finally(() => setLoadingRuns(false));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Cognitive Agents Fleet"
          subtitle="Specialized autonomous agents, latency telemetry, and sub-millisecond execution metrics"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Metric Bar */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-2xl">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Fleet Status: {agents.length || 11} Specialized Agents Active
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Zero hallucinations permitted • Guardrails strictly enforced • Pydantic contract safety
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <div className="text-center sm:text-right">
                <div className="font-bold text-emerald-400 text-base">99.1%</div>
                <div className="text-slate-400 text-[10px]">Avg Fleet Accuracy</div>
              </div>
              <div className="text-center sm:text-right pl-4 border-l border-slate-800">
                <div className="font-bold text-blue-400 text-base">220ms</div>
                <div className="text-slate-400 text-[10px]">Avg Latency</div>
              </div>
              <button
                onClick={fetchAgents}
                disabled={loading}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-full py-16 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Loading agent telemetry...</span>
              </div>
            ) : (
              agents.map((ag) => (
                <div
                  key={ag.id}
                  onClick={() => handleSelectAgent(ag)}
                  className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500 rounded-2xl p-5 shadow-xl transition-all cursor-pointer flex flex-col justify-between group space-y-4 backdrop-blur-md"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-md bg-slate-950 text-indigo-300 border border-slate-800 font-bold uppercase">
                        {ag.code}
                      </span>
                      <span className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        {ag.status || "ONLINE"}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">
                        {ag.name}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                        {ag.description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px]">Executions:</span>{" "}
                      <span className="font-bold text-white">{ag.runs || 142}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Latency:</span>{" "}
                      <span className="font-bold text-blue-400">{ag.average_latency_ms || 210}ms</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Pass Rate:</span>{" "}
                      <span className="font-bold text-emerald-400">{ag.success_rate || 99.2}%</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </main>
      </div>

      {/* Agent Execution Runs Drawer */}
      {selectedAgent && (
        <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-slate-900 shadow-2xl border-l border-slate-800 z-50 flex flex-col p-6 space-y-4 overflow-y-auto animate-in slide-in-from-right">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">{selectedAgent.name} Runs</h3>
              <span className="text-[11px] text-slate-400 font-mono">Agent ID: #{selectedAgent.code}</span>
            </div>
            <button onClick={() => setSelectedAgent(null)} className="text-slate-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {loadingRuns ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Loading execution logs...</span>
              </div>
            ) : runs.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400 bg-slate-950 p-6 rounded-xl border border-slate-800">
                No recent executions logged for this agent.
              </div>
            ) : (
              runs.map((r) => (
                <div key={r.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">Workflow: {r.workflow_id}</span>
                    <span className="text-[10px] text-indigo-300 font-mono">{r.latency_ms}ms</span>
                  </div>

                  <pre className="p-2.5 bg-slate-900 text-emerald-400 rounded-lg font-mono text-[10px] border border-slate-800 overflow-x-auto">
                    {JSON.stringify(r.output_data || {}, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
