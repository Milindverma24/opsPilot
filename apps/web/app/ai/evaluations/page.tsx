"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  CheckCircle2,
  XCircle,
  Play,
  Filter,
  RefreshCw,
  Plus,
  GitBranch,
  Gauge,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Cpu,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function EvaluationsPage() {
  const [evals, setEvals] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);

  // New Experiment Modal
  const [showExpModal, setShowExpModal] = useState(false);
  const [expName, setExpName] = useState("");
  const [expAgentId, setExpAgentId] = useState("aria-support-ai");
  const [baselineVersion, setBaselineVersion] = useState("v1.0");
  const [candidateVersion, setCandidateVersion] = useState("v1.1");
  const [trafficSplit, setTrafficSplit] = useState(10);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [evRes, expRes] = await Promise.all([
        api.evaluations.list(),
        api.experiments.list(),
      ]);
      setEvals(evRes?.data || []);
      setExperiments(expRes?.data || []);
    } catch (err) {
      console.error("Failed to load evaluation data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunEvaluation = async () => {
    setRunningEval(true);
    try {
      await api.evaluations.run({
        agent_id: "aria-support-ai",
        version_id: "v1.1",
        dataset_version: "v1.0",
      });
      await fetchData();
    } catch (err) {
      console.error("Evaluation execution failed:", err);
    } finally {
      setRunningEval(false);
    }
  };

  const handleCreateExperiment = async () => {
    if (!expName.trim()) return;
    try {
      await api.experiments.create({
        name: expName,
        agent_id: expAgentId,
        baseline_version: baselineVersion,
        candidate_version: candidateVersion,
        traffic_percentage: trafficSplit,
      });
      setShowExpModal(false);
      setExpName("");
      await fetchData();
    } catch (err) {
      console.error("Failed to create experiment:", err);
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
                  <Gauge className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">Regression Evals & A/B Testing</h1>
                  <p className="text-xs text-slate-400">
                    Automated regression benchmark quality gates & live canary traffic experiments
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchData}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                title="Refresh"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <button
                onClick={() => setShowExpModal(true)}
                className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-2 transition"
              >
                <GitBranch className="w-4 h-4 text-purple-400" />
                <span>New A/B Experiment</span>
              </button>

              <button
                onClick={handleRunEvaluation}
                disabled={runningEval}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold text-xs transition shadow-lg shadow-purple-900/30"
              >
                {runningEval ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                <span>{runningEval ? "Running Benchmark..." : "Run Evaluation Suite"}</span>
              </button>
            </div>
          </div>

          {/* Quality Thresholds Card */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Enforced Quality Gate Thresholds</span>
              </h3>
              <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
                Zero Degradation Policy
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Policy Compliance</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-xl font-black text-emerald-400">≥ 99.0%</span>
                  <span className="text-[10px] text-slate-500">(Hard Block)</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Cannot deploy if below threshold</p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Intent Classification</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-xl font-black text-blue-400">≥ 95.0%</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Multi-class customer intent</p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Tool Selection Accuracy</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-xl font-black text-purple-400">≥ 95.0%</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Strict business tool invocation</p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">RAG Groundedness</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-xl font-black text-amber-400">≥ 95.0%</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Faithfulness to company store docs</p>
              </div>
            </div>
          </div>

          {/* Active A/B Experiments */}
          {experiments.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-purple-400" />
                <span>Active A/B Experiments ({experiments.length})</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {experiments.map((exp) => (
                  <div key={exp.id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-slate-200">{exp.name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        {exp.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
                      <div>Baseline: <span className="text-slate-200">{exp.baseline_version}</span> ({100 - exp.traffic_percentage}%)</div>
                      <div>Candidate: <span className="text-purple-300 font-bold">{exp.candidate_version}</span> ({exp.traffic_percentage}%)</div>
                    </div>

                    {/* Visual split bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full flex overflow-hidden">
                      <div className="bg-blue-600 h-full" style={{ width: `${100 - exp.traffic_percentage}%` }}></div>
                      <div className="bg-purple-500 h-full" style={{ width: `${exp.traffic_percentage}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evaluation Runs History */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Evaluation Suite Run History</h3>
                <p className="text-xs text-slate-400">Automated benchmark runs against curated golden datasets</p>
              </div>
              <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded">
                Golden Dataset v1.0
              </span>
            </div>

            <div className="divide-y divide-slate-800">
              {evals.map((ev) => (
                <div key={ev.id} className="p-4 hover:bg-slate-800/40 transition space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {ev.passed ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-200">
                            Version {ev.version_id || "v1.1"} Benchmark
                          </span>
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded text-[10px] font-bold border",
                              ev.passed
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            )}
                          >
                            {ev.passed ? "PASSED" : "FAILED QUALITY GATE"}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500 font-mono">Agent: {ev.agent_id} • Run ID: {ev.id}</span>
                      </div>
                    </div>

                    <span className="text-xs text-slate-500">
                      {ev.created_at ? new Date(ev.created_at).toLocaleString() : ""}
                    </span>
                  </div>

                  {/* Metrics Bar */}
                  {ev.metrics && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs font-mono">
                      <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 block">Policy Compliance:</span>
                        <span className="font-bold text-emerald-400">
                          {((ev.metrics.policy_compliance || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 block">Intent Accuracy:</span>
                        <span className="font-bold text-blue-400">
                          {((ev.metrics.intent_accuracy || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 block">Tool Selection:</span>
                        <span className="font-bold text-purple-400">
                          {((ev.metrics.tool_selection_accuracy || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] text-slate-400 block">RAG Groundedness:</span>
                        <span className="font-bold text-amber-400">
                          {((ev.metrics.rag_groundedness || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Failure Reasons Callout */}
                  {ev.failure_reasons && ev.failure_reasons.length > 0 && (
                    <div className="p-2.5 rounded bg-rose-950/20 border border-rose-500/30 text-rose-300 text-xs font-mono space-y-1">
                      <span className="font-bold flex items-center gap-1.5 text-rose-400">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Gate Failure Reasons:
                      </span>
                      {ev.failure_reasons.map((r: string, idx: number) => (
                        <div key={idx} className="pl-4">• {r}</div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {evals.length === 0 && !loading && (
                <div className="p-8 text-center text-slate-500 text-xs">
                  No evaluation runs recorded. Click "Run Evaluation Suite" above to benchmark.
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* New Experiment Modal */}
      {showExpModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-purple-400" />
              <span>Create A/B Traffic Experiment</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 font-semibold block mb-1">Experiment Name</label>
                <input
                  type="text"
                  value={expName}
                  onChange={(e) => setExpName(e.target.value)}
                  placeholder="e.g. Sizing Assistant Few-Shot v1.2 vs v1.0"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Baseline Version</label>
                  <input
                    type="text"
                    value={baselineVersion}
                    onChange={(e) => setBaselineVersion(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Candidate Version</label>
                  <input
                    type="text"
                    value={candidateVersion}
                    onChange={(e) => setCandidateVersion(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-semibold">Candidate Traffic Split: {trafficSplit}%</label>
                  <span className="text-slate-500 font-mono">Baseline: {100 - trafficSplit}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={trafficSplit}
                  onChange={(e) => setTrafficSplit(Number(e.target.value))}
                  className="w-full accent-purple-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                onClick={() => setShowExpModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateExperiment}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
              >
                Launch Experiment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
