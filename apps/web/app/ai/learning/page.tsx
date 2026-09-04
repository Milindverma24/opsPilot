"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Database,
  Download,
  Filter,
  Plus,
  RefreshCw,
  CheckCircle2,
  FileSpreadsheet,
  Tag,
  Star,
  FileCode,
  ArrowDownToLine,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function LearningPage() {
  const [examples, setExamples] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  // Add example modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [category, setCategory] = useState("POLICY_COMPLIANCE");
  const [input, setInput] = useState("");
  const [expectedOutput, setExpectedOutput] = useState("");
  const [correction, setCorrection] = useState("");

  const fetchExamples = async () => {
    setLoading(true);
    try {
      const res = await api.learning.examples({
        category: categoryFilter || undefined,
        approved: true,
      });
      setExamples(res?.data || []);
    } catch (err) {
      console.error("Failed to load learning examples:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExamples();
  }, [categoryFilter]);

  const handleCreateExample = async () => {
    if (!input.trim() || !expectedOutput.trim()) return;
    try {
      await api.learning.createExample({
        category,
        input,
        expected_output: expectedOutput,
        correction: correction || undefined,
        source_type: "MANUAL_EXAMPLE",
        dataset_version: "v1.0",
      });
      setShowAddModal(false);
      setInput("");
      setExpectedOutput("");
      setCorrection("");
      await fetchExamples();
    } catch (err) {
      console.error("Failed to add learning example:", err);
    }
  };

  const handleDownloadJsonl = () => {
    const url = api.learning.exportJsonlUrl(categoryFilter || undefined);
    window.open(url, "_blank");
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
                  <Database className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">Curated Learning Dataset</h1>
                  <p className="text-xs text-slate-400">
                    High-quality fine-tuning examples, human corrections, and JSONL dataset export
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchExamples}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                title="Refresh"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <button
                onClick={handleDownloadJsonl}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-xs transition"
              >
                <ArrowDownToLine className="w-4 h-4 text-emerald-400" />
                <span>Export JSONL Dataset</span>
              </button>

              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-900/30"
              >
                <Plus className="w-4 h-4" />
                <span>Add Golden Example</span>
              </button>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {["", "POLICY_COMPLIANCE", "INTENT_CLASSIFICATION", "TOOL_SELECTION", "SIZING_ASSISTANCE"].map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 border",
                  categoryFilter === cat
                    ? "bg-purple-600 border-purple-500 text-white shadow-sm"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
                )}
              >
                {cat || "All Categories"}
              </button>
            ))}
          </div>

          {/* Learning Examples Table / Grid */}
          <div className="space-y-3">
            {examples.map((ex) => (
              <div
                key={ex.id}
                className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      {ex.category}
                    </span>
                    <span className="text-xs font-mono text-slate-500">Source: {ex.source_type}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Approved
                    </span>
                    <span className="text-xs font-mono text-slate-500">Dataset: {ex.dataset_version}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                      Shopper Input
                    </span>
                    <p className="text-slate-200 font-mono text-xs">{ex.input}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block">
                      Target Golden Response / Correction
                    </span>
                    <p className="text-emerald-300 font-mono text-xs">{ex.expected_output || ex.correction}</p>
                  </div>
                </div>
              </div>
            ))}

            {examples.length === 0 && !loading && (
              <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 space-y-2">
                <FileSpreadsheet className="w-8 h-8 text-slate-500 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-300">No learning examples in dataset</h4>
                <p className="text-xs text-slate-500">
                  Human corrections on AI conversations are automatically converted into approved training examples.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Add Example Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-purple-400" />
              <span>Add Golden Training Example</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 font-semibold block mb-1">Learning Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="POLICY_COMPLIANCE">POLICY_COMPLIANCE</option>
                  <option value="INTENT_CLASSIFICATION">INTENT_CLASSIFICATION</option>
                  <option value="TOOL_SELECTION">TOOL_SELECTION</option>
                  <option value="SIZING_ASSISTANCE">SIZING_ASSISTANCE</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Shopper Input (Prompt)</label>
                <textarea
                  rows={2}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="e.g. Can I return my jeans after 28 days?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Expected Golden AI Response</label>
                <textarea
                  rows={3}
                  value={expectedOutput}
                  onChange={(e) => setExpectedOutput(e.target.value)}
                  placeholder="e.g. Yes, UrbanThread accepts returns within 30 days of delivery..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Correction Notes (Optional)</label>
                <input
                  type="text"
                  value={correction}
                  onChange={(e) => setCorrection(e.target.value)}
                  placeholder="Highlight key store policy or exact tool required"
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
                onClick={handleCreateExample}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
              >
                Save Example
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
