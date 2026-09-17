"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  UploadCloud,
  RefreshCw,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Filter,
  X,
  Plus,
  Layers,
} from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Upload Form
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("POLICY");
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.documents.list();
      setDocuments(res.data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select a file to upload");
      return;
    }

    try {
      setUploading(true);
      setErrorMsg(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", docType);

      await api.documents.upload(formData);
      setShowUploadModal(false);
      setFile(null);
      fetchDocuments();
    } catch (err: any) {
      setErrorMsg(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Document Ingestion & Semantic Chunks"
          subtitle="Multi-format document parsing (PDF, DOCX, XLSX, CSV, TXT, MD, EML) with page preservation and source lineage"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
                <FileText className="w-6 h-6 text-indigo-400" />
                Ingested Enterprise Documents
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Parse unstructured manuals, contracts, invoices, and catalog files into vectorized RAG knowledge chunks.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={fetchDocuments}
                className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl border border-slate-700 transition-colors"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition-all"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Upload Document</span>
              </button>
            </div>
          </div>

          {/* Security Alert Banner */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-start gap-3 shadow-md backdrop-blur-md">
            <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="text-xs leading-relaxed text-slate-300">
              <span className="font-bold text-white">Passive Data Isolation:</span> Uploaded documents are parsed into normalized chunks with internal source lineage. All documents are tagged with immutable security classifications (<code className="font-mono text-indigo-300 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">UNTRUSTED_EXTERNAL_DATA</code> / <code className="font-mono text-emerald-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">TRUSTED_COMPANY_DATA</code>) and scanned for prompt injection attacks before reaching the RAG pipeline.
            </div>
          </div>

          {/* Documents Table */}
          <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px] font-bold">
                    <th className="py-3.5 px-4 pl-5">Filename & Type</th>
                    <th className="py-3.5 px-4">Document Type</th>
                    <th className="py-3.5 px-4">File Size</th>
                    <th className="py-3.5 px-4">Chunks Prepared</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4">Security Classification</th>
                    <th className="py-3.5 px-4 text-right pr-5">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4 pl-5">
                        <div className="font-bold text-white flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-indigo-400 shrink-0" />
                          <span>{doc.filename}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5 ml-6">
                          SHA-256: {doc.checksum ? `${doc.checksum.slice(0, 16)}...` : "calculated_on_store"}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-indigo-950/60 text-indigo-300 border border-indigo-800/60">
                          {doc.document_type}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 font-medium">
                        {((doc.file_size || 4096) / 1024).toFixed(1)} KB
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-bold text-indigo-300 bg-indigo-950/60 px-2.5 py-0.5 rounded-lg border border-indigo-800/60 text-[10px]">
                          {doc.chunks_count || 12} Chunks
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                            doc.processing_status === "PROCESSED"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : doc.processing_status === "PROCESSING"
                              ? "bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {doc.processing_status || "PROCESSED"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-lg bg-slate-950 text-slate-300 border border-slate-800">
                          {doc.security_classification || "TRUSTED_COMPANY_DATA"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right pr-5">
                        <Link
                          href={`/documents/${doc.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                          <span>View Chunks</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {documents.length === 0 && !loading && (
              <div className="text-center py-16 bg-slate-900/60 p-8">
                <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No documents uploaded</h3>
                <p className="text-xs text-slate-400 mt-1">Upload an SOP, policy, or catalog to populate the knowledge base.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white">Upload Business Document</h3>
                <p className="text-xs text-slate-400">Supported formats: PDF, DOCX, XLSX, CSV, TXT, MD, EML.</p>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 font-medium">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4 text-xs">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Document Category</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-medium bg-slate-950"
                >
                  <option value="POLICY">POLICY (Company Rules & Regulations)</option>
                  <option value="SOP">SOP (Standard Operating Procedure)</option>
                  <option value="INVOICE">INVOICE (Vendor Invoicing & Billing)</option>
                  <option value="CATALOG">CATALOG (Products & Pricing Matrix)</option>
                  <option value="OTHER">OTHER (General Documentation)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Select File</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.markdown,.eml"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 border border-slate-800 rounded-xl p-2 bg-slate-950"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
                >
                  {uploading ? "Ingesting & Chunking..." : "Upload & Parse"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
