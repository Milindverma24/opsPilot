"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Mail, 
  RefreshCw, 
  ShieldAlert, 
  ShieldCheck, 
  Paperclip, 
  User, 
  Clock, 
  ArrowRight,
  AlertTriangle
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function EmailsPage() {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const res = await api.emails.list({ page_size: 50 });
      setEmails(res.data || []);
      if (res.data?.length > 0 && !selectedEmail) {
        setSelectedEmail(res.data[0]);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  const handleSelectEmail = async (id: string) => {
    try {
      const res = await api.emails.get(id);
      setSelectedEmail(res.data);
    } catch (err: any) {
      console.error(err);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
              <Mail className="w-6 h-6 text-blue-600" />
              Inbound Emails & Communications
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Multi-channel email ingestion stream with attachment isolation and deterministic prompt injection defense.
            </p>
          </div>
          <button
            onClick={fetchEmails}
            className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors self-start sm:self-auto"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Security Notice */}
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800 leading-relaxed">
            <span className="font-bold">Untrusted Inbound Data:</span> All inbound customer and vendor emails are classified as <code className="font-mono bg-rose-100 px-1 rounded">UNTRUSTED_USER_CONTENT</code>. Content is scanned deterministically for policy bypass and injection directives. Under no circumstance will the system execute actions or commands embedded in messages.
          </div>
        </div>

        {/* Master-Detail Email Split Pane */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[640px]">
          {/* Email List (Left Column) */}
          <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="p-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Inbound Inbox ({emails.length})
              </span>
              <span className="text-[10px] text-slate-400">Mock Connector Active</span>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
              {emails.map((e) => {
                const isSelected = selectedEmail?.id === e.id;
                const hasInjection = e.security_flags && e.security_flags.length > 0;
                return (
                  <button
                    key={e.id}
                    onClick={() => handleSelectEmail(e.id)}
                    className={`w-full text-left p-3.5 transition-colors block ${
                      isSelected ? "bg-blue-50/70 border-l-4 border-blue-600" : "hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-bold text-slate-900 truncate">{e.sender}</span>
                      <span className="text-[10px] text-slate-400 shrink-0">
                        {e.received_at ? new Date(e.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ""}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-slate-700 truncate mb-1">
                      {e.subject}
                    </div>

                    <div className="flex items-center gap-1.5 flex-wrap mt-1">
                      {hasInjection ? (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          INJECTION_ATTEMPT
                        </span>
                      ) : (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                          {e.security_classification || "UNTRUSTED"}
                        </span>
                      )}
                      {e.attachments_count > 0 && (
                        <span className="text-[9px] font-semibold text-slate-500 flex items-center gap-0.5">
                          <Paperclip className="w-2.5 h-2.5" />
                          {e.attachments_count}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Email Reader View (Right Column) */}
          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            {selectedEmail ? (
              <div className="flex-1 overflow-y-auto flex flex-col">
                {/* Subject & Metadata Header */}
                <div className="p-5 border-b border-slate-100 bg-slate-50/50">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h2 className="text-base font-bold text-slate-900">{selectedEmail.subject}</h2>
                    {selectedEmail.security_flags?.length > 0 && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500 text-white shadow-sm shrink-0">
                        PROMPT_INJECTION_FLAGGED
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-slate-600 space-y-1">
                    <div>
                      <span className="text-slate-400 font-semibold mr-1.5">From:</span>
                      <span className="font-bold text-slate-800">{selectedEmail.sender}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold mr-1.5">To:</span>
                      <span className="text-slate-700">{selectedEmail.recipient}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 pt-1">
                      <Clock className="w-3 h-3" />
                      <span>{selectedEmail.received_at ? new Date(selectedEmail.received_at).toLocaleString() : ""}</span>
                    </div>
                  </div>
                </div>

                {/* Prompt Injection Warning Callout */}
                {selectedEmail.security_flags?.length > 0 && (
                  <div className="m-5 p-3.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
                    <div className="font-bold flex items-center gap-1.5 mb-1 text-rose-900">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Deterministic Security Rule Triggered
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Risk Flags: {selectedEmail.security_flags.join(", ")}. This email contains directives attempting to override policies or manipulate system parameters. Autonomous AI action is completely blocked.
                    </p>
                  </div>
                )}

                {/* Body Content */}
                <div className="p-5 flex-1">
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                    {selectedEmail.body_text || "No text content available."}
                  </div>
                </div>

                {/* Passive Isolation Notice Footer */}
                <div className="p-3 border-t border-slate-100 bg-slate-50 text-[10px] text-slate-400 text-center font-mono">
                  &lt;untrusted_business_content source="EMAIL" trust_level="zero"&gt;
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-xs text-slate-400">
                Select an email to view thread details
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
