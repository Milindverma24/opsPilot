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
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);

  useEffect(() => {
    api.agents
      .list()
      .then((res) => setAgents(res.agents || []))
      .catch((err) => console.error("Error loading agents:", err))
      .finally(() => setLoading(false));
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
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="AI Agent Fleet"
          subtitle="Specialized autonomous agents, latency telemetry, and execution metrics"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Metric Bar */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Fleet Status: 11 Agents Operational
                </h3>
                <p className="text-xs text-slate-500">
                  Zero hallucinations permitted • Guardrails strictly enforced • Pydantic contracts
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <div className="text-center sm:text-right">
                <div className="font-bold text-slate-900">98.4%</div>
                <div className="text-slate-400 text-[10px]">Avg Fleet Accuracy</div>
              </div>
              <div className="text-center sm:text-right">
                <div className="font-bold text-slate-900">220ms</div>
                <div className="text-slate-400 text-[10px]">Avg Agent Latency</div>
              </div>
            </div>
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-full py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Loading agent telemetry...</span>
              </div>
            ) : (
              agents.map((ag) => (
                <div
                  key={ag.id}
                  onClick={() => handleSelectAgent(ag)}
                  className="bg-white border border-slate-200 hover:border-blue-500 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold uppercase">
                        {ag.code}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-emerald-600 font-bold">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        {ag.status}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                        {ag.name}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {ag.description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px]">Runs:</span>{" "}
                      <span className="font-bold text-slate-800">{ag.runs}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Latency:</span>{" "}
                      <span className="font-bold text-slate-800">{ag.average_latency_ms}ms</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Success:</span>{" "}
                      <span className="font-bold text-emerald-600">{ag.success_rate}%</span>
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
        <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col p-6 space-y-4 overflow-y-auto">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <h3 className="text-sm font-bold text-slate-900">{selectedAgent.name} Runs</h3>
              <span className="text-[11px] text-slate-500 font-mono">Agent ID: {selectedAgent.code}</span>
            </div>
            <button onClick={() => setSelectedAgent(null)} className="text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {loadingRuns ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Loading execution logs...</span>
              </div>
            ) : runs.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No recent executions logged for this agent.
              </div>
            ) : (
              runs.map((r) => (
                <div key={r.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">Workflow: {r.workflow_id}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{r.latency_ms}ms</span>
                  </div>

                  <pre className="p-2 bg-slate-900 text-emerald-400 rounded font-mono text-[10px] overflow-x-auto">
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
