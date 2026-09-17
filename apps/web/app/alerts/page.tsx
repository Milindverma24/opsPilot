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
  Bell,
  Activity,
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
  const [creating, setCreating] = useState(false);
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
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await api.alerts.create({
        alert_type: newType,
        severity: newSeverity,
        title: newTitle.trim(),
        description: newDesc.trim() || undefined,
        source_type: "MANUAL",
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
      await fetchAlerts();
    } catch (err: any) {
      alert("Failed to create alert: " + (err.message || "Unknown error"));
    } finally {
      setCreating(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 shadow-sm shadow-rose-500/10">
            <AlertOctagon className="w-3 h-3" /> CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 shadow-sm shadow-amber-500/10">
            <AlertTriangle className="w-3 h-3" /> HIGH
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
            <Info className="w-3 h-3" /> MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
            LOW
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "OPEN":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-rose-950/60 text-rose-400 border border-rose-800/80">
            OPEN
          </span>
        );
      case "ACKNOWLEDGED":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-amber-950/60 text-amber-400 border border-amber-800/80">
            ACKNOWLEDGED
          </span>
        );
      case "RESOLVED":
        return (
          <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-800/80">
            RESOLVED
          </span>
        );
      default:
        return <span className="text-xs text-slate-400">{status}</span>;
    }
  };

  const openCount = alerts.filter((a) => a.status === "OPEN").length;
  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL" && a.status !== "RESOLVED").length;
  const resolvedCount = alerts.filter((a) => a.status === "RESOLVED").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Autonomous Alert Center"
          subtitle="Real-time operational anomaly tracking, automated escalations, and incident mitigation"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Active Open Alerts</span>
                <Bell className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-rose-400 mt-2">{openCount}</div>
              <div className="text-[11px] text-slate-400 mt-1">Requiring triage or resolution</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Critical Incidents</span>
                <AlertOctagon className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-2">{criticalCount}</div>
              <div className="text-[11px] text-slate-400 mt-1">High-impact operational blocks</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Total Incidents Resolved</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-2">{resolvedCount}</div>
              <div className="text-[11px] text-slate-400 mt-1">Remediated automatically / staff</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Surveillance Status</span>
                <Activity className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white mt-2">Active</div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Anomaly sensors live
              </div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-wrap w-full md:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">All Statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="ACKNOWLEDGED">Acknowledged</option>
                  <option value="RESOLVED">Resolved</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Severity:</span>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto justify-end">
              <button
                onClick={fetchAlerts}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>

              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-rose-600/30 transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Incident Alert</span>
              </button>
            </div>
          </div>

          {/* Alerts Grid */}
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`bg-slate-900/80 border rounded-2xl p-5 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  alert.status === "RESOLVED"
                    ? "border-slate-800 opacity-75"
                    : alert.severity === "CRITICAL"
                    ? "border-rose-800/80 shadow-lg shadow-rose-950/20"
                    : "border-slate-800"
                }`}
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono text-xs text-slate-400">#{alert.id.slice(0, 8)}</span>
                    <h3 className="text-sm font-bold text-white">{alert.title}</h3>
                    {getSeverityBadge(alert.severity)}
                    {getStatusBadge(alert.status)}
                  </div>

                  {alert.description && (
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {alert.description}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1 flex-wrap">
                    <span>
                      Type: <strong className="text-slate-300">{alert.alert_type}</strong>
                    </span>
                    <span>
                      Source: <strong className="text-slate-300">{alert.source_type}</strong>
                    </span>
                    <span>Created: {new Date(alert.created_at).toLocaleString()}</span>
                    {alert.acknowledged_at && (
                      <span className="text-amber-400">
                        Acked: {new Date(alert.acknowledged_at).toLocaleTimeString()}
                      </span>
                    )}
                    {alert.resolved_at && (
                      <span className="text-emerald-400">
                        Resolved: {new Date(alert.resolved_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 justify-end">
                  {alert.status === "OPEN" && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={actingId === alert.id}
                      className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 rounded-xl text-xs font-semibold transition flex items-center gap-1.5"
                    >
                      <span>{actingId === alert.id ? "Acknowledging..." : "Acknowledge"}</span>
                    </button>
                  )}

                  {alert.status !== "RESOLVED" && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      disabled={actingId === alert.id}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>{actingId === alert.id ? "Resolving..." : "Resolve Incident"}</span>
                    </button>
                  )}

                  {alert.status === "RESOLVED" && (
                    <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium bg-emerald-950/40 px-3 py-1.5 rounded-xl border border-emerald-900/50">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Incident Closed
                    </span>
                  )}
                </div>
              </div>
            ))}

            {alerts.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
                <CheckCircle2 className="w-12 h-12 text-emerald-500/60 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">All clear! No alerts detected</h3>
                <p className="text-xs text-slate-400 mt-1">Autonomous systems are running within standard operational thresholds.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Create Alert Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-rose-600/20 text-rose-400 border border-rose-500/30 flex items-center justify-center">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Create Operational Incident Alert</h3>
                  <p className="text-[11px] text-slate-400">Broadcast a manual alert into the operations escalation bus</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAlert} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Alert Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Carrier API Latency Spike (>3500ms)"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-rose-500"
                  >
                    <option value="CRITICAL">CRITICAL (Red Alert)</option>
                    <option value="HIGH">HIGH (Degraded SLA)</option>
                    <option value="MEDIUM">MEDIUM (Warning)</option>
                    <option value="LOW">LOW (Informational)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Anomaly Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-rose-500"
                  >
                    <option value="WORKFLOW_FAILURE">Workflow Failure</option>
                    <option value="CARRIER_TIMEOUT">Carrier Timeout</option>
                    <option value="INVENTORY_DISCREPANCY">Inventory Discrepancy</option>
                    <option value="SECURITY_TRIGGER">Security Policy Trigger</option>
                    <option value="PAYMENT_GATEWAY_ERROR">Payment Gateway Error</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Incident Details & Context</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Describe observed impact, affected SKUs/orders, and mitigation steps taken..."
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-rose-600/30 transition disabled:opacity-50 flex items-center gap-2"
                >
                  {creating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>{creating ? "Broadcasting..." : "Broadcast Alert"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
