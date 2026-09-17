"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  CheckSquare,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  FileText,
  Loader2,
  Sparkles,
  DollarSign,
  Lock,
  MessageSquare,
  X,
  Send,
  Eye,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("PENDING");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Modals
  const [activeModal, setActiveModal] = useState<"approve" | "reject" | "payload" | "comments" | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<any>(null);
  const [commentInput, setCommentInput] = useState<string>("");
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [newCommentText, setNewCommentText] = useState<string>("");

  const loadApprovals = () => {
    setLoading(true);
    api.approvals
      .list(filter)
      .then((res) => setApprovals(res.approvals || []))
      .catch((err) => console.error("Error loading approvals:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadApprovals();
  }, [filter]);

  const openApproveModal = (item: any) => {
    setSelectedApproval(item);
    setCommentInput("");
    setActiveModal("approve");
  };

  const openRejectModal = (item: any) => {
    setSelectedApproval(item);
    setRejectionReason("");
    setActiveModal("reject");
  };

  const openPayloadModal = (item: any) => {
    setSelectedApproval(item);
    setActiveModal("payload");
  };

  const openCommentsModal = (item: any) => {
    setSelectedApproval(item);
    setNewCommentText("");
    setActiveModal("comments");
  };

  const handleConfirmApprove = async () => {
    if (!selectedApproval) return;
    setProcessingId(selectedApproval.id);
    try {
      await api.approvals.approve(selectedApproval.id, commentInput);
      setStatusMessage(`Operation #${selectedApproval.id.slice(0, 8)} approved and signed.`);
      setActiveModal(null);
      loadApprovals();
    } catch (err: any) {
      alert("Approval failed: " + (err.message || "Failed"));
    } finally {
      setProcessingId(null);
    }
  };

  const handleConfirmReject = async () => {
    if (!selectedApproval) return;
    if (!rejectionReason.trim()) {
      alert("A reason is required to reject an operational approval.");
      return;
    }
    setProcessingId(selectedApproval.id);
    try {
      await api.approvals.reject(selectedApproval.id, rejectionReason);
      setStatusMessage(`Operation #${selectedApproval.id.slice(0, 8)} rejected.`);
      setActiveModal(null);
      loadApprovals();
    } catch (err: any) {
      alert("Rejection failed: " + (err.message || "Failed"));
    } finally {
      setProcessingId(null);
    }
  };

  const handleAddComment = async () => {
    if (!selectedApproval || !newCommentText.trim()) return;
    try {
      await api.approvals.addComment(selectedApproval.id, newCommentText);
      const updated = {
        ...selectedApproval,
        comments: [
          ...(selectedApproval.comments || []),
          {
            author_name: "Manager (You)",
            comment: newCommentText,
            created_at: new Date().toISOString(),
          },
        ],
      };
      setSelectedApproval(updated);
      setNewCommentText("");
      loadApprovals();
    } catch (err: any) {
      alert("Failed to add comment: " + err.message);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Human-in-the-Loop Approvals Desk"
          subtitle="Cryptographically sealed, multi-signature sign-off for high-value transactions and automated actions"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {statusMessage && (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-xl text-emerald-400 text-xs font-semibold flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>{statusMessage}</span>
              </div>
              <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 flex-wrap">
              {["PENDING", "APPROVED", "REJECTED", "ALL"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilter(st)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    filter === st
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : "bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800"
                  }`}
                >
                  {st === "PENDING"
                    ? "Pending Sign-off"
                    : st === "APPROVED"
                    ? "Approved"
                    : st === "REJECTED"
                    ? "Rejected"
                    : "All Requests"}
                </button>
              ))}
            </div>

            <button
              onClick={loadApprovals}
              disabled={loading}
              className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 rounded-xl transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>

          {/* Approvals List */}
          <div className="space-y-4">
            {loading ? (
              <div className="py-16 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Loading pending requests...</span>
              </div>
            ) : approvals.length === 0 ? (
              <div className="text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
                <CheckCircle2 className="w-12 h-12 text-emerald-500/60 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">Inbox Clean</h3>
                <p className="text-xs text-slate-400 mt-1">No pending operations require your signature right now.</p>
              </div>
            ) : (
              approvals.map((item) => {
                const isProcessing = processingId === item.id;
                const reqType = item.request_type || "ACTION";

                return (
                  <div
                    key={item.id}
                    className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-slate-700 transition space-y-4 backdrop-blur-md"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-xl mt-0.5">
                          <CheckSquare className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-bold text-sm text-white">
                              {item.title || reqType}
                            </span>
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                                item.risk_level === "CRITICAL"
                                  ? "bg-purple-950/60 text-purple-400 border-purple-800"
                                  : item.risk_level === "HIGH"
                                  ? "bg-rose-950/60 text-rose-400 border-rose-800"
                                  : "bg-blue-950/60 text-blue-400 border-blue-800"
                              }`}
                            >
                              Risk: {item.risk_level || "MEDIUM"}
                            </span>

                            <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-slate-950 text-slate-300 border border-slate-800">
                              {item.approval_mode || "ONE_APPROVER"}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate-400 mt-1.5 flex flex-wrap items-center gap-2">
                            <span>
                              Requester: <strong className="text-slate-200">{item.requested_by_type || "AI_EMPLOYEE"}</strong>
                            </span>
                            <span>•</span>
                            <span>Required Roles: {JSON.stringify(item.required_roles || ["OPERATIONS_MANAGER"])}</span>
                            {item.expires_at && (
                              <>
                                <span>•</span>
                                <span className="font-mono text-amber-400">Expires: {formatDate(item.expires_at)}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="text-right sm:self-auto self-end flex flex-col items-end">
                        {item.amount ? (
                          <div className="text-xl font-black text-white">
                            {formatCurrency(item.amount, item.currency || "INR")}
                          </div>
                        ) : (
                          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Action Review
                          </div>
                        )}
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {formatDate(item.created_at)}
                        </div>
                      </div>
                    </div>

                    {/* Cryptographic Hash Badge & Security Snapshot */}
                    <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-[11px]">
                      <div className="flex items-center gap-1.5 font-mono text-slate-400">
                        <Lock className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="font-semibold text-slate-300">SHA-256 Payload Hash:</span>
                        <span className="text-indigo-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-[10px]">
                          {item.action_payload_hash ? `${item.action_payload_hash.slice(0, 16)}...` : "VERIFIED_ATTESTATION"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openPayloadModal(item)}
                          className="px-2.5 py-1 text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded-lg font-medium text-[11px] flex items-center gap-1 transition-colors border border-slate-800"
                        >
                          <Eye className="w-3 h-3 text-indigo-400" />
                          <span>Inspect Payload</span>
                        </button>

                        <button
                          onClick={() => openCommentsModal(item)}
                          className="px-2.5 py-1 text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded-lg font-medium text-[11px] flex items-center gap-1 transition-colors border border-slate-800"
                        >
                          <MessageSquare className="w-3 h-3 text-indigo-400" />
                          <span>Audit Trail</span>
                        </button>
                      </div>
                    </div>

                    {/* Policy Justification */}
                    <div className="p-3 bg-amber-950/40 border border-amber-900/60 rounded-xl space-y-1 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-400 text-[11px]">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                        <span>Policy Trigger Reason</span>
                      </div>
                      <p className="text-slate-300 text-[11px]">{item.reason || "Exceeded autonomous execution threshold."}</p>
                    </div>

                    {/* Action Controls */}
                    {item.status === "PENDING" && (
                      <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
                        <button
                          onClick={() => openRejectModal(item)}
                          disabled={isProcessing}
                          className="px-4 py-2 border border-slate-800 hover:bg-rose-950/60 hover:text-rose-300 hover:border-rose-800 text-slate-300 text-xs font-bold rounded-xl transition-colors disabled:opacity-50"
                        >
                          Reject Request
                        </button>
                        <button
                          onClick={() => openApproveModal(item)}
                          disabled={isProcessing}
                          className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                        >
                          {isProcessing ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <ShieldCheck className="w-4 h-4" />
                          )}
                          <span>Sign & Approve</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </main>
      </div>

      {/* Approve Confirmation Modal */}
      {activeModal === "approve" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-sm text-white">Authorize & Sign Execution</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Confirm authorization for <strong className="text-white">{selectedApproval.title}</strong>. This decision is cryptographically logged in the audit ledger.
            </p>

            <div className="space-y-1 text-xs">
              <label className="font-bold text-slate-400">Approval Comment (Optional)</label>
              <textarea
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                placeholder="e.g. Verified with supplier over phone; approved for dispatch."
                rows={3}
                className="w-full p-3 font-medium text-xs bg-slate-950 border border-slate-800 rounded-xl focus:border-indigo-500 text-white outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmApprove}
                disabled={processingId === selectedApproval.id}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center gap-1.5"
              >
                {processingId === selectedApproval.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm & Sign</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {activeModal === "reject" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-rose-400" />
                <h3 className="font-bold text-sm text-white">Reject Request</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              <label className="font-bold text-slate-300">Mandatory Justification Reason</label>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Explain why this request is rejected..."
                rows={3}
                required
                className="w-full p-3 font-medium text-xs bg-slate-950 border border-slate-800 rounded-xl focus:border-rose-500 text-white outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                disabled={processingId === selectedApproval.id}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-600/30 flex items-center gap-1.5"
              >
                {processingId === selectedApproval.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Reject Request</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payload Inspection Modal */}
      {activeModal === "payload" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Lock className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm text-white">Action Payload Inspector</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <span className="font-mono text-slate-400 text-[11px]">
                Payload Hash: {selectedApproval.action_payload_hash}
              </span>
              <pre className="p-3 bg-slate-950 text-indigo-300 rounded-xl font-mono text-[11px] border border-slate-800 max-h-64 overflow-y-auto">
                {JSON.stringify(selectedApproval.action_payload || selectedApproval.action_params || {}, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
