"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Inbox,
  Plus,
  Search,
  Filter,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  X,
  Send,
  Zap,
  RefreshCw,
  Eye,
  FileText,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function OperationsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("ALL");
  const [search, setSearch] = useState("");
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);

  // Ingest form state
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [source, setSource] = useState("MANUAL_UPLOAD");
  const [eventType, setEventType] = useState("INVOICE");
  const [submitting, setSubmitting] = useState(false);

  const loadEvents = () => {
    setLoading(true);
    api.events
      .list()
      .then((res) => setEvents(res.events || []))
      .catch((err) => console.error("Error loading events:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSubmitting(true);
    try {
      await api.events.create({ title, content, source, event_type: eventType });
      setIngestModalOpen(false);
      setTitle("");
      setContent("");
      loadEvents();
    } catch (err: any) {
      alert("Error ingesting event: " + (err.message || "Failed"));
    } finally {
      setSubmitting(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    const matchesFilter = filterType === "ALL" || ev.event_type === filterType;
    const matchesSearch = !search || ev.title?.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Operations Event Stream"
          subtitle="Unified stream of incoming transactions, customer inquiries, and autonomous pipeline triggers"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Controls Bar */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 w-full sm:w-auto flex-wrap">
              <div className="relative w-full sm:w-72">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search operational events..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Event Type Filter */}
              <div className="flex items-center gap-1.5 text-xs flex-wrap">
                {["ALL", "INVOICE", "COMPLAINT", "PURCHASE_ORDER"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilterType(t)}
                    className={`px-3 py-1.5 rounded-xl font-semibold transition-all ${
                      filterType === t
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        : "bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700/80"
                    }`}
                  >
                    {t.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              <button
                onClick={loadEvents}
                disabled={loading}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs border border-slate-700 transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>

              <button
                onClick={() => setIngestModalOpen(true)}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-1.5 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Ingest New Event</span>
              </button>
            </div>
          </div>

          {/* Events Table */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3.5 px-4 pl-5">Event Title & Source</th>
                    <th className="py-3.5 px-4">Category</th>
                    <th className="py-3.5 px-4">Content Preview</th>
                    <th className="py-3.5 px-4">Received Time</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                    <th className="py-3.5 px-4 text-right pr-5">Inspection</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredEvents.map((ev) => (
                    <tr
                      key={ev.id}
                      onClick={() => setSelectedEvent(ev)}
                      className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 pl-5">
                        <div className="font-bold text-white group-hover:text-indigo-400 transition-colors">
                          {ev.title}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                          Source: {ev.source}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-lg bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 font-semibold text-[10px]">
                          {ev.event_type}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 max-w-xs truncate text-slate-400 font-mono text-[11px]">
                        {ev.content_preview || "No content payload"}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                        {formatDate(ev.received_at)}
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold text-[10px]">
                          {ev.status || "PROCESSED"}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right pr-5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEvent(ev);
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 group-hover:text-white rounded-lg text-xs font-semibold border border-slate-700 transition flex items-center gap-1 ml-auto"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredEvents.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 p-8">
                <Inbox className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No events found</h3>
                <p className="text-xs text-slate-400 mt-1">Ingest a new event or adjust filter parameters.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Ingest Modal */}
      {ingestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl p-6 max-w-md w-full shadow-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Ingest Operational Event</h3>
              <button
                onClick={() => setIngestModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleIngest} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Event Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Urgent invoice verification from Acme Corp"
                  required
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Stream Category</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="INVOICE">Invoice Processing</option>
                  <option value="COMPLAINT">Customer Complaint</option>
                  <option value="PURCHASE_ORDER">Purchase Order</option>
                  <option value="OTHER">General Operations</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Payload Content (JSON / Text)</label>
                <textarea
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste invoice JSON, raw complaint email, or payload..."
                  required
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-indigo-300 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIngestModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  <span>Trigger Autonomous Pipeline</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Event Details Inspection Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl p-6 max-w-lg w-full shadow-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{selectedEvent.title}</h3>
                  <p className="text-[11px] text-slate-400">ID: #{selectedEvent.id}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div>
                  <span className="text-slate-400">Category:</span>
                  <div className="font-semibold text-white mt-0.5">{selectedEvent.event_type}</div>
                </div>
                <div>
                  <span className="text-slate-400">Source Channel:</span>
                  <div className="font-semibold text-white mt-0.5">{selectedEvent.source}</div>
                </div>
                <div>
                  <span className="text-slate-400">Status:</span>
                  <div className="font-semibold text-emerald-400 mt-0.5">{selectedEvent.status || "PROCESSED"}</div>
                </div>
                <div>
                  <span className="text-slate-400">Received At:</span>
                  <div className="font-semibold text-white mt-0.5">{formatDate(selectedEvent.received_at)}</div>
                </div>
              </div>

              <div>
                <span className="text-slate-400 block mb-1 font-semibold">Raw Content Payload:</span>
                <pre className="p-3 bg-slate-950 text-indigo-300 rounded-xl font-mono text-[11px] border border-slate-800 max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {selectedEvent.content || selectedEvent.content_preview || "No content body"}
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end border-t border-slate-800">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition"
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
