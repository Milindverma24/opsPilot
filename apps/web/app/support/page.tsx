"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";
import { 
  Headphones, 
  Search, 
  MessageSquare, 
  ShieldAlert, 
  Send, 
  Clock, 
  CheckCircle2, 
  AlertTriangle,
  User,
  Plus,
  Sparkles,
  Check,
  X,
  BookOpen,
  HelpCircle,
  CornerDownRight,
  ShieldCheck,
  RotateCcw
} from "lucide-react";

export default function SupportPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<any | null>(null);
  const [conversation, setConversation] = useState<any | null>(null);
  const [convLoading, setConvLoading] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [resolving, setResolving] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");

  // RAG Auto-Draft State
  const [ragDrafting, setRagDrafting] = useState(false);
  const [ragCitations, setRagCitations] = useState<any[]>([]);

  // Create Ticket Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCustomerId, setNewCustomerId] = useState("cust-001");
  const [newCustomerName, setNewCustomerName] = useState("Rahul Sharma");
  const [newSubject, setNewSubject] = useState("Size exchange request for Order ORD-102");
  const [newPriority, setNewPriority] = useState("MEDIUM");
  const [newDescription, setNewDescription] = useState("Customer tried the M size hoodie and feels it fits slightly snug. Wants exchange for L.");
  const [createSubmitting, setCreateSubmitting] = useState(false);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await api.support.tickets();
      setTickets(res.data || []);
      if (res.data && res.data.length > 0 && !selectedTicket) {
        handleSelectTicket(res.data[0]);
      }
    } catch (err) {
      console.error("Failed to load tickets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleSelectTicket = async (ticket: any) => {
    setSelectedTicket(ticket);
    setConvLoading(true);
    setRagCitations([]);
    try {
      const res = await api.support.conversation(ticket.customer_id);
      setConversation(res.data);
    } catch (err) {
      console.error("Failed to load customer conversation:", err);
      // Mock fallback conversation if none exists
      setConversation({
        conversation_id: "conv-" + ticket.id,
        messages: [
          {
            id: "m-1",
            sender_type: "CUSTOMER",
            content: ticket.subject + ": " + (ticket.description || "I need immediate help regarding my order."),
            created_at: ticket.created_at || new Date().toISOString(),
            is_untrusted: true
          }
        ]
      });
    } finally {
      setConvLoading(false);
    }
  };

  const handleDraftWithRag = async () => {
    if (!selectedTicket) return;
    setRagDrafting(true);
    setRagCitations([]);
    try {
      const query = selectedTicket.subject + " " + (selectedTicket.description || "");
      const res = await api.knowledge.search(query);
      const results = res.results || [];
      if (results.length > 0) {
        const top = results[0];
        setReplyText(
          `Hi ${selectedTicket.customer_name || "there"},\n\n` +
          `Regarding your query: according to our ${top.document_title || "UrbanThread Policy"}, ${top.content}\n\n` +
          `Please let us know if you would like us to arrange this right away!`
        );
        setRagCitations(results);
      } else {
        setReplyText(
          `Hi ${selectedTicket.customer_name || "there"},\n\n` +
          `Thank you for reaching out to UrbanThread Customer Care. We are reviewing your ticket regarding "${selectedTicket.subject}". ` +
          `Our 30-day exchange window applies to all unworn items with original tags. We will process this for you right away!`
        );
      }
    } catch (err: any) {
      console.error("RAG Auto-Draft failed:", err);
      setReplyText(
        `Hi ${selectedTicket.customer_name || "there"},\n\n` +
        `Thank you for reaching out to UrbanThread Support. We are investigating your inquiry and our team is happy to assist you immediately.`
      );
    } finally {
      setRagDrafting(false);
    }
  };

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || !conversation?.conversation_id) return;
    setSending(true);
    try {
      await api.support.addMessage(conversation.conversation_id, {
        sender_type: "AI_AGENT",
        content: replyText.trim(),
        message_type: "TEXT"
      });
      setConversation((prev: any) => ({
        ...prev,
        messages: [
          ...(prev?.messages || []),
          {
            id: "msg-" + Date.now(),
            sender_type: "AI_AGENT",
            content: replyText.trim(),
            created_at: new Date().toISOString(),
            is_untrusted: false
          }
        ]
      }));
      setReplyText("");
      setRagCitations([]);
    } catch (err: any) {
      alert(err.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleResolveTicket = async () => {
    if (!selectedTicket) return;
    setResolving(true);
    try {
      await api.support.resolve(selectedTicket.id);
      setSelectedTicket((prev: any) => ({ ...prev, status: "RESOLVED" }));
      setTickets((prev) =>
        prev.map((t) => (t.id === selectedTicket.id ? { ...t, status: "RESOLVED" } : t))
      );
    } catch (err: any) {
      alert(err.message || "Failed to resolve ticket");
    } finally {
      setResolving(false);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateSubmitting(true);
    try {
      const res = await api.support.createTicket({
        customer_id: newCustomerId,
        subject: newSubject,
        description: newDescription,
        priority: newPriority
      });
      setShowCreateModal(false);
      await fetchTickets();
    } catch (err: any) {
      alert(err.message || "Failed to create support ticket");
    } finally {
      setCreateSubmitting(false);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case "URGENT":
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">Urgent</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">High</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">Low</span>;
    }
  };

  const filteredTickets = tickets.filter((t) => {
    const matchesSearch =
      t.subject?.toLowerCase().includes(search.toLowerCase()) ||
      t.ticket_number?.toLowerCase().includes(search.toLowerCase()) ||
      t.customer_name?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || t.status === statusFilter;
    const matchesPriority = priorityFilter === "ALL" || t.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Customer Support & Helpdesk"
          subtitle="Ticket escalation, live customer communications, RAG agent auto-drafts, and ticket lifecycle resolution"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Headphones className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tickets</span>
                <div className="text-2xl font-bold text-white mt-0.5">{tickets.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Open Inquiries</span>
                <div className="text-2xl font-bold text-amber-400 mt-0.5">
                  {tickets.filter((t) => t.status === "OPEN").length}
                </div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolved</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">
                  {tickets.filter((t) => t.status === "RESOLVED").length}
                </div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aria RAG Engine</span>
                <div className="text-sm font-bold text-emerald-400 mt-1 flex items-center gap-1">
                  <Check className="w-4 h-4" /> Ready for Drafts
                </div>
              </div>
            </div>
          </div>

          {/* Main 2-Column Split: Tickets List + Conversation Workbench */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Tickets Directory */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">Tickets Queue</h3>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    New Ticket
                  </button>
                </div>

                <div className="relative">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by customer, subject, or #"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Filters */}
                <div className="flex gap-2 text-xs">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="OPEN">Open</option>
                    <option value="RESOLVED">Resolved</option>
                  </select>

                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="ALL">All Priorities</option>
                    <option value="URGENT">Urgent</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              {/* Tickets Cards */}
              <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
                {loading ? (
                  <div className="py-16 text-center text-slate-500 text-xs">Loading support cases...</div>
                ) : filteredTickets.length === 0 ? (
                  <div className="py-16 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                    No tickets found matching filters.
                  </div>
                ) : (
                  filteredTickets.map((t) => {
                    const isSelected = selectedTicket?.id === t.id;
                    return (
                      <div
                        key={t.id}
                        onClick={() => handleSelectTicket(t)}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-slate-900 border-blue-500 shadow-md shadow-blue-500/10"
                            : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex justify-between items-start mb-1.5">
                          <span className="font-mono text-xs font-bold text-white">{t.ticket_number}</span>
                          {getPriorityBadge(t.priority)}
                        </div>
                        <h4 className="text-xs font-semibold text-slate-200 line-clamp-1">{t.subject}</h4>
                        <div className="flex justify-between items-center text-[11px] text-slate-400 mt-2.5">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3 text-slate-500" />
                            {t.customer_name}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              t.status === "RESOLVED"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            {t.status}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Right Column: Active Conversation & RAG Reply Studio */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[740px] overflow-hidden shadow-lg">
              {selectedTicket ? (
                <>
                  {/* Ticket Header Bar */}
                  <div className="p-4 bg-slate-950/90 border-b border-slate-800 flex justify-between items-center shrink-0">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-white">{selectedTicket.ticket_number}</span>
                        <span className="text-xs text-slate-400">• {selectedTicket.customer_name}</span>
                        {getPriorityBadge(selectedTicket.priority)}
                      </div>
                      <p className="text-xs font-semibold text-slate-200 mt-0.5">{selectedTicket.subject}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      {selectedTicket.status !== "RESOLVED" && (
                        <button
                          onClick={handleResolveTicket}
                          disabled={resolving}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-300 font-bold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          {resolving ? "Resolving..." : "Resolve Ticket"}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Messages Feed */}
                  <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-slate-950/40">
                    {convLoading ? (
                      <div className="py-20 text-center text-slate-500 text-xs">Loading conversation history...</div>
                    ) : (conversation?.messages || []).length === 0 ? (
                      <div className="py-20 text-center text-slate-500 text-xs">No message transcript recorded.</div>
                    ) : (
                      (conversation?.messages || []).map((m: any, idx: number) => {
                        const isCustomer = m.sender_type === "CUSTOMER";
                        return (
                          <div
                            key={m.id || idx}
                            className={`flex flex-col ${isCustomer ? "items-start" : "items-end"}`}
                          >
                            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mb-1 px-1">
                              <span>{isCustomer ? selectedTicket.customer_name : "OpsPilot Agent (Aria)"}</span>
                              {m.is_untrusted && (
                                <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px] flex items-center gap-0.5">
                                  <ShieldAlert className="w-2.5 h-2.5" /> Untrusted Input
                                </span>
                              )}
                            </div>
                            <div
                              className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                                isCustomer
                                  ? "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm"
                                  : "bg-blue-600 text-white shadow-md shadow-blue-600/20 rounded-tr-sm"
                              }`}
                            >
                              <p className="whitespace-pre-wrap">{m.content}</p>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* RAG Grounding Banner if available */}
                  {ragCitations.length > 0 && (
                    <div className="p-3 bg-indigo-950/50 border-t border-indigo-500/20 text-xs text-indigo-200 flex items-center justify-between shrink-0">
                      <div className="flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-indigo-400 shrink-0" />
                        <span className="line-clamp-1">
                          Draft grounded in: <strong className="text-white">{ragCitations[0]?.document_title}</strong>
                        </span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold shrink-0">
                        {Math.round((ragCitations[0]?.score || 0.95) * 100)}% Match
                      </span>
                    </div>
                  )}

                  {/* Reply Input Bar */}
                  <form onSubmit={handleSendReply} className="p-3.5 bg-slate-950 border-t border-slate-800 shrink-0 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                        <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
                        Compose Support Response
                      </span>

                      <button
                        type="button"
                        onClick={handleDraftWithRag}
                        disabled={ragDrafting}
                        className="px-3 py-1 rounded-xl bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/30 text-violet-300 text-xs font-bold transition-all flex items-center gap-1.5 disabled:opacity-50"
                        title="Search RAG knowledge base to draft an accurate, policy-backed reply"
                      >
                        <Sparkles className={`w-3.5 h-3.5 text-violet-400 ${ragDrafting ? "animate-spin" : ""}`} />
                        {ragDrafting ? "Drafting with RAG..." : "Draft with Aria (RAG)"}
                      </button>
                    </div>

                    <div className="relative">
                      <textarea
                        rows={3}
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder="Type response to customer or use 'Draft with Aria (RAG)'..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 resize-none pr-12"
                      />
                      <button
                        type="submit"
                        disabled={sending || !replyText.trim()}
                        className="absolute right-2.5 bottom-3.5 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 transition-colors shadow-md shadow-blue-600/20"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2">
                  <Headphones className="w-8 h-8 text-slate-600" />
                  <span>Select a support ticket from the queue to view messages.</span>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Headphones className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Open Support Case</h3>
                  <p className="text-xs text-slate-400">Register new customer grievance or return request</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Customer Identifier / Name</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    required
                    placeholder="cust-001"
                    value={newCustomerId}
                    onChange={(e) => setNewCustomerId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Rahul Sharma"
                    value={newCustomerName}
                    onChange={(e) => setNewCustomerName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Subject *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Size exchange request for Order ORD-102"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Priority</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent (Immediate Escalation)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Description / Customer Message *</label>
                <textarea
                  required
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Detail the issue reported by the customer..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-600/20 disabled:opacity-50"
                >
                  {createSubmitting ? "Creating..." : "Submit Ticket"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
