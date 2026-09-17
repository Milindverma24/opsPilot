"use client";

import { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Package,
  Truck,
  Star,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  Headphones,
  CheckCircle2,
  Clock,
  ExternalLink,
  Lock,
  UserCheck,
  BookOpen,
} from "lucide-react";
import { api } from "@/lib/api";

interface ChatMessage {
  id: string;
  sender_type: string;
  sender_id?: string;
  message_type?: string;
  content: string;
  metadata?: any;
  created_at?: string;
}

export function CustomerChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([
    "Track my order",
    "Return an item",
    "Shipping policy",
    "Find my size",
  ]);
  const [simulatedCustomer, setSimulatedCustomer] = useState<string>("cust-001");
  const [isGuest, setIsGuest] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [handoffRequested, setHandoffRequested] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const [activeOrder, setActiveOrder] = useState<any | null>(null);

  const initConversation = async () => {
    try {
      setLoading(true);
      let orderDetails: any = undefined;
      try {
        const stored = localStorage.getItem("urbanthread_active_order");
        if (stored) {
          orderDetails = JSON.parse(stored);
          setActiveOrder(orderDetails);
        }
      } catch (e) {}

      const res = await api.customer.startConversation({
        channel: "WEBSITE_CHAT",
        customer_id: isGuest ? undefined : simulatedCustomer,
        organization_slug: "urbanthread",
        order_details: orderDetails,
      });

      const conv = res.data;
      setConversationId(conv.conversation_id);
      if (conv.suggested_actions) {
        setSuggestedActions(conv.suggested_actions);
      }
      if (conv.greeting) {
        setMessages([
          {
            id: "msg-init",
            sender_type: "AI_AGENT",
            sender_id: "aria-support-ai",
            message_type: "SUGGESTION",
            content: conv.greeting,
            metadata: { suggested_actions: conv.suggested_actions },
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.error("Failed to start chat session:", err);
      setMessages([
        {
          id: "msg-err",
          sender_type: "SYSTEM",
          content: "Sorry, I had trouble connecting. Type your question below or click an action to retry!",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenWidget = () => {
    setIsOpen(true);
    if (!conversationId) {
      initConversation();
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || loading) return;

    setInputText("");

    // Optimistically add user message
    const userMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      sender_type: "CUSTOMER",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      let activeConvId = conversationId;
      if (!activeConvId) {
        const convRes = await api.customer.startConversation({
          channel: "WEBSITE_CHAT",
          customer_id: isGuest ? undefined : simulatedCustomer,
          organization_slug: "urbanthread",
        });
        activeConvId = convRes.data.conversation_id;
        setConversationId(activeConvId);
      }

      if (!activeConvId) {
        throw new Error("Unable to establish conversation session");
      }

      const res = await api.customer.sendMessage(activeConvId, text);
      const data = res?.data || res || {};
      const responseType = data.response_type || data.message_type || "TEXT";
      const messageContent = data.message || data.content || "I am here to help!";

      // Append assistant message
      const aiMsg: ChatMessage = {
        id: "res-" + Date.now(),
        sender_type: responseType === "HUMAN_HANDOFF" ? "SYSTEM" : "AI_AGENT",
        sender_id: "aria-support-ai",
        message_type: responseType,
        content: messageContent,
        metadata: data.card_data || data.metadata || (data.requires_confirmation ? { confirmation: true } : {}),
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMsg]);

      if (data.requires_confirmation) {
        setSuggestedActions(["Yes, proceed with return", "No, cancel this request"]);
      } else if (responseType === "HUMAN_HANDOFF") {
        setHandoffRequested(true);
        setSuggestedActions(["Check ticket status", "Start new inquiry"]);
      } else {
        setSuggestedActions(["Track my order", "Return an item", "Shipping policy", "Find my size"]);
      }
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: "err-" + Date.now(),
        sender_type: "SYSTEM",
        content: "Sorry, I encountered an issue. " + (err.message || "Please try again."),
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleHandoff = async () => {
    if (!conversationId || loading) return;
    setLoading(true);
    try {
      const res = await api.customer.requestHandoff(conversationId);
      const data = res.data;
      setHandoffRequested(true);
      setMessages((prev) => [
        ...prev,
        {
          id: "sys-handoff-" + Date.now(),
          sender_type: "SYSTEM",
          message_type: "HUMAN_HANDOFF",
          content: data.message || "You have been connected to our human support queue. A representative will review your chat shortly.",
          metadata: { ticket_id: data.ticket_id },
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      alert("Handoff request failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedbackSubmit = async (rating: number) => {
    if (!conversationId) return;
    setFeedbackRating(rating);
    try {
      await api.customer.submitFeedback(conversationId, {
        rating,
        feedback: feedbackNotes || undefined,
        was_helpful: rating >= 4,
      });
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error("Failed to submit feedback:", err);
    }
  };

  const handleReset = () => {
    setConversationId(null);
    setMessages([]);
    setFeedbackSubmitted(false);
    setFeedbackRating(null);
    setHandoffRequested(false);
    initConversation();
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none">
      {/* Closed State Floating Launcher Button */}
      {!isOpen && (
        <button
          onClick={handleOpenWidget}
          id="customer-chat-launcher"
          className="group flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 text-white rounded-full shadow-2xl hover:shadow-blue-500/40 hover:scale-105 transition-all duration-300 border border-blue-400/30"
        >
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center font-bold text-sm">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 border-2 border-indigo-700 rounded-full animate-pulse"></span>
          </div>
          <div className="text-left pr-1">
            <div className="text-xs font-semibold tracking-tight">Chat with Aria</div>
            <div className="text-[10px] text-blue-100 font-normal">UrbanThread AI Employee</div>
          </div>
          <Sparkles className="w-4 h-4 text-blue-200 group-hover:rotate-12 transition-transform" />
        </button>
      )}

      {/* Opened State Chat Window */}
      {isOpen && (
        <div className="w-[410px] h-[640px] max-h-[90vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-4 flex flex-col gap-2 relative">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/30">
                    <Bot className="w-6 h-6" />
                  </div>
                  <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-slate-900 rounded-full"></span>
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm">Aria</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-blue-500/20 text-blue-300 border border-blue-400/30 font-medium">
                      AI Employee
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-300 flex items-center gap-1">
                    <span>UrbanThread Shopper Support</span>
                    <span className="text-emerald-400">• Online</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={handleHandoff}
                  disabled={handoffRequested || loading}
                  title="Speak to Human Agent"
                  className="p-1.5 text-slate-300 hover:text-amber-300 hover:bg-slate-800/80 rounded-lg transition-colors"
                >
                  <Headphones className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Persona switcher bar for testing & verification */}
            <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[11px]">
              <div className="flex items-center gap-1.5 text-slate-300">
                {isGuest ? (
                  <span className="flex items-center gap-1 text-amber-300">
                    <Lock className="w-3 h-3" /> Guest Mode (Public Info)
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-emerald-300">
                    <UserCheck className="w-3 h-3" /> Auth Customer: Priya (#cust-001)
                  </span>
                )}
              </div>
              <button
                onClick={() => {
                  setIsGuest(!isGuest);
                  handleReset();
                }}
                className="text-[10px] text-blue-300 hover:text-blue-100 underline decoration-blue-400/60"
              >
                {isGuest ? "Switch to Auth" : "Switch to Guest"}
              </button>
            </div>

            {/* Active Booked Order Context Banner */}
            {activeOrder && (
              <div className="bg-blue-950/80 border-t border-blue-800/50 px-3 py-1.5 flex items-center justify-between text-[10px] text-blue-200">
                <span className="truncate">
                  📦 <strong>#{activeOrder.orderNumber}</strong>: {activeOrder.productName} ({activeOrder.size})
                </span>
                <span className="text-emerald-300 font-bold shrink-0 ml-2">Booked</span>
              </div>
            )}
          </div>

          {/* Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50">
            {messages.map((msg) => {
              const isUser = msg.sender_type === "CUSTOMER";
              const isSystem = msg.sender_type === "SYSTEM";

              if (isSystem) {
                const isActualHandoff = msg.message_type === "HUMAN_HANDOFF" || msg.metadata?.ticket_id;
                return (
                  <div key={msg.id} className={`p-3 ${isActualHandoff ? "bg-amber-50 border-amber-200 text-amber-800" : "bg-rose-50 border-rose-200 text-rose-800"} border rounded-xl text-xs flex items-start gap-2.5`}>
                    <AlertTriangle className={`w-4 h-4 ${isActualHandoff ? "text-amber-600" : "text-rose-600"} shrink-0 mt-0.5`} />
                    <div className="space-y-1">
                      <div className={`font-semibold ${isActualHandoff ? "text-amber-900" : "text-rose-900"}`}>
                        {isActualHandoff ? "Human Support Handover" : "Connection Notice"}
                      </div>
                      <div>{msg.content}</div>
                      {msg.metadata?.ticket_id && (
                        <div className="text-[10px] font-mono text-amber-700 font-medium">
                          Support Ticket: #{msg.metadata.ticket_id}
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}
                >
                  {!isUser && (
                    <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-sm">
                      A
                    </div>
                  )}

                  <div className={`max-w-[82%] space-y-2`}>
                    <div
                      className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-none shadow-md shadow-blue-500/10"
                          : "bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm"
                      }`}
                    >
                      {msg.content}
                    </div>

                    {/* Rich Cards: Order Card */}
                    {msg.metadata?.order && (
                      <div className="bg-white border border-blue-100 rounded-xl p-3 shadow-sm text-xs space-y-2">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5">
                            <Package className="w-3.5 h-3.5 text-blue-600" />
                            Order #{msg.metadata.order.order_number || msg.metadata.order.id}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                            {msg.metadata.order.status}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 space-y-1">
                          <div className="flex justify-between">
                            <span>Amount:</span>
                            <span className="font-semibold text-slate-900">₹{msg.metadata.order.total_amount}</span>
                          </div>
                          {msg.metadata.order.shipment && (
                            <div className="flex justify-between items-center text-slate-700">
                              <span className="flex items-center gap-1">
                                <Truck className="w-3 h-3 text-slate-500" />
                                {msg.metadata.order.shipment.carrier}
                              </span>
                              <span className="font-mono text-[10px]">{msg.metadata.order.shipment.tracking_number}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Rich Confirmation Card: Returns & Cancellations */}
                    {msg.metadata?.confirmation && (
                      <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-3 text-xs space-y-2.5">
                        <div className="flex items-center gap-2 text-amber-900 font-semibold">
                          <AlertTriangle className="w-4 h-4 text-amber-600" />
                          <span>Confirmation Required</span>
                        </div>
                        <p className="text-amber-800 text-[11px]">
                          This action will initiate an official request. Would you like to proceed?
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSendMessage("Yes, proceed with return")}
                            className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
                          >
                            Yes, Confirm
                          </button>
                          <button
                            onClick={() => handleSendMessage("No, cancel this request")}
                            className="flex-1 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-medium transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Grounded RAG Citations */}
                    {msg.metadata?.citations && Array.isArray(msg.metadata.citations) && msg.metadata.citations.length > 0 && (
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-[11px] space-y-1.5 shadow-xs">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider flex items-center gap-1">
                          <BookOpen className="w-3 h-3 text-blue-600" />
                          <span>Grounded Knowledge Sources</span>
                        </div>
                        <div className="space-y-1">
                          {msg.metadata.citations.map((c: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between text-[10px] bg-white px-2 py-1 rounded border border-slate-100">
                              <span className="font-medium text-slate-700 truncate max-w-[200px]" title={c.source}>
                                {c.source}
                              </span>
                              <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 font-semibold shrink-0">
                                {Math.round((c.confidence || 0.95) * 100)}% Match
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Booking Card CTA */}
                    {msg.message_type === "BOOKING_CARD" && (
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3 text-xs space-y-2">
                        <div className="font-semibold text-blue-950 flex items-center gap-1.5">
                          <Sparkles className="w-4 h-4 text-blue-600" />
                          <span>UrbanThread Booking Portal</span>
                        </div>
                        <p className="text-slate-600 text-[11px]">
                          Book a try-at-home fitting or schedule a personalized styling session.
                        </p>
                        <a
                          href={msg.metadata?.link || "/store?tab=fitting"}
                          className="inline-flex items-center justify-center w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
                        >
                          {msg.metadata?.cta || "Open Booking Portal"}
                        </a>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 text-xs font-bold">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex gap-2.5 items-center text-slate-500 text-xs">
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 text-xs font-bold">
                  A
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-3.5 py-2.5 flex items-center gap-1.5 shadow-sm">
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  <span className="text-[11px] text-slate-400 ml-1">Aria is thinking...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Action Pills */}
          <div className="px-4 py-2 bg-slate-100/80 border-t border-slate-200/60 overflow-x-auto flex gap-1.5 no-scrollbar">
            {suggestedActions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(action)}
                disabled={loading}
                className="px-2.5 py-1 bg-white hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 border border-slate-200 rounded-full text-[11px] font-medium text-slate-700 whitespace-nowrap transition-all shrink-0 shadow-xs"
              >
                {action}
              </button>
            ))}
          </div>

          {/* Feedback Star Rating Section */}
          <div className="px-4 py-2 bg-white border-t border-slate-200/80 flex items-center justify-between text-xs">
            <span className="text-[11px] text-slate-500">Rate this response:</span>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleFeedbackSubmit(star)}
                  className={`p-0.5 transition-transform hover:scale-125 ${
                    feedbackRating && feedbackRating >= star
                      ? "text-amber-400 fill-amber-400"
                      : "text-slate-300 hover:text-amber-400"
                  }`}
                >
                  <Star className="w-3.5 h-3.5 fill-current" />
                </button>
              ))}
              {feedbackSubmitted && (
                <span className="text-[10px] text-emerald-600 font-semibold ml-1">Saved!</span>
              )}
            </div>
          </div>

          {/* Input Footer */}
          <div className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
            <input
              type="text"
              id="customer-chat-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Ask about orders, returns, sizing..."
              disabled={loading}
              className="flex-1 bg-slate-100 hover:bg-slate-50 focus:bg-white border border-slate-200 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none transition-all"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || loading}
              className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl shadow-sm transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
