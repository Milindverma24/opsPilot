"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  UploadCloud, 
  RefreshCw, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock,
  ArrowRight
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function ImportsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Form State
  const [file, setFile] = useState<File | null>(null);
  const [entityType, setEntityType] = useState("customers");
  const [sourceType, setSourceType] = useState("CSV");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await api.imports.list();
      setJobs(res.data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select a file to import");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("entity_type", entityType);
      formData.append("source_type", sourceType);

      await api.imports.create(formData);
      setShowUploadModal(false);
      setFile(null);
      fetchJobs();
    } catch (err: any) {
      setErrorMsg(err.message || "Import initiation failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
              <UploadCloud className="w-6 h-6 text-blue-600" />
              Business Data Batch Imports
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Bulk CSV and JSON ingestion for customers, products, inventory, orders, and vendors with tenant validation.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchJobs}
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
              <span>Initiate Batch Import</span>
            </button>
          </div>
        </div>

        {/* Jobs Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                  <th className="py-3 px-4">Filename & Source</th>
                  <th className="py-3 px-4">Entity Target</th>
                  <th className="py-3 px-4">Total Records</th>
                  <th className="py-3 px-4">Successful</th>
                  <th className="py-3 px-4">Failed</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Completed At</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900 flex items-center gap-2">
                        <FileSpreadsheet className="w-4 h-4 text-blue-600 shrink-0" />
                        <span>{j.filename}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 ml-6">Format: {j.source_type}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded text-[10px] uppercase">
                        {j.entity_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900">{j.total_records}</td>
                    <td className="py-3 px-4 text-emerald-600 font-bold">{j.successful_records}</td>
                    <td className="py-3 px-4 text-rose-600 font-bold">{j.failed_records}</td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        j.status === "COMPLETED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : j.status === "PARTIALLY_COMPLETED"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : j.status === "PROCESSING"
                          ? "bg-blue-50 text-blue-700 border-blue-200 animate-pulse"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}>
                        {j.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      {j.completed_at ? new Date(j.completed_at).toLocaleString() : "Processing"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/imports/${j.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        <span>Inspect</span>
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
              <h3 className="text-base font-bold text-slate-900 mb-1">Initiate Batch Data Import</h3>
              <p className="text-xs text-slate-500 mb-4">Upload CSV or JSON file containing synthetic business records.</p>

              {errorMsg && (
                <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 font-medium">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Target Entity Type</label>
                  <select
                    value={entityType}
                    onChange={(e) => setEntityType(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium bg-white"
                  >
                    <option value="customers">Customers (name, email, phone, status)</option>
                    <option value="products">Products (sku, name, base_price, sale_price, brand)</option>
                    <option value="vendors">Vendors (name, code, email, phone, status)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Source File Format</label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium bg-white"
                  >
                    <option value="CSV">Comma Separated Values (CSV)</option>
                    <option value="JSON">JavaScript Object Notation (JSON)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Select File</label>
                  <input
                    type="file"
                    required
                    accept=".csv,.json"
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
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-sm transition-colors disabled:opacity-50"
                  >
                    {submitting ? "Processing..." : "Start Import"}
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
