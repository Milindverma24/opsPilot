"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  UploadCloud, 
  ArrowLeft, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  FileSpreadsheet,
  Clock
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function ImportDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.imports.get(id)
        .then((res) => setJob(res.data))
        .catch((err) => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <AppLayout>
        <div className="py-16 text-center text-xs text-slate-400">Loading import job details...</div>
      </AppLayout>
    );
  }

  if (!job) {
    return (
      <AppLayout>
        <div className="py-16 text-center">
          <p className="text-xs text-rose-600 font-semibold">Import job not found</p>
          <Link href="/imports" className="text-xs text-blue-600 underline mt-2 block">
            Return to Imports List
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
            href="/imports"
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Imports</span>
          </Link>
        </div>

        {/* Job Header Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <FileSpreadsheet className="w-5 h-5 text-blue-600" />
                <h1 className="text-base font-bold text-slate-900">{job.filename}</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 uppercase">
                  {job.entity_type}
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                  job.status === "COMPLETED"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : job.status === "PARTIALLY_COMPLETED"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-rose-50 text-rose-700 border-rose-200"
                }`}>
                  {job.status}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                Job ID: {job.id} • Format: {job.source_type}
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs text-slate-600 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Rows</span>
                <span className="font-bold text-slate-800 text-sm">{job.total_records}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Success</span>
                <span className="font-bold text-emerald-600 text-sm">{job.successful_records}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Failed</span>
                <span className="font-bold text-rose-600 text-sm">{job.failed_records}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Report Section */}
        {job.error_report?.length > 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-rose-50/50 flex items-center justify-between">
              <h3 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                Row-Level Error Report ({job.error_report.length})
              </h3>
              <span className="text-[11px] text-rose-600 font-medium">Valid records were committed successfully</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                    <th className="py-3 px-4">Row Number</th>
                    <th className="py-3 px-4">Error Cause</th>
                    <th className="py-3 px-4">Rejected Row Payload</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {job.error_report.map((err: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-800">
                        Row #{err.row || idx + 1}
                      </td>
                      <td className="py-3 px-4 text-rose-700 font-medium">
                        {err.error}
                      </td>
                      <td className="py-3 px-4">
                        <pre className="text-[10px] font-mono bg-slate-100 p-2 rounded max-w-md overflow-x-auto text-slate-700">
                          {JSON.stringify(err.data || {}, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center shadow-sm">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <div className="text-sm font-bold text-emerald-900">Zero Ingestion Errors</div>
            <p className="text-xs text-emerald-700 mt-1">All {job.total_records} records parsed, verified against schema, and persisted cleanly.</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
