"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowUpRight,
  UserCheck,
  RotateCcw,
  Search,
  Filter,
  Loader2,
  X,
  MessageSquare,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Modal states
  const [resolveModalEsc, setResolveModalEsc] = useState<any>(null);
  const [resolutionText, setResolutionText] = useState<string>("");

  const loadEscalations = () => {
    setLoading(true);
    const params = filter === "ALL" ? {} : { status: filter };
    api.escalations
      .list(params)
      .then((res) => setEscalations(res.escalations || []))
      .catch((err) => console.error("Error loading escalations:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEscalations();
  }, [filter]);

  const handleAcknowledge = async (id: string) => {
    setActionLoadingId(id);
    try {
      await api.escalations.acknowledge(id);
      setStatusMessage("Escalation acknowledged. You are assigned as incident owner.");
      loadEscalations();
    } catch (err: any) {
      alert("Error acknowledging: " + (err.message || "Failed"));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePromote = async (id: string) => {
    const reason = prompt("Enter escalation escalation reason:") || "Manual tier escalation triggered by supervisor";
    setActionLoadingId(id);
    try {
      await api.escalations.escalate(id, reason);
      setStatusMessage("Incident escalated to the next operational tier.");
      loadEscalations();
    } catch (err: any) {
      alert("Error escalating: " + (err.message || "Failed"));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleResolve = async () => {
    if (!resolveModalEsc) return;
    if (!resolutionText.trim()) {
      alert("Please provide resolution notes before closing.");
      return;
    }
    setActionLoadingId(resolveModalEsc.id);
    try {
      await api.escalations.resolve(resolveModalEsc.id, resolutionText);
      setStatusMessage(`Incident #${resolveModalEsc.id.slice(0, 8)} successfully resolved.`);
      setResolveModalEsc(null);
      setResolutionText("");
      loadEscalations();
    } catch (err: any) {
      alert("Error resolving: " + (err.message || "Failed"));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCheckSla = async () => {
    try {
      const res = await api.escalations.checkSla();
      setStatusMessage(`SLA check completed. ${res.breached_promoted || 0} overdue incidents auto-promoted.`);
      loadEscalations();
    } catch (err: any) {
      alert("SLA check error: " + err.message);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev?.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-50 text-rose-700 border-rose-200";
      case "HIGH":
        return "bg-orange-50 text-orange-700 border-orange-200";
      case "MEDIUM":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-blue-50 text-blue-700 border-blue-200";
    }
  };

  const getLevelBadge = (lvl: string) => {
    switch (lvl?.toUpperCase()) {
      case "CRITICAL":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "LEVEL_3":
        return "bg-rose-50 text-rose-700 border-rose-200";
      case "LEVEL_2":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Incident Escalations & SLA Management"
          subtitle="Multi-tiered human incident response, SLA countdown monitors, and operational breach progression"
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

          {/* Action Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {["ALL", "OPEN", "ACKNOWLEDGED", "RESOLVED"].map((st) => (
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

            <div className="flex items-center gap-2">
              <button
                onClick={handleCheckSla}
                className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 shadow-sm transition-all"
              >
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span>Scan Overdue SLAs</span>
              </button>
              <button
                onClick={loadEscalations}
                className="p-1.5 bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 rounded-lg shadow-sm transition-all"
                title="Refresh"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Escalations List */}
          <div className="space-y-4">
            {loading ? (
              <div className="py-16 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>Fetching active escalations...</span>
              </div>
            ) : escalations.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-2xl border border-slate-200 p-8 space-y-3">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
                <h3 className="text-base font-bold text-slate-900">Zero Unresolved Incidents</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  All autonomous operations are within normal parameters. No SLA breaches or active escalations detected.
                </p>
              </div>
            ) : (
              escalations.map((esc) => {
                const isProcessing = actionLoadingId === esc.id;
                const isOverdue = esc.due_at && new Date(esc.due_at).getTime() < Date.now() && esc.status !== "RESOLVED";

                return (
                  <div
                    key={esc.id}
                    className={`bg-white border rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow space-y-4 ${
                      isOverdue ? "border-rose-300 ring-1 ring-rose-200 bg-rose-50/20" : "border-slate-200"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${isOverdue ? "bg-rose-100 text-rose-700" : "bg-amber-50 text-amber-600"}`}>
                          <ShieldAlert className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-slate-900">
                              Incident #{esc.id.slice(0, 8)}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getLevelBadge(esc.level)}`}>
                              {esc.level}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getSeverityBadge(esc.severity)}`}>
                              {esc.severity}
                            </span>
                            {isOverdue && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-600 text-white animate-pulse">
                                SLA OVERDUE
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5 font-mono">
                            <span>Team: {esc.assigned_team || "OPERATIONS"}</span>
                            <span>•</span>
                            <span>Status: {esc.status}</span>
                            {esc.assigned_user && (
                              <>
                                <span>•</span>
                                <span>Owner: {esc.assigned_user.full_name}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* SLA Countdown Badge */}
                      <div className="flex items-center gap-2 text-xs">
                        <Clock className={`w-4 h-4 ${isOverdue ? "text-rose-600 animate-bounce" : "text-slate-400"}`} />
                        <span className={`font-mono text-[11px] ${isOverdue ? "text-rose-700 font-bold" : "text-slate-600"}`}>
                          Due: {formatDate(esc.due_at)}
                        </span>
                      </div>
                    </div>

                    {/* Reason / Incident Description */}
                    <div className="text-xs text-slate-700 space-y-1">
                      <span className="font-semibold text-slate-800">Incident Details:</span>
                      <p className="bg-slate-50 p-3 rounded-xl border border-slate-100 font-medium">
                        {esc.reason}
                      </p>
                    </div>

                    {/* Resolution if resolved */}
                    {esc.resolution && (
                      <div className="text-xs text-emerald-800 space-y-1">
                        <span className="font-semibold text-emerald-900">Resolution Notes:</span>
                        <p className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-200 font-medium">
                          {esc.resolution}
                        </p>
                      </div>
                    )}

                    {/* Action Controls */}
                    {esc.status !== "RESOLVED" && (
                      <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-100">
                        {esc.status === "OPEN" && (
                          <button
                            onClick={() => handleAcknowledge(esc.id)}
                            disabled={isProcessing}
                            className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                          >
                            <UserCheck className="w-3.5 h-3.5" />
                            <span>Acknowledge Incident</span>
                          </button>
                        )}

                        <button
                          onClick={() => handlePromote(esc.id)}
                          disabled={isProcessing}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                        >
                          <ArrowUpRight className="w-3.5 h-3.5" />
                          <span>Escalate Tier</span>
                        </button>

                        <button
                          onClick={() => {
                            setResolveModalEsc(esc);
                            setResolutionText("");
                          }}
                          disabled={isProcessing}
                          className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold inline-flex items-center gap-1 shadow-sm transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Resolve Incident</span>
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

      {/* Resolve Incident Modal */}
      {resolveModalEsc && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-sm text-slate-900">
                  Resolve Incident #{resolveModalEsc.id.slice(0, 8)}
                </h3>
              </div>
              <button onClick={() => setResolveModalEsc(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700">
                Action & Resolution Notes <span className="text-rose-500">*</span>
              </label>
              <textarea
                value={resolutionText}
                onChange={(e) => setResolutionText(e.target.value)}
                placeholder="Describe corrective action taken, root cause, or carrier re-dispatch instructions..."
                rows={4}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setResolveModalEsc(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                disabled={actionLoadingId === resolveModalEsc.id}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center gap-1.5"
              >
                {actionLoadingId === resolveModalEsc.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm Resolution</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
