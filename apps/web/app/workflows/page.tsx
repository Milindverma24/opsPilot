"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  GitBranch,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Play,
  ArrowRight,
  Eye,
  Loader2,
  X,
  Bot,
  ShieldCheck,
  Zap,
  Pause,
  RotateCcw,
  Sliders,
  Sparkles,
  Terminal,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function WorkflowsPage() {
  const [activeTab, setActiveTab] = useState<"definitions" | "runs">("definitions");
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loadingWfs, setLoadingWfs] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [selectedStep, setSelectedStep] = useState<any>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Test modal
  const [testModalWf, setTestModalWf] = useState<any>(null);
  const [testMode, setTestMode] = useState<string>("LIVE_MOCK");
  const [testPayload, setTestPayload] = useState<string>("{}");
  const [testResult, setTestResult] = useState<any>(null);
  const [testRunning, setTestRunning] = useState<boolean>(false);

  const loadWorkflows = () => {
    setLoadingWfs(true);
    api.workflows
      .list()
      .then((data) => setWorkflows(data.workflows || data || []))
      .catch((err) => console.error("Error loading workflows:", err))
      .finally(() => setLoadingWfs(false));
  };

  const loadRuns = () => {
    setLoadingRuns(true);
    api.workflowRuns
      .list()
      .then((data) => setRuns(data.runs || data || []))
      .catch((err) => console.error("Error loading runs:", err))
      .finally(() => setLoadingRuns(false));
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  useEffect(() => {
    if (activeTab === "runs") {
      loadRuns();
    }
  }, [activeTab]);

  const handleToggleEnabled = async (wf: any) => {
    try {
      const updated = await api.workflows.toggleEnabled(wf.id, !wf.enabled);
      setWorkflows(workflows.map((w) => (w.id === wf.id ? { ...w, enabled: updated.enabled } : w)));
    } catch (err: any) {
      alert("Failed to toggle workflow: " + err.message);
    }
  };

  const openTestModal = (wf: any) => {
    setTestModalWf(wf);
    setTestResult(null);
    if (wf.workflow_type === "ORDER_FULFILLMENT") {
      setTestPayload(JSON.stringify({ order_id: "ord-test-01", sku: "UT-SHIRT-001", total_amount: 2499.0 }, null, 2));
    } else if (wf.workflow_type === "SHIPMENT_DELAY_RESOLUTION") {
      setTestPayload(JSON.stringify({ order_id: "ord-test-01", delay_days: 3 }, null, 2));
    } else if (wf.workflow_type === "INVENTORY_REPLENISHMENT") {
      setTestPayload(JSON.stringify({ sku: "UT-SHIRT-001", quantity_available: 4, amount: 25000.0 }, null, 2));
    } else if (wf.workflow_type === "RETURN_PROCESSING") {
      setTestPayload(JSON.stringify({ order_id: "ord-test-01", return_reason: "SIZE_TOO_SMALL", amount: 2499.0 }, null, 2));
    } else {
      setTestPayload(JSON.stringify({ amount: 1000.0 }, null, 2));
    }
  };

  const handleRunTest = async () => {
    if (!testModalWf) return;
    setTestRunning(true);
    setTestResult(null);
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(testPayload);
      } catch {}
      const res = await api.workflows.test(testModalWf.id, {
        test_mode: testMode,
        input_data: parsed,
      });
      setTestResult(res);
      if (activeTab === "runs") loadRuns();
    } catch (err: any) {
      alert("Test failed: " + err.message);
    } finally {
      setTestRunning(false);
    }
  };

  const handlePauseRun = async (runId: string) => {
    setActionLoadingId(runId);
    try {
      await api.workflowRuns.pause(runId);
      loadRuns();
    } catch (err: any) {
      alert("Pause failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleResumeRun = async (runId: string) => {
    setActionLoadingId(runId);
    try {
      await api.workflowRuns.resume(runId);
      loadRuns();
    } catch (err: any) {
      alert("Resume failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRetryRun = async (runId: string) => {
    setActionLoadingId(runId);
    try {
      await api.workflowRuns.retry(runId);
      loadRuns();
    } catch (err: any) {
      alert("Retry failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSelectRun = async (runId: string) => {
    try {
      const data = await api.workflowRuns.get(runId);
      setSelectedRun(data.run || data);
      if (data.run?.step_runs && data.run.step_runs.length > 0) {
        setSelectedStep(data.run.step_runs[0]);
      }
    } catch (err: any) {
      alert("Failed to load run details: " + err.message);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case "COMPLETED":
        return "bg-emerald-950/60 text-emerald-400 border-emerald-800";
      case "RUNNING":
        return "bg-indigo-950/60 text-indigo-400 border-indigo-800 animate-pulse";
      case "WAITING_FOR_APPROVAL":
        return "bg-amber-950/60 text-amber-400 border-amber-800";
      case "WAITING":
        return "bg-indigo-950/60 text-indigo-400 border-indigo-800";
      case "RETRYING":
        return "bg-purple-950/60 text-purple-400 border-purple-800";
      case "FAILED":
        return "bg-rose-950/60 text-rose-400 border-rose-800";
      case "PAUSED":
        return "bg-slate-900 text-slate-400 border-slate-700";
      default:
        return "bg-slate-900 text-slate-400 border-slate-800";
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Autonomous Business Workflow Engine"
          subtitle="Durable multi-step orchestration, deterministic branching, and safe controlled business execution"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Tab Navigation */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("definitions")}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === "definitions"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                <GitBranch className="w-4 h-4" />
                <span>Autonomous Workflows ({workflows.length})</span>
              </button>

              <button
                onClick={() => setActiveTab("runs")}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === "runs"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                <Clock className="w-4 h-4" />
                <span>Execution Runs & History</span>
              </button>
            </div>

            <button
              onClick={() => (activeTab === "definitions" ? loadWorkflows() : loadRuns())}
              className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 rounded-xl transition"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* TAB 1: WORKFLOW DEFINITIONS */}
          {activeTab === "definitions" && (
            <div className="space-y-4">
              {loadingWfs ? (
                <div className="py-16 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  <span>Loading workflow registry...</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {workflows.map((wf) => (
                    <div
                      key={wf.id}
                      className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg hover:border-slate-700 transition space-y-4 flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-bold text-sm text-white">{wf.name}</h3>
                              <span className="px-2 py-0.5 rounded-md bg-slate-950 text-indigo-300 border border-slate-800 font-mono text-[10px]">
                                {wf.version || "v1"}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 line-clamp-2">{wf.description}</p>
                          </div>

                          {/* Enable / Disable Switch */}
                          <button
                            onClick={() => handleToggleEnabled(wf)}
                            className={`px-2.5 py-1 rounded-full text-[10px] font-bold border transition-colors ${
                              wf.enabled
                                ? "bg-emerald-950/60 text-emerald-400 border-emerald-800 hover:bg-emerald-900/60"
                                : "bg-slate-950 text-slate-500 border-slate-800 hover:bg-slate-900"
                            }`}
                          >
                            {wf.enabled ? "ACTIVE" : "DISABLED"}
                          </button>
                        </div>

                        {/* Metadata Pills */}
                        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-400">
                          <span className="bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                            Trigger: <strong className="text-indigo-400">{wf.trigger_type}</strong>
                          </span>
                          <span className="bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                            Concurrency: {wf.max_concurrent_runs || 20} max
                          </span>
                          <span className="bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                            Timeout: {wf.timeout_seconds || 1800}s
                          </span>
                        </div>

                        {/* Step count & types preview */}
                        {wf.steps && (
                          <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                            <span className="text-[11px] font-semibold text-slate-400">Steps Architecture:</span>
                            <div className="flex flex-wrap items-center gap-1.5">
                              {wf.steps.map((st: any) => (
                                <span
                                  key={st.id || st.step_order}
                                  className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-950 text-slate-300 border border-slate-800"
                                >
                                  {st.step_order}. {st.step_type}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Action Bar */}
                      <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800/80">
                        <button
                          onClick={() => openTestModal(wf)}
                          className="px-3.5 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md shadow-indigo-600/30 transition-all"
                        >
                          <Play className="w-3.5 h-3.5 fill-white" />
                          <span>Simulate / Test Run</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: EXECUTION RUNS */}
          {activeTab === "runs" && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl overflow-hidden backdrop-blur-md">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3.5 px-4 pl-5">Run ID & Workflow</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4">Current Step</th>
                      <th className="py-3.5 px-4">Started At</th>
                      <th className="py-3.5 px-4 text-right pr-5">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {loadingRuns ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-400">
                          <Loader2 className="w-4 h-4 animate-spin mx-auto text-indigo-400" />
                          <span className="mt-1 inline-block">Loading execution runs...</span>
                        </td>
                      </tr>
                    ) : runs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-400">
                          No execution runs recorded yet. Trigger a workflow test or wait for business events.
                        </td>
                      </tr>
                    ) : (
                      runs.map((r) => {
                        const isLoading = actionLoadingId === r.id;

                        return (
                          <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                            <td className="py-3.5 px-4 pl-5">
                              <div className="font-bold text-white">
                                {r.workflow?.name || r.workflow?.workflow_type || "Autonomous Run"}
                              </div>
                              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                                #{r.id.slice(0, 8)} • Event: {r.trigger_event_type || "EVENT"}
                              </div>
                            </td>

                            <td className="py-3.5 px-4">
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(r.status)}`}>
                                {r.status}
                              </span>
                            </td>

                            <td className="py-3.5 px-4 font-mono text-slate-300">
                              Step #{r.current_step_order || 1}
                            </td>

                            <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                              {formatDate(r.started_at || r.created_at)}
                            </td>

                            <td className="py-3.5 px-4 text-right pr-5">
                              <div className="flex items-center justify-end gap-1.5">
                                {r.status === "RUNNING" && (
                                  <button
                                    onClick={() => handlePauseRun(r.id)}
                                    disabled={isLoading}
                                    className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-800 rounded-lg transition"
                                    title="Pause Run"
                                  >
                                    <Pause className="w-3.5 h-3.5" />
                                  </button>
                                )}

                                {r.status === "PAUSED" && (
                                  <button
                                    onClick={() => handleResumeRun(r.id)}
                                    disabled={isLoading}
                                    className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-slate-800 rounded-lg transition"
                                    title="Resume Run"
                                  >
                                    <Play className="w-3.5 h-3.5" />
                                  </button>
                                )}

                                {["FAILED", "RETRYING"].includes(r.status) && (
                                  <button
                                    onClick={() => handleRetryRun(r.id)}
                                    disabled={isLoading}
                                    className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-slate-800 rounded-lg transition"
                                    title="Retry Run"
                                  >
                                    <RotateCcw className="w-3.5 h-3.5" />
                                  </button>
                                )}

                                <button
                                  onClick={() => handleSelectRun(r.id)}
                                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg font-semibold text-[11px] inline-flex items-center gap-1 transition"
                                >
                                  <Eye className="w-3 h-3 text-indigo-400" />
                                  <span>Inspect</span>
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Visual Workflow Run Drawer */}
      {selectedRun && (
        <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-slate-900 shadow-2xl border-l border-slate-800 z-50 flex flex-col p-6 space-y-4 overflow-y-auto animate-in slide-in-from-right">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">
                  {selectedRun.workflow?.name || "Workflow Execution Run"}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(selectedRun.status)}`}>
                  {selectedRun.status}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">Run ID: {selectedRun.id}</div>
            </div>
            <button
              onClick={() => setSelectedRun(null)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Visual Step Timeline */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-400 text-xs uppercase tracking-wider">Step Timeline</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {selectedRun.step_runs?.map((st: any) => {
                const isSelected = selectedStep?.id === st.id;
                return (
                  <button
                    key={st.id}
                    onClick={() => setSelectedStep(st)}
                    className={`p-2.5 rounded-xl text-left border transition-all ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30"
                        : "bg-slate-950 hover:bg-slate-800 text-slate-300 border-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[11px] truncate">{st.workflow_step?.step_type || "STEP"}</span>
                      {st.status === "SUCCEEDED" ? (
                        <CheckCircle2 className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-white" : "text-emerald-400"}`} />
                      ) : st.status === "FAILED" ? (
                        <XCircle className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-white" : "text-rose-400"}`} />
                      ) : (
                        <Clock className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-white" : "text-amber-400"}`} />
                      )}
                    </div>
                    <div className={`text-[9px] mt-0.5 font-mono ${isSelected ? "text-indigo-200" : "text-slate-500"}`}>
                      #{st.attempt_number || 1} • {st.status}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Step Detail Inspector */}
          {selectedStep && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 flex-1 overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-white">
                  Step Detail: {selectedStep.workflow_step?.name || selectedStep.workflow_step?.step_type}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Status: {selectedStep.status} • Duration: {selectedStep.duration_ms || 0}ms
                </span>
              </div>

              {selectedStep.error_message && (
                <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-rose-300 text-xs">
                  <strong>Error ({selectedStep.error_code}):</strong> {selectedStep.error_message}
                </div>
              )}

              <div className="space-y-1 text-xs">
                <span className="font-semibold text-slate-400">Output Data:</span>
                <pre className="p-3 bg-slate-900 text-emerald-400 rounded-xl font-mono text-[11px] border border-slate-800 overflow-x-auto">
                  {JSON.stringify(selectedStep.output_data || {}, null, 2)}
                </pre>
              </div>

              {selectedStep.input_data && (
                <div className="space-y-1 text-xs pt-2">
                  <span className="font-semibold text-slate-400">Input Context:</span>
                  <pre className="p-3 bg-slate-900 border border-slate-800 text-indigo-300 rounded-xl font-mono text-[11px] overflow-x-auto">
                    {JSON.stringify(selectedStep.input_data || {}, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Test / Simulate Modal */}
      {testModalWf && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Play className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm text-white">
                  Simulate Workflow: {testModalWf.name}
                </h3>
              </div>
              <button onClick={() => setTestModalWf(null)} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-slate-300">Execution Mode</label>
                <div className="grid grid-cols-3 gap-2">
                  {["PLAN_ONLY", "DRY_RUN", "LIVE_MOCK"].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setTestMode(mode)}
                      className={`py-1.5 rounded-xl border text-center font-bold text-[11px] transition-all ${
                        testMode === mode
                          ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30"
                          : "bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800"
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-slate-300">Test Input Payload (JSON)</label>
                <textarea
                  value={testPayload}
                  onChange={(e) => setTestPayload(e.target.value)}
                  rows={5}
                  className="w-full p-3 font-mono text-[11px] text-indigo-300 bg-slate-950 border border-slate-800 rounded-xl focus:border-indigo-500 outline-none resize-none"
                />
              </div>

              {testResult && (
                <div className="space-y-1 pt-2 border-t border-slate-800">
                  <span className="font-bold text-emerald-400">Execution Result:</span>
                  <pre className="p-3 bg-slate-950 text-emerald-400 border border-slate-800 rounded-xl font-mono text-[11px] max-h-40 overflow-y-auto">
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setTestModalWf(null)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white rounded-xl"
              >
                Close
              </button>
              <button
                onClick={handleRunTest}
                disabled={testRunning}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 flex items-center gap-1.5"
              >
                {testRunning && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Execute Test</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
