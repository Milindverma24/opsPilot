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
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function OperationsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("ALL");
  const [search, setSearch] = useState("");
  const [ingestModalOpen, setIngestModalOpen] = useState(false);

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
      alert("Error ingesting event: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    const matchesFilter = filterType === "ALL" || ev.event_type === filterType;
    const matchesSearch = !search || ev.title.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Operations Inbox"
          subtitle="Unified stream of incoming transactions, customer inquiries, and automated events"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search operational events..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                />
              </div>

              {/* Event Type Filter */}
              <div className="flex items-center gap-1 text-xs">
                {["ALL", "INVOICE", "COMPLAINT", "PURCHASE_ORDER"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilterType(t)}
                    className={`px-2.5 py-1.5 rounded-lg font-semibold transition-colors ${
                      filterType === t
                        ? "bg-slate-900 text-white shadow-sm"
                        : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                    }`}
                  >
                    {t.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => setIngestModalOpen(true)}
              className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm flex items-center justify-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Ingest New Event</span>
            </button>
          </div>

          {/* Events Table */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Event Title & Source</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Content Preview</th>
                    <th className="py-3 px-4">Received</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredEvents.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-900">
                        <div className="font-bold text-slate-900">{ev.title}</div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Source: {ev.source}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[10px]">
                          {ev.event_type}
                        </span>
                      </td>

                      <td className="py-3 px-4 max-w-xs truncate text-slate-500 font-mono text-[11px]">
                        {ev.content_preview}
                      </td>

                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                        {formatDate(ev.received_at)}
                      </td>

                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                          {ev.status || "PROCESSED"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Ingest Modal */}
      {ingestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Ingest Operational Event</h3>
              <button onClick={() => setIngestModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleIngest} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Urgent complaint from Acme client"
                  required
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Stream Category</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="INVOICE">Invoice</option>
                  <option value="COMPLAINT">Customer Complaint</option>
                  <option value="PURCHASE_ORDER">Purchase Order</option>
                  <option value="OTHER">General Operations</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payload Content</label>
                <textarea
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste invoice JSON, raw complaint email, or payload..."
                  required
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg font-mono text-[11px] focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1.5"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>Trigger Autonomous Pipeline</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
