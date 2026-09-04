"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  FileText, 
  ArrowLeft, 
  FileCode, 
  Layers, 
  ShieldCheck, 
  Hash, 
  Clock,
  ExternalLink
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"chunks" | "raw">("chunks");

  useEffect(() => {
    if (id) {
      api.documents.get(id)
        .then((res) => setDoc(res.data))
        .catch((err) => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <AppLayout>
        <div className="py-16 text-center text-xs text-slate-400">Loading document chunks & metadata...</div>
      </AppLayout>
    );
  }

  if (!doc) {
    return (
      <AppLayout>
        <div className="py-16 text-center">
          <p className="text-xs text-rose-600 font-semibold">Document not found</p>
          <Link href="/documents" className="text-xs text-blue-600 underline mt-2 block">
            Return to Documents List
          </Link>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="pb-4 border-b border-slate-200">
          <Link
            href="/documents"
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Documents</span>
          </Link>
        </div>

        {/* Document Header Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <FileCode className="w-5 h-5 text-blue-600" />
                <h1 className="text-base font-bold text-slate-900">{doc.filename}</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  {doc.document_type}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {doc.processing_status}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono flex items-center gap-2">
                <span>Checksum: {doc.checksum}</span>
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs text-slate-600 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Source Lineage</span>
                <span className="font-mono text-slate-800 font-semibold">{doc.source_type}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Chunks</span>
                <span className="font-bold text-slate-800 text-sm">{doc.chunks?.length || 0}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Security Level</span>
                <span className="text-slate-700 font-bold">{doc.security_classification}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab("chunks")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              activeTab === "chunks"
                ? "bg-blue-600 text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Normalized Chunks ({doc.chunks?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab("raw")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              activeTab === "raw"
                ? "bg-blue-600 text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Extracted Full Text
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "chunks" ? (
          <div className="space-y-3">
            {doc.chunks?.map((chunk: any) => (
              <div key={chunk.chunk_index} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                <div className="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-100 text-[11px] text-slate-500 font-medium">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded text-[10px]">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    {chunk.page_number && (
                      <span className="text-slate-400">Page {chunk.page_number}</span>
                    )}
                  </div>
                  <div className="font-mono text-[10px] text-slate-400">
                    Source: {chunk.metadata?.source_uri || doc.filename}
                  </div>
                </div>

                <div className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed font-sans">
                  {chunk.content}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">Complete Extracted Text</h3>
            <pre className="text-xs text-slate-800 whitespace-pre-wrap font-mono leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-100 max-h-[600px] overflow-y-auto">
              {doc.raw_text || "No raw text available"}
            </pre>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
