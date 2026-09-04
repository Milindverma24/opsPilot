"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  ThumbsUp,
  Star,
  MessageSquare,
  Filter,
  Plus,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  User,
  Cpu,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function FeedbackPage() {
  const [feedbackList, setFeedbackList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [agentFilter, setAgentFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  // Submit feedback modal
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [agentId, setAgentId] = useState("aria-support-ai");
  const [feedbackType, setFeedbackType] = useState("POLICY_VIOLATION");
  const [rating, setRating] = useState(2);
  const [correction, setCorrection] = useState("");
  const [comment, setComment] = useState("");
  const [expectedBehavior, setExpectedBehavior] = useState("");
  const [actualBehavior, setActualBehavior] = useState("");

  const fetchFeedback = async () => {
    setLoading(true);
    try {
      const res = await api.feedback.list({
        agent_id: agentFilter || undefined,
        feedback_type: typeFilter || undefined,
      });
      setFeedbackList(res?.data || []);
    } catch (err) {
      console.error("Failed to load feedback:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeedback();
  }, [agentFilter, typeFilter]);

  const handleSubmitFeedback = async () => {
    try {
      await api.feedback.submitAgent({
        agent_id: agentId,
        feedback_type: feedbackType,
        rating,
        correction: correction || undefined,
        comment: comment || undefined,
        expected_behavior: expectedBehavior || undefined,
        actual_behavior: actualBehavior || undefined,
      });
      setShowSubmitModal(false);
      setCorrection("");
      setComment("");
      setExpectedBehavior("");
      setActualBehavior("");
      await fetchFeedback();
    } catch (err) {
      console.error("Failed to submit feedback:", err);
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
                  <ThumbsUp className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">AI Feedback & Human Corrections</h1>
                  <p className="text-xs text-slate-400">
                    Operator reviews, turn-by-turn customer ratings, and auto-learning example generation
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchFeedback}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                title="Refresh"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <button
                onClick={() => setShowSubmitModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-900/30"
              >
                <Plus className="w-4 h-4" />
                <span>Submit Operator Review</span>
              </button>
            </div>
          </div>

          {/* Feedback Type Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {["", "POLICY_VIOLATION", "INCORRECT_TOOL", "TONE_ISSUE", "EXCELLENT_DECISION"].map((ft) => (
              <button
                key={ft}
                onClick={() => setTypeFilter(ft)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 border",
                  typeFilter === ft
                    ? "bg-purple-600 border-purple-500 text-white shadow-sm"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
                )}
              >
                {ft || "All Reviews"}
              </button>
            ))}
          </div>

          {/* Feedback Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {feedbackList.map((fb) => (
              <div
                key={fb.id}
                className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[10px] font-bold border uppercase",
                        fb.feedback_type === "POLICY_VIOLATION"
                          ? "bg-rose-500/10 text-rose-300 border-rose-500/20"
                          : fb.feedback_type === "EXCELLENT_DECISION"
                          ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-300 border-amber-500/20"
                      )}
                    >
                      {fb.feedback_type}
                    </span>
                    <span className="text-xs font-mono text-slate-400">Agent: {fb.agent_id}</span>
                  </div>

                  <div className="flex items-center gap-1 text-amber-400">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <Star
                        key={s}
                        className={cn("w-3.5 h-3.5", s <= fb.rating ? "fill-amber-400" : "text-slate-700")}
                      />
                    ))}
                  </div>
                </div>

                {fb.comment && <p className="text-xs text-slate-300 italic">"{fb.comment}"</p>}

                {(fb.actual_behavior || fb.expected_behavior) && (
                  <div className="space-y-1.5 text-xs font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                    {fb.actual_behavior && (
                      <div className="text-rose-300">
                        <span className="text-slate-500">Actual: </span>
                        {fb.actual_behavior}
                      </div>
                    )}
                    {fb.expected_behavior && (
                      <div className="text-emerald-300">
                        <span className="text-slate-500">Expected: </span>
                        {fb.expected_behavior}
                      </div>
                    )}
                  </div>
                )}

                {fb.correction && (
                  <div className="p-2 rounded bg-purple-950/30 border border-purple-500/30 text-xs text-purple-200 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    <span><strong>Correction:</strong> {fb.correction}</span>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Reviewer: {fb.reviewer_user_id || "Customer"}</span>
                  <span>{fb.created_at ? new Date(fb.created_at).toLocaleDateString() : ""}</span>
                </div>
              </div>
            ))}

            {feedbackList.length === 0 && !loading && (
              <div className="col-span-full p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 space-y-2">
                <ThumbsUp className="w-8 h-8 text-slate-500 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-300">No feedback entries recorded</h4>
                <p className="text-xs text-slate-500">
                  Staff can review AI decisions and submit corrections to train future agent iterations.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Submit Feedback Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-purple-400" />
              <span>Submit Staff Review on AI</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Agent</label>
                  <select
                    value={agentId}
                    onChange={(e) => setAgentId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="aria-support-ai">Aria (Support AI)</option>
                    <option value="inventory-ai">Atlas (Inventory)</option>
                    <option value="orders-ai">Orion (Orders)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Feedback Type</label>
                  <select
                    value={feedbackType}
                    onChange={(e) => setFeedbackType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="POLICY_VIOLATION">POLICY_VIOLATION</option>
                    <option value="INCORRECT_TOOL">INCORRECT_TOOL</option>
                    <option value="TONE_ISSUE">TONE_ISSUE</option>
                    <option value="EXCELLENT_DECISION">EXCELLENT_DECISION</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Score Rating: {rating} / 5</label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setRating(s)}
                      className={cn(
                        "p-2 rounded-lg border text-xs font-bold transition",
                        s === rating ? "bg-amber-500/20 text-amber-300 border-amber-500" : "bg-slate-950 border-slate-800 text-slate-400"
                      )}
                    >
                      {s} ★
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Actual Agent Behavior</label>
                <input
                  type="text"
                  value={actualBehavior}
                  onChange={(e) => setActualBehavior(e.target.value)}
                  placeholder="e.g. AI stated return window was 14 days"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Expected Correct Behavior</label>
                <input
                  type="text"
                  value={expectedBehavior}
                  onChange={(e) => setExpectedBehavior(e.target.value)}
                  placeholder="e.g. Inform customer returns are accepted within 30 days"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Learning Correction (Golden Pattern)</label>
                <textarea
                  rows={2}
                  value={correction}
                  onChange={(e) => setCorrection(e.target.value)}
                  placeholder="Explains the rule: Returns are 30 days from delivery date for clothing items."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                onClick={() => setShowSubmitModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitFeedback}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
              >
                Save Review
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
