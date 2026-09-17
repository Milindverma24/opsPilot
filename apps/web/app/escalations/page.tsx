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
  const [resolutionText, setResolutionText] = useState<string>("Issue mitigated via manual verification.");

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
      setStatusMessage("Escalation acknowledged. Assigned to operations triage.");
      loadEscalations();
    } catch (err: any) {
      alert("Error acknowledging: " + (err.message || "Failed"));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePromote = async (id: string) => {
    setActionLoadingId(id);
    try {
      await api.escalations.promote(id, "Escalated by supervisor to Level 2 tier.");
      setStatusMessage("Incident escalated to Level 2 Tier.");
      loadEscalations();
    } catch (err: any) {
      alert("Error promoting: " + (err.message || "Failed"));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleConfirmResolve = async () => {
    if (!resolveModalEsc || !resolutionText.trim()) return;
    setActionLoadingId(resolveModalEsc.id);
    try {
      await api.escalations.resolve(resolveModalEsc.id, resolutionText);
      setStatusMessage(`Incident #${resolveModalEsc.id.slice(0, 8)} resolved.`);
      setResolveModalEsc(null);
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
      setStatusMessage(`SLA Scan: ${res.breached_count || 0} overdue escalations checked.`);
      loadEscalations();
    } catch (err: any) {
      alert("SLA check failed: " + err.message);
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case "LEVEL_3":
        return "bg-purple-950/60 text-purple-400 border-purple-800";
      case "LEVEL_2":
        return "bg-rose-950/60 text-rose-400 border-rose-800";
      default:
        return "bg-amber-950/60 text-amber-400 border-amber-800";
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-rose-950/60 text-rose-400 border-rose-800";
      case "HIGH":
        return "bg-amber-950/60 text-amber-400 border-amber-800";
      default:
        return "bg-blue-950/60 text-blue-400 border-blue-800";
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Escalations & Real-Time SLA Cockpit"
          subtitle="Tier-based human oversight, incident response escalation trees, and guaranteed SLA timers"
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

          {/* Action Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-wrap">
              {["ALL", "OPEN", "ACKNOWLEDGED", "RESOLVED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilter(st)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    filter === st
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={handleCheckSla}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 shadow-sm transition-all"
              >
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Scan Overdue SLAs</span>
              </button>
              <button
                onClick={loadEscalations}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl transition-all"
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
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Fetching active escalations...</span>
              </div>
            ) : escalations.length === 0 ? (
              <div className="py-20 text-center bg-slate-900/60 rounded-2xl border border-slate-800 p-8 space-y-3">
                <CheckCircle2 className="w-12 h-12 text-emerald-500/60 mx-auto mb-2" />
                <h3 className="text-base font-bold text-white">Zero Unresolved Incidents</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
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
                    className={`bg-slate-900/80 border rounded-2xl p-5 shadow-xl transition-all space-y-4 backdrop-blur-md ${
                      isOverdue
                        ? "border-rose-800/80 shadow-lg shadow-rose-950/30"
                        : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${isOverdue ? "bg-rose-500/10 text-rose-400 border border-rose-500/30" : "bg-amber-500/10 text-amber-400 border border-amber-500/30"}`}>
                          <ShieldAlert className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-bold text-sm text-white">
                              Incident #{esc.id.slice(0, 8)}
                            </span>
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getLevelBadge(esc.level)}`}>
                              {esc.level || "LEVEL_1"}
                            </span>
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getSeverityBadge(esc.severity)}`}>
                              {esc.severity || "HIGH"}
                            </span>
                            {isOverdue && (
                              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-600 text-white animate-pulse">
                                SLA OVERDUE
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-1 font-mono">
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
                        <Clock className={`w-4 h-4 ${isOverdue ? "text-rose-400 animate-bounce" : "text-slate-400"}`} />
                        <span className={`font-mono text-[11px] ${isOverdue ? "text-rose-400 font-bold" : "text-slate-300"}`}>
                          Due: {formatDate(esc.due_at)}
                        </span>
                      </div>
                    </div>

                    {/* Reason / Incident Description */}
                    <div className="text-xs text-slate-300 space-y-1">
                      <span className="font-semibold text-slate-400">Incident Details:</span>
                      <p className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-medium">
                        {esc.reason}
                      </p>
                    </div>

                    {/* Resolution if resolved */}
                    {esc.resolution && (
                      <div className="text-xs text-emerald-400 space-y-1">
                        <span className="font-semibold text-emerald-300">Resolution Notes:</span>
                        <p className="bg-emerald-950/40 p-3 rounded-xl border border-emerald-800 font-medium">
                          {esc.resolution}
                        </p>
                      </div>
                    )}

                    {/* Action Controls */}
                    {esc.status !== "RESOLVED" && (
                      <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-800">
                        {esc.status === "OPEN" && (
                          <button
                            onClick={() => handleAcknowledge(esc.id)}
                            disabled={isProcessing}
                            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-1 shadow-md shadow-indigo-600/30 transition"
                          >
                            <UserCheck className="w-3.5 h-3.5" />
                            <span>Acknowledge Incident</span>
                          </button>
                        )}

                        <button
                          onClick={() => handlePromote(esc.id)}
                          disabled={isProcessing}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold inline-flex items-center gap-1 transition"
                        >
                          <ArrowUpRight className="w-3.5 h-3.5 text-amber-400" />
                          <span>Escalate Tier</span>
                        </button>

                        <button
                          onClick={() => {
                            setResolveModalEsc(esc);
                            setResolutionText("Issue verified and cleared by staff.");
                          }}
                          disabled={isProcessing}
                          className="px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 inline-flex items-center gap-1.5 transition"
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
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-sm text-white">Resolve Incident #{resolveModalEsc.id.slice(0, 8)}</h3>
              </div>
              <button onClick={() => setResolveModalEsc(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              <label className="font-bold text-slate-300">Resolution Summary</label>
              <textarea
                value={resolutionText}
                onChange={(e) => setResolutionText(e.target.value)}
                placeholder="Explain the corrective action taken..."
                rows={3}
                required
                className="w-full p-3 font-medium text-xs bg-slate-950 border border-slate-800 rounded-xl focus:border-indigo-500 text-white outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setResolveModalEsc(null)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmResolve}
                disabled={actionLoadingId === resolveModalEsc.id}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center gap-1.5"
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
