"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Rocket,
  ShieldCheck,
  Filter,
  RefreshCw,
  Plus,
  ArrowRight,
  GitBranch,
  AlertTriangle,
  History,
  FileCode,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ImprovementsPage() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [actingId, setActingId] = useState<string | null>(null);

  // New Candidate Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [agentId, setAgentId] = useState("aria-support-ai");
  const [candidateType, setCandidateType] = useState("PROMPT_IMPROVEMENT");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [proposedPrompt, setProposedPrompt] = useState("");
  const [proposedRules, setProposedRules] = useState("");
  const [expectedImpact, setExpectedImpact] = useState("");
  const [risk, setRisk] = useState("LOW");

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const res = await api.improvements.list({
        status: statusFilter || undefined,
      });
      setCandidates(res.data || []);
    } catch (err) {
      console.error("Failed to load candidates:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [statusFilter]);

  const handleApprove = async (id: string) => {
    setActingId(id);
    try {
      await api.improvements.approve(id);
      await fetchCandidates();
    } catch (err) {
      console.error("Failed to approve candidate:", err);
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setActingId(id);
    try {
      await api.improvements.reject(id);
      await fetchCandidates();
    } catch (err) {
      console.error("Failed to reject candidate:", err);
    } finally {
      setActingId(null);
    }
  };

  const handleDeploy = async (id: string) => {
    setActingId(id);
    try {
      await api.improvements.deploy(id);
      await fetchCandidates();
    } catch (err) {
      console.error("Failed to deploy candidate:", err);
    } finally {
      setActingId(null);
    }
  };

  const handleRollback = async (id: string) => {
    setActingId(id);
    try {
      await api.improvements.rollback(id);
      await fetchCandidates();
    } catch (err) {
      console.error("Failed to rollback candidate:", err);
    } finally {
      setActingId(null);
    }
  };

  const handleCreateCandidate = async () => {
    if (!title.trim() || !description.trim()) return;
    try {
      const rulesList = proposedRules
        .split("\n")
        .map((r) => r.trim())
        .filter(Boolean);
      await api.improvements.create({
        agent_id: agentId,
        candidate_type: candidateType,
        title,
        description,
        proposed_change: {
          system_prompt: proposedPrompt || undefined,
          behavior_rules: rulesList.length ? rulesList : undefined,
        },
        expected_impact: expectedImpact || undefined,
        risk,
      });
      setShowCreateModal(false);
      setTitle("");
      setDescription("");
      setProposedPrompt("");
      setProposedRules("");
      await fetchCandidates();
    } catch (err) {
      console.error("Failed to propose candidate:", err);
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
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">AI Improvement Candidates</h1>
                  <p className="text-xs text-slate-400">
                    Human-in-the-Loop review cockpit: AI proposes improvements, human operators approve & deploy
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchCandidates}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                title="Refresh"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-900/30"
              >
                <Plus className="w-4 h-4" />
                <span>Propose Candidate</span>
              </button>
            </div>
          </div>

          {/* Pipeline Banner */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between overflow-x-auto text-xs font-mono text-slate-400 gap-4">
            <span className="text-purple-400 font-bold shrink-0">Controlled Pipeline:</span>
            <div className="flex items-center gap-2 shrink-0">
              <span className="px-2 py-1 rounded bg-slate-800 text-slate-300">Experience Capture</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2 py-1 rounded bg-slate-800 text-slate-300">Feedback & Eval</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2 py-1 rounded bg-slate-800 text-slate-300">Candidate Propose</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30">
                Human Review Gate
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                Version & Deploy
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2 py-1 rounded bg-slate-800 text-slate-300">Regression Test</span>
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {["", "GENERATED", "APPROVED", "DEPLOYED", "REJECTED", "ROLLED_BACK"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 border",
                  statusFilter === st
                    ? "bg-purple-600 border-purple-500 text-white shadow-sm"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
                )}
              >
                {st || "All Candidates"}
              </button>
            ))}
          </div>

          {/* Candidates Grid */}
          <div className="grid grid-cols-1 gap-4">
            {candidates.map((cand) => {
              const isActing = actingId === cand.id;
              return (
                <div
                  key={cand.id}
                  className={cn(
                    "p-5 rounded-xl border bg-slate-900/50 space-y-4 transition",
                    cand.status === "GENERATED"
                      ? "border-amber-500/30 hover:border-amber-500/50"
                      : cand.status === "APPROVED"
                      ? "border-blue-500/30 hover:border-blue-500/50"
                      : cand.status === "DEPLOYED"
                      ? "border-emerald-500/30 hover:border-emerald-500/50"
                      : "border-slate-800 hover:border-slate-700"
                  )}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wide",
                          cand.status === "GENERATED"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : cand.status === "APPROVED"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                            : cand.status === "DEPLOYED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : cand.status === "ROLLED_BACK"
                            ? "bg-orange-500/10 text-orange-400 border-orange-500/20"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        )}
                      >
                        {cand.status}
                      </span>
                      <h3 className="text-base font-bold text-white tracking-tight">{cand.title}</h3>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                      <span>Agent: {cand.agent_id}</span>
                      <span>• Risk: <span className="font-bold text-slate-300">{cand.risk}</span></span>
                      <span>• Type: {cand.candidate_type}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{cand.description}</p>

                  {cand.expected_impact && (
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400 shrink-0" />
                      <span><strong>Expected Impact:</strong> {cand.expected_impact}</span>
                    </div>
                  )}

                  {/* Proposed Change Inspection */}
                  {cand.proposed_change && (
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>Proposed Prompt & Rule Diff</span>
                        <span>Structured JSON</span>
                      </div>
                      <pre className="text-purple-300 overflow-x-auto whitespace-pre-wrap max-h-40 text-[11px] leading-relaxed">
                        {JSON.stringify(cand.proposed_change, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Action Bar */}
                  <div className="flex flex-wrap items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
                    <span className="text-slate-500 text-[11px]">
                      Created {cand.created_at ? new Date(cand.created_at).toLocaleString() : ""}
                      {cand.reviewed_by ? ` • Reviewed by ${cand.reviewed_by}` : ""}
                    </span>

                    <div className="flex items-center gap-2">
                      {cand.status === "GENERATED" && (
                        <>
                          <button
                            onClick={() => handleReject(cand.id)}
                            disabled={isActing}
                            className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 font-semibold transition flex items-center gap-1.5"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                          <button
                            onClick={() => handleApprove(cand.id)}
                            disabled={isActing}
                            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition flex items-center gap-1.5 shadow-sm"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Approve Candidate</span>
                          </button>
                        </>
                      )}

                      {cand.status === "APPROVED" && (
                        <button
                          onClick={() => handleDeploy(cand.id)}
                          disabled={isActing}
                          className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition flex items-center gap-1.5 shadow-md shadow-emerald-900/30"
                        >
                          <Rocket className="w-3.5 h-3.5" />
                          <span>Promote to Active Production</span>
                        </button>
                      )}

                      {cand.status === "DEPLOYED" && (
                        <button
                          onClick={() => handleRollback(cand.id)}
                          disabled={isActing}
                          className="px-3 py-1.5 rounded-lg bg-orange-500/10 hover:bg-orange-500/20 text-orange-300 border border-orange-500/30 font-semibold transition flex items-center gap-1.5"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Rollback to Predecessor</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {candidates.length === 0 && !loading && (
              <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 space-y-2">
                <Sparkles className="w-8 h-8 text-slate-500 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-300">No improvement candidates found</h4>
                <p className="text-xs text-slate-500">
                  Candidates are automatically generated from human corrections or can be proposed manually.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Propose Candidate Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-purple-400" />
              <span>Propose AI Improvement Candidate</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Target Agent</label>
                  <select
                    value={agentId}
                    onChange={(e) => setAgentId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="aria-support-ai">Aria (Customer Support AI)</option>
                    <option value="inventory-ai">Atlas (Inventory AI)</option>
                    <option value="orders-ai">Orion (Order Operations AI)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-semibold block mb-1">Risk Assessment</label>
                  <select
                    value={risk}
                    onChange={(e) => setRisk(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH (Requires Senior Review)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Proposal Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Enforce 30-Day Return Delivery Date Rule"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Rationale & Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Why is this change necessary? Mention recurring confusion or customer feedback..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Updated System Prompt (Optional)</label>
                <textarea
                  rows={3}
                  value={proposedPrompt}
                  onChange={(e) => setProposedPrompt(e.target.value)}
                  placeholder="You are Aria. Always calculate the 30-day window from the order DELIVERED timestamp..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-[11px] resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Behavior Rules (One per line)</label>
                <textarea
                  rows={2}
                  value={proposedRules}
                  onChange={(e) => setProposedRules(e.target.value)}
                  placeholder="Verify delivered timestamp before rejecting returns&#10;Never process unverified cash refunds"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-[11px] resize-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Expected Business Impact</label>
                <input
                  type="text"
                  value={expectedImpact}
                  onChange={(e) => setExpectedImpact(e.target.value)}
                  placeholder="Reduces customer escalation rate by 15%"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCandidate}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
              >
                Submit Proposal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
