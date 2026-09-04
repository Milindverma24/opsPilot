"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  Search,
  ShieldAlert,
  ChevronRight,
  Plus,
  X,
  AlertOctagon,
  Info,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [actingId, setActingId] = useState<string | null>(null);

  // New alert modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newSeverity, setNewSeverity] = useState("HIGH");
  const [newType, setNewType] = useState("WORKFLOW_FAILURE");

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.alerts.list({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      });
      setAlerts(res.data || []);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, severityFilter]);

  const handleAcknowledge = async (id: string) => {
    setActingId(id);
    try {
      await api.alerts.acknowledge(id);
      await fetchAlerts();
    } catch (err: any) {
      alert("Acknowledge failed: " + err.message);
    } finally {
      setActingId(null);
    }
  };

  const handleResolve = async (id: string) => {
    setActingId(id);
    try {
      await api.alerts.resolve(id);
      await fetchAlerts();
    } catch (err: any) {
      alert("Resolve failed: " + err.message);
    } finally {
      setActingId(null);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;
    try {
      await api.alerts.create({
        alert_type: newType,
        severity: newSeverity,
        title: newTitle,
        description: newDesc || undefined,
        source_type: "MANUAL",
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
      await fetchAlerts();
    } catch (err: any) {
      alert("Failed to create alert: " + err.message);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-600 border border-rose-500/20 flex items-center gap-1">
            <AlertOctagon className="w-3 h-3" /> CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> HIGH
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-600 border border-blue-500/20 flex items-center gap-1">
            <Info className="w-3 h-3" /> MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            LOW
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "OPEN":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
            OPEN
          </span>
        );
      case "ACKNOWLEDGED":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
            ACKNOWLEDGED
          </span>
        );
      case "RESOLVED":
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            RESOLVED
          </span>
        );
      default:
        return <span className="text-xs text-slate-500">{status}</span>;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Operational Alert Center"
          subtitle="Real-time operational exceptions, workforce degradation notifications, and SLA breach governance"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
                Operational Alerts & Incident Response
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Monitors workflow failures, inventory stockouts, carrier webhook delays, and high-risk approval backlogs.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Trigger Incident Alert</span>
              </button>

              <button
                onClick={fetchAlerts}
                disabled={loading}
                className="p-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-slate-700 shadow-xs transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-slate-500">Filter Status:</span>
              <div className="flex gap-1.5">
                {[
                  { label: "All", value: "" },
                  { label: "Open", value: "OPEN" },
                  { label: "Acknowledged", value: "ACKNOWLEDGED" },
                  { label: "Resolved", value: "RESOLVED" },
                ].map((tab) => (
                  <button
                    key={tab.value}
                    onClick={() => setStatusFilter(tab.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      statusFilter === tab.value
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <span className="text-xs font-semibold text-slate-500">Severity:</span>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-medium focus:outline-none"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>

          {/* Alerts List */}
          <div className="space-y-3">
            {alerts.length === 0 && !loading && (
              <div className="p-8 text-center bg-white rounded-2xl border border-slate-200">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <h3 className="font-bold text-slate-800 text-sm">All Clear</h3>
                <p className="text-xs text-slate-500 mt-1">No active alerts matching your current filter criteria.</p>
              </div>
            )}

            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="space-y-2 max-w-2xl">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    {getSeverityBadge(alert.severity)}
                    {getStatusBadge(alert.status)}
                    <span className="text-[11px] font-mono text-slate-400">#{alert.id}</span>
                    <span className="text-[11px] font-semibold text-blue-600 uppercase bg-blue-50 px-2 py-0.5 rounded">
                      {alert.alert_type}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{alert.title}</h3>
                    <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{alert.description}</p>
                  </div>

                  <div className="text-[11px] text-slate-400 flex items-center gap-3">
                    <span>Source: {alert.source_type || "WORKFLOW"}</span>
                    {alert.source_id && <span>Ref: #{alert.source_id}</span>}
                    <span>•</span>
                    <span>Created: {new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 shrink-0">
                  {alert.status === "OPEN" && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={actingId === alert.id}
                      className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      <span>Acknowledge</span>
                    </button>
                  )}

                  {alert.status !== "RESOLVED" && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      disabled={actingId === alert.id}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Resolve</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>

      {/* Modal: Create Alert */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base">Trigger New Operational Alert</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAlert} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700">Alert Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BlueDart API Carrier Webhook Failure"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-700">Alert Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none"
                  >
                    <option value="WORKFLOW_FAILURE">WORKFLOW_FAILURE</option>
                    <option value="INVENTORY_CRITICAL">INVENTORY_CRITICAL</option>
                    <option value="APPROVAL_BACKLOG">APPROVAL_BACKLOG</option>
                    <option value="CARRIER_DELAY">CARRIER_DELAY</option>
                    <option value="SECURITY_SHIELD">SECURITY_SHIELD</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700">Detailed Description</label>
                <textarea
                  rows={3}
                  placeholder="Details on operational failure, error messages, and impact..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs"
                >
                  Create Alert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
