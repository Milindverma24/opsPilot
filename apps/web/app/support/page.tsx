"use client";

import { useEffect, useState } from "react";
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
  User
} from "lucide-react";

export default function SupportPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<any | null>(null);
  const [conversation, setConversation] = useState<any | null>(null);
  const [convLoading, setConvLoading] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await api.support.tickets();
      setTickets(res.data || []);
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
    try {
      const res = await api.support.conversation(ticket.customer_id);
      setConversation(res.data);
    } catch (err) {
      console.error("Failed to load customer conversation:", err);
    } finally {
      setConvLoading(false);
    }
  };

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || !conversation?.conversation_id) return;
    setSending(true);
    try {
      await api.support.addMessage(conversation.conversation_id, {
        sender_type: "EMPLOYEE",
        content: replyText.trim()
      });
      setReplyText("");
      // Refresh conversation
      const res = await api.support.conversation(selectedTicket.customer_id);
      setConversation(res.data);
    } catch (err: any) {
      alert(err.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
        return <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Critical</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">High</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-xs rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">Low</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <Headphones className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Customer Support & Care</h1>
          <p className="text-sm text-slate-400">Ticket escalation, live messaging, and untrusted prompt injection defense.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Tickets List */}
        <div className="lg:col-span-2 space-y-3">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Active Support Cases ({tickets.length})
          </div>
          <div className="space-y-2 max-h-[700px] overflow-y-auto pr-1">
            {loading ? (
              <div className="py-12 text-center text-slate-400 text-sm">Loading tickets...</div>
            ) : tickets.map((t) => (
              <div
                key={t.id}
                onClick={() => handleSelectTicket(t)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${selectedTicket?.id === t.id ? 'bg-slate-800/80 border-blue-500' : 'bg-slate-900 border-slate-800 hover:border-slate-700'}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs font-bold text-white">{t.ticket_number}</span>
                  {getPriorityBadge(t.priority)}
                </div>
                <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">{t.subject}</h4>
                <div className="flex justify-between items-center text-xs text-slate-400 mt-2">
                  <span>{t.customer_name}</span>
                  <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{t.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Conversation & Untrusted Input Tagging */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col h-[740px] overflow-hidden">
          {selectedTicket ? (
            <>
              {/* Header */}
              <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white">{selectedTicket.ticket_number}</span>
                    <span className="text-xs text-slate-400">• {selectedTicket.customer_name}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white mt-0.5">{selectedTicket.subject}</h3>
                </div>
                <div>{getPriorityBadge(selectedTicket.priority)}</div>
              </div>

              {/* Messages Feed */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                {convLoading ? (
                  <div className="py-20 text-center text-slate-400 text-sm">Loading messages...</div>
                ) : conversation?.messages?.length === 0 ? (
                  <div className="py-20 text-center text-slate-400 text-sm">No messages yet in this channel.</div>
                ) : (
                  conversation?.messages?.map((m: any) => (
                    <div
                      key={m.id}
                      className={`flex flex-col ${m.sender_type === 'CUSTOMER' ? 'items-start' : 'items-end'}`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-medium text-slate-400">
                          {m.sender_type === 'CUSTOMER' ? selectedTicket.customer_name : 'Customer Care Agent'}
                        </span>
                        {m.is_untrusted && (
                          <span className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                            <ShieldAlert className="w-2.5 h-2.5" /> UNTRUSTED_INPUT
                          </span>
                        )}
                      </div>
                      <div
                        className={`p-3.5 rounded-xl max-w-lg text-sm ${m.sender_type === 'CUSTOMER' ? 'bg-slate-950 border border-slate-800 text-slate-200' : 'bg-blue-600 text-white shadow-sm'}`}
                      >
                        {m.content}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Reply Form */}
              <form onSubmit={handleSendReply} className="p-4 bg-slate-950/90 border-t border-slate-800 flex gap-3 items-center">
                <input
                  type="text"
                  placeholder="Type an official support reply..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
                />
                <button
                  type="submit"
                  disabled={sending || !replyText.trim()}
                  className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                  {sending ? "Sending..." : "Reply"}
                </button>
              </form>
            </>
          ) : (
            <div className="m-auto text-center text-slate-400 p-8">
              <Headphones className="w-10 h-10 mx-auto mb-3 text-slate-600" />
              <p className="text-sm">Select a support case on the left to view customer communication stream.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
