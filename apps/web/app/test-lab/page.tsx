"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  FlaskConical,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";

export default function TestLabPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [results, setResults] = useState<Record<string, any>>({});
  const [runningAll, setRunningAll] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [filter, setFilter] = useState("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api.testLab
      .getScenarios()
      .then((res) => setScenarios(res.scenarios || []))
      .catch((err) => console.error("Error loading scenarios:", err));
  }, []);

  const handleRunSingle = async (scId: string) => {
    setRunningId(scId);
    try {
      const res = await api.testLab.run(scId);
      if (res.results && res.results.length > 0) {
        setResults((prev) => ({ ...prev, [scId]: res.results[0] }));
      }
    } catch (err: any) {
      console.error(`Error running ${scId}:`, err);
    } finally {
      setRunningId(null);
    }
  };

  const handleRunAll = async () => {
    setRunningAll(true);
    try {
      const res = await api.testLab.run("ALL");
      if (res.results) {
        const resultMap: Record<string, any> = {};
        res.results.forEach((r: any) => {
          resultMap[r.test_id] = r;
        });
        setResults(resultMap);
      }
    } catch (err: any) {
      console.error("Error running all test scenarios:", err);
    } finally {
      setRunningAll(false);
    }
  };

  const filteredScenarios = scenarios.filter((s) => {
    if (filter === "ALL") return true;
    return s.category === filter;
  });

  const passedCount = Object.values(results).filter((r) => r.passed).length;
  const totalRan = Object.keys(results).length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Autonomous Operations Test Lab"
          subtitle="One-click simulation environment for enterprise operations, risk, and security scenarios"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Banner */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="p-2 bg-emerald-100 text-emerald-800 rounded-lg">
                  <FlaskConical className="w-5 h-5" />
                </span>
                <h2 className="text-lg font-bold text-slate-900">
                  Interactive Evaluation & Simulation Suite
                </h2>
              </div>
              <p className="text-xs text-slate-500 max-w-2xl">
                Simulate business operations, test idempotency, observe prompt injection defenses, inspect policy triggers, and verify mock payments in a zero-risk sandbox.
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              {totalRan > 0 && (
                <div className="px-3 py-1.5 bg-slate-100 rounded-lg text-xs font-semibold text-slate-700">
                  Passed: <span className="text-emerald-600 font-bold">{passedCount}</span> / {totalRan}
                </div>
              )}
              <button
                onClick={handleRunAll}
                disabled={runningAll}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex items-center gap-2"
              >
                {runningAll ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 fill-white" />
                )}
                <span>Run All 14 Scenarios</span>
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            {["ALL", "INVOICE", "COMPLAINT", "SECURITY", "POLICY_APPROVAL", "ERROR_HANDLING"].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                  filter === cat
                    ? "bg-slate-900 text-white shadow-sm"
                    : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                }`}
              >
                {cat.replace("_", " ")}
              </button>
            ))}
          </div>

          {/* Scenarios Table */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 w-28">Scenario</th>
                    <th className="py-3 px-4">Description & Input</th>
                    <th className="py-3 px-4 w-40">Expected Outcome</th>
                    <th className="py-3 px-4 w-48">Actual AI Result</th>
                    <th className="py-3 px-4 w-28 text-center">Status</th>
                    <th className="py-3 px-4 w-24 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredScenarios.map((sc) => {
                    const res = results[sc.id];
                    const isRunning = runningId === sc.id || runningAll;
                    const isExpanded = expandedId === sc.id;

                    return (
                      <tr key={sc.id} className="hover:bg-slate-50/70 transition-colors">
                        {/* ID & Category */}
                        <td className="py-3 px-4 font-mono align-top">
                          <span className="font-bold text-slate-900">{sc.id}</span>
                          <div className="text-[10px] text-slate-400 mt-0.5">{sc.category}</div>
                        </td>

                        {/* Name & Input Summary */}
                        <td className="py-3 px-4 align-top max-w-sm">
                          <div className="font-bold text-slate-900 text-xs">{sc.name}</div>
                          <div className="text-slate-500 text-[11px] mt-0.5">{sc.description}</div>
                          <div className="text-slate-400 font-mono text-[10px] bg-slate-50 p-1.5 rounded mt-1.5 border border-slate-100">
                            {sc.input_summary}
                          </div>
                        </td>

                        {/* Expected Output */}
                        <td className="py-3 px-4 align-top text-[11px] text-slate-600 font-medium">
                          {sc.expected_output}
                        </td>

                        {/* Actual Output */}
                        <td className="py-3 px-4 align-top text-[11px]">
                          {res ? (
                            <div className="space-y-1">
                              <span className="font-semibold text-slate-800">
                                {res.actual_output}
                              </span>
                              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                                <span>Time: {res.execution_time_ms}ms</span>
                                <span>•</span>
                                <span className={res.risk_level === "CRITICAL" ? "text-rose-600 font-bold" : ""}>
                                  Risk: {res.risk_level}
                                </span>
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">Not yet executed</span>
                          )}
                        </td>

                        {/* Pass/Fail Status */}
                        <td className="py-3 px-4 align-top text-center">
                          {isRunning ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600">
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Running</span>
                            </span>
                          ) : res ? (
                            res.passed ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span>PASS</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-bold">
                                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                                <span>FAIL</span>
                              </span>
                            )
                          ) : (
                            <span className="text-slate-400 text-[11px] font-medium">-</span>
                          )}
                        </td>

                        {/* Action Button */}
                        <td className="py-3 px-4 align-top text-right">
                          <button
                            onClick={() => handleRunSingle(sc.id)}
                            disabled={isRunning}
                            className="px-2.5 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-600 border border-slate-200 rounded-lg text-slate-700 font-semibold text-[11px] transition-colors disabled:opacity-50"
                          >
                            Run
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
