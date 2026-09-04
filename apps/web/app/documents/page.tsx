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
  Filter
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
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
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
              <FileText className="w-6 h-6 text-blue-600" />
              Document Ingestion & Chunks
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Multi-format document parsing (PDF, DOCX, XLSX, CSV, TXT, MD, EML) with page preservation, chunking, and source lineage.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchDocuments}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm transition-colors"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Security Alert Banner */}
        <div className="bg-slate-900 text-white rounded-xl p-4 flex items-start gap-3 shadow-sm">
          <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed text-slate-300">
            <span className="font-bold text-white">Passive Data Isolation:</span> Uploaded documents are parsed into normalized chunks with internal source lineage. All documents are tagged with immutable security classifications (<code className="font-mono text-blue-300 bg-slate-800 px-1 rounded">UNTRUSTED_EXTERNAL_DATA</code> / <code className="font-mono text-blue-300 bg-slate-800 px-1 rounded">TRUSTED_COMPANY_DATA</code>) and scanned for prompt injection attacks before reaching the RAG pipeline.
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                  <th className="py-3 px-4">Filename & Type</th>
                  <th className="py-3 px-4">Document Type</th>
                  <th className="py-3 px-4">File Size</th>
                  <th className="py-3 px-4">Chunks Prepared</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Security Classification</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900 flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-blue-600 shrink-0" />
                        <span>{doc.filename}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5 ml-6">
                        SHA-256: {doc.checksum?.slice(0, 16)}...
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {doc.document_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-medium">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-800 bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200 text-[10px]">
                        {doc.chunks_count || 0} Chunks
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        doc.processing_status === "PROCESSED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : doc.processing_status === "PROCESSING"
                          ? "bg-blue-50 text-blue-700 border-blue-200 animate-pulse"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}>
                        {doc.processing_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {doc.security_classification || "UNTRUSTED_EXTERNAL_DATA"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/documents/${doc.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
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
        </div>

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
              <h3 className="text-base font-bold text-slate-900 mb-1">Upload Business Document</h3>
              <p className="text-xs text-slate-500 mb-4">Supported formats: PDF, DOCX, XLSX, CSV, TXT, MD, EML.</p>

              {errorMsg && (
                <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 font-medium">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">File Document Type</label>
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium bg-white"
                  >
                    <option value="POLICY">POLICY (Company Rules & Regulations)</option>
                    <option value="SOP">SOP (Standard Operating Procedure)</option>
                    <option value="INVOICE">INVOICE (Vendor Invoicing & Billing)</option>
                    <option value="CATALOG">CATALOG (Products & Pricing Matrix)</option>
                    <option value="OTHER">OTHER (General Documentation)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Select File</label>
                  <input
                    type="file"
                    required
                    accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.markdown,.eml"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 border border-slate-300 rounded-lg p-1"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploading}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-sm transition-colors disabled:opacity-50"
                  >
                    {uploading ? "Ingesting..." : "Upload & Parse"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
