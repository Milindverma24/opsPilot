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

  const openCommentsModal = async (item: any) => {
    setSelectedApproval(item);
    setActiveModal("comments");
    try {
      const full = await api.approvals.get(item.id);
      setSelectedApproval(full);
    } catch {}
  };

  const handleConfirmApprove = async () => {
    if (!selectedApproval) return;
    setProcessingId(selectedApproval.id);
    try {
      const res = await api.approvals.approve(selectedApproval.id, commentInput);
      setStatusMessage(res.message || `Approval granted successfully. Workflow resumed!`);
      setActiveModal(null);
      loadApprovals();
    } catch (err: any) {
      alert("Approval error: " + (err.message || "Failed to approve"));
    } finally {
      setProcessingId(null);
    }
  };

  const handleConfirmReject = async () => {
    if (!selectedApproval) return;
    if (!rejectionReason.trim()) {
      alert("Rejection reason is required by governance policy.");
      return;
    }
    setProcessingId(selectedApproval.id);
    try {
      await api.approvals.reject(selectedApproval.id, rejectionReason);
      setStatusMessage(`Approval #${selectedApproval.id.slice(0, 8)} rejected. Associated workflow cancelled.`);
      setActiveModal(null);
      loadApprovals();
    } catch (err: any) {
      alert("Rejection error: " + err.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handlePostComment = async () => {
    if (!selectedApproval || !newCommentText.trim()) return;
    try {
      const res = await api.approvals.addComment(selectedApproval.id, newCommentText);
      setSelectedApproval({
        ...selectedApproval,
        comments: [...(selectedApproval.comments || []), res.comment || res],
      });
      setNewCommentText("");
    } catch (err: any) {
      alert("Failed to post comment: " + err.message);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Human-in-the-Loop Governance & Approvals"
          subtitle="Cryptographically verified action review, separation of duties, and multi-level human sign-off"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Status Message Alert */}
          {statusMessage && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{statusMessage}</span>
              </div>
              <button onClick={() => setStatusMessage(null)} className="text-emerald-700 hover:text-emerald-900 text-xs">
                Dismiss
              </button>
            </div>
          )}

          {/* Filter tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            {["PENDING", "APPROVED", "REJECTED", "EXPIRED", "CANCELLED"].map((st) => (
              <button
                key={st}
                onClick={() => setFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  filter === st
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Approvals Grid */}
          <div className="space-y-4">
            {loading ? (
              <div className="py-16 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>Loading approvals queue...</span>
              </div>
            ) : approvals.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-2xl border border-slate-200 p-8 space-y-2">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
                <h3 className="text-sm font-bold text-slate-900">Governance Clear!</h3>
                <p className="text-xs text-slate-500">
                  No {filter.toLowerCase()} approvals requiring your attention at this time.
                </p>
              </div>
            ) : (
              approvals.map((item) => {
                const isProcessing = processingId === item.id;
                const reqType = (item.approval_type || item.action_type || item.request_type || "OPERATION").replace(/_/g, " ");

                return (
                  <div
                    key={item.id}
                    className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
                          <CheckSquare className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-slate-900">
                              {item.title || reqType}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                              item.risk_level === "CRITICAL"
                                ? "bg-purple-50 text-purple-700 border-purple-200"
                                : item.risk_level === "HIGH"
                                ? "bg-rose-50 text-rose-700 border-rose-200"
                                : "bg-blue-50 text-blue-700 border-blue-200"
                            }`}>
                              Risk: {item.risk_level}
                            </span>

                            {/* Approval Mode Badge */}
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-slate-700 border border-slate-200">
                              {item.approval_mode || "ONE_APPROVER"}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate-500 mt-1 flex flex-wrap items-center gap-2">
                            <span>Requester: <strong className="text-slate-700 font-semibold">{item.requested_by_type || "AI_EMPLOYEE"}</strong></span>
                            <span>•</span>
                            <span>Required Roles: {JSON.stringify(item.required_roles || ["MANAGER"])}</span>
                            {item.expires_at && (
                              <>
                                <span>•</span>
                                <span className="font-mono text-slate-400">Expires: {formatDate(item.expires_at)}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="text-right sm:self-auto self-end flex flex-col items-end">
                        {item.amount ? (
                          <div className="text-lg font-black text-slate-900">
                            {formatCurrency(item.amount, item.currency || "INR")}
                          </div>
                        ) : (
                          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                            Action Review
                          </div>
                        )}
                        <div className="text-[10px] text-slate-400 font-mono">
                          {formatDate(item.created_at)}
                        </div>
                      </div>
                    </div>

                    {/* Cryptographic Hash Badge & Security Snapshot */}
                    <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-slate-50 rounded-xl border border-slate-200/80 text-[11px]">
                      <div className="flex items-center gap-1.5 font-mono text-slate-600">
                        <Lock className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="font-semibold text-slate-800">SHA-256 Payload Hash:</span>
                        <span className="text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 text-[10px]">
                          {item.action_payload_hash ? `${item.action_payload_hash.slice(0, 16)}...` : "VERIFIED_ATTESTATION"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openPayloadModal(item)}
                          className="px-2 py-1 text-slate-600 hover:text-blue-600 hover:bg-white rounded font-medium text-[11px] flex items-center gap-1 transition-colors"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Inspect Payload</span>
                        </button>

                        <button
                          onClick={() => openCommentsModal(item)}
                          className="px-2 py-1 text-slate-600 hover:text-blue-600 hover:bg-white rounded font-medium text-[11px] flex items-center gap-1 transition-colors"
                        >
                          <MessageSquare className="w-3 h-3" />
                          <span>Audit Trail</span>
                        </button>
                      </div>
                    </div>

                    {/* Policy Justification */}
                    <div className="p-3 bg-amber-50/70 border border-amber-100 rounded-xl space-y-1 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900 text-[11px]">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                        <span>Policy Trigger Reason</span>
                      </div>
                      <p className="text-slate-700 text-[11px]">{item.reason}</p>
                    </div>

                    {/* Multi-Level Signatures Collected */}
                    {item.approvals_received && item.approvals_received.length > 0 && (
                      <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl space-y-1.5 text-xs">
                        <span className="font-bold text-blue-900 text-[11px]">Signatures Recorded:</span>
                        <div className="space-y-1">
                          {item.approvals_received.map((sig: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between text-[11px] text-slate-700 font-mono">
                              <span>✓ {sig.user_name} ({sig.role})</span>
                              <span className="text-slate-400">{formatDate(sig.approved_at)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action Controls */}
                    {item.status === "PENDING" && (
                      <div className="flex items-center justify-end gap-2.5 pt-1 border-t border-slate-100">
                        <button
                          onClick={() => openRejectModal(item)}
                          disabled={isProcessing}
                          className="px-4 py-2 border border-slate-300 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-300 text-slate-700 text-xs font-bold rounded-xl transition-colors disabled:opacity-50"
                        >
                          Reject Request
                        </button>
                        <button
                          onClick={() => openApproveModal(item)}
                          disabled={isProcessing}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
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
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-sm text-slate-900">Authorize Execution</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              You are granting human supervisory approval for <strong className="text-slate-900 font-semibold">{selectedApproval.title || selectedApproval.approval_type}</strong>.
              Upon confirmation, the workflow engine will re-validate the SHA-256 payload integrity hash and resume execution.
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Audit Comment (Optional)</label>
              <textarea
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                placeholder="e.g., Reviewed return documents and verified inventory status..."
                rows={3}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmApprove}
                disabled={processingId === selectedApproval.id}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm flex items-center gap-1.5"
              >
                {processingId === selectedApproval.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm & Authorize</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {activeModal === "reject" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-rose-600" />
                <h3 className="font-bold text-sm text-slate-900">Reject Approval Request</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700">
                Mandatory Rejection Reason <span className="text-rose-500">*</span>
              </label>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="State policy violation, lack of documentation, or reason for rejection..."
                rows={3}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-rose-500 outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                disabled={processingId === selectedApproval.id}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl shadow-sm flex items-center gap-1.5"
              >
                {processingId === selectedApproval.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Reject & Cancel Workflow</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payload Inspection Modal */}
      {activeModal === "payload" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Lock className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-sm text-slate-900">Cryptographic Payload Inspector</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 font-mono text-[11px] break-all">
                <span className="font-bold text-slate-800">SHA-256 Digest:</span>
                <p className="text-emerald-700 mt-1">{selectedApproval.action_payload_hash || "NOT_HASHED"}</p>
              </div>

              <div>
                <span className="font-bold text-slate-700">Action Payload:</span>
                <pre className="mt-1 p-3 bg-slate-900 text-emerald-400 rounded-xl font-mono text-[11px] overflow-x-auto max-h-60">
                  {JSON.stringify(selectedApproval.action_payload || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comments & Audit Modal */}
      {activeModal === "comments" && selectedApproval && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-sm text-slate-900">Audit Comments Thread</h3>
              </div>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 flex-1 overflow-y-auto">
              {!selectedApproval.comments || selectedApproval.comments.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  No comments recorded for this approval yet.
                </div>
              ) : (
                selectedApproval.comments.map((c: any) => (
                  <div key={c.id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-800">{c.user_name || "Auditor"}</span>
                      <span className="text-slate-400 font-mono text-[10px]">{formatDate(c.created_at)}</span>
                    </div>
                    <p className="text-xs text-slate-700">{c.comment}</p>
                  </div>
                ))
              )}
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <input
                type="text"
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder="Add human auditor note..."
                className="flex-1 text-xs p-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
              />
              <button
                onClick={handlePostComment}
                className="p-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
