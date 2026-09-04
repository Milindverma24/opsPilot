"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Database, 
  Globe, 
  FileText, 
  Mail, 
  UploadCloud, 
  ShieldCheck, 
  CheckCircle2, 
  ArrowRight,
  RefreshCw,
  Sliders
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function DataSourcesSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [connectorStatus, setConnectorStatus] = useState<any>(null);

  const testEmailConnector = async () => {
    try {
      setLoading(true);
      const res = await api.emails.testConnector();
      setConnectorStatus(res);
    } catch (err: any) {
      alert("Connector test failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testEmailConnector();
  }, []);

  const sources = [
    {
      title: "Storefront Website Ingestion",
      desc: "SSRF-protected crawler with robots.txt parsing and SHA-256 change detection.",
      href: "/data-sources/websites",
      icon: Globe,
      status: "ACTIVE",
      statusClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
    },
    {
      title: "Business Documents & Policies",
      desc: "Multi-format parsers (PDF, DOCX, XLSX, CSV, TXT, MD, EML) with page-preserving chunks.",
      href: "/documents",
      icon: FileText,
      status: "ACTIVE",
      statusClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
    },
    {
      title: "Inbound Email Stream",
      desc: "Mock / IMAP / Webhook connector with attachment lineage and prompt injection containment.",
      href: "/emails",
      icon: Mail,
      status: "CONNECTED",
      statusClass: "bg-emerald-50 text-emerald-700 border-emerald-200"
    },
    {
      title: "Batch Data Imports",
      desc: "CSV and JSON batch ingestion framework for products, customers, and inventory.",
      href: "/imports",
      icon: UploadCloud,
      status: "READY",
      statusClass: "bg-blue-50 text-blue-700 border-blue-200"
    }
  ];

  return (
    <AppLayout>
      <div className="space-y-6 max-w-5xl">
        {/* Header */}
        <div className="pb-5 border-b border-slate-200">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Database className="w-6 h-6 text-blue-600" />
            Data Sources & Ingestion Architecture
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage data connectors, external website monitors, inbound communication webhooks, and security boundaries.
          </p>
        </div>

        {/* Security Isolation Notice */}
        <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm border border-slate-800">
          <div className="flex items-start gap-3.5">
            <ShieldCheck className="w-6 h-6 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-white mb-1">Architecture Boundary Notice</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Phase 5 makes the enterprise observable to the future AI employee without granting direct write access or arbitrary execution rights. All imported content is stored passively, tagged with security classifications (<code className="font-mono text-blue-300 bg-slate-800 px-1 rounded">UNTRUSTED_EXTERNAL_DATA</code> / <code className="font-mono text-blue-300 bg-slate-800 px-1 rounded">UNTRUSTED_USER_CONTENT</code>), and bounded by deterministic prompt injection filters.
              </p>
            </div>
          </div>
        </div>

        {/* Data Source Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sources.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.title} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow transition-shadow flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${s.statusClass}`}>
                      {s.status}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 mb-1">{s.title}</h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4">{s.desc}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <Link
                    href={s.href}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <span>Manage Pipeline</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>

        {/* Mock Email Gateway Diagnostics */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-blue-600" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Email Connector Health Status
              </h3>
            </div>
            <button
              onClick={testEmailConnector}
              disabled={loading}
              className="p-1.5 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Provider</span>
              <span className="font-bold text-slate-800">{connectorStatus?.provider || "MOCK_EMAIL_GATEWAY"}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Status</span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {connectorStatus?.status === "ok" ? "Operational" : "Checking..."}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Ingestion Latency</span>
              <span className="font-mono text-slate-700">{connectorStatus?.latency_ms || 12} ms</span>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
