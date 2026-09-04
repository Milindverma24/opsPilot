"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Package,
  CheckSquare,
  AlertTriangle,
  Play,
  RotateCcw,
  ShieldCheck,
  Barcode,
  Truck,
  User,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";

export default function EmployeeTaskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [step1Done, setStep1Done] = useState(false);
  const [step2Done, setStep2Done] = useState(false);
  const [step3Done, setStep3Done] = useState(false);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchTask = async () => {
    setLoading(true);
    try {
      const res = await api.tasks.get(id);
      setTask(res);
      if (res.status === "COMPLETED") {
        setStep1Done(true);
        setStep2Done(true);
        setStep3Done(true);
      }
    } catch (err: any) {
      setError(err.message || "Task not found");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTask();
  }, [id]);

  const handleClaim = async () => {
    setSubmitting(true);
    try {
      await api.tasks.claim(id);
      await fetchTask();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      await api.tasks.complete(id, notes || "Fulfillment completed according to manifest", {
        step1_verified: step1Done,
        step2_packed: step2Done,
        step3_labeled: step3Done,
        verified_at: new Date().toISOString(),
      });
      await fetchTask();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Topbar title="Task Details" subtitle="Loading..." />
          <div className="p-12 text-center text-slate-500">Loading task instructions...</div>
        </div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="flex h-screen overflow-hidden bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Topbar title="Task Details" subtitle="Not Found" />
          <div className="p-12 text-center space-y-4">
            <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">Task Not Found</h2>
            <Link
              href="/employee/tasks"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Return to Queue
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const items = task.payload?.items || task.payload?.order?.items || [];
  const allStepsComplete = step1Done && step2Done && step3Done;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title={`Task #${task.id.slice(0, 8)}`}
          subtitle={`${task.task_type.replace("_", " ")} — ${task.title}`}
        />

        <main className="p-6 space-y-6 max-w-5xl mx-auto w-full">
          <div className="flex items-center justify-between">
            <Link
              href="/employee/tasks"
              className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Task Dispatcher
            </Link>

            <span
              className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ${
                task.status === "COMPLETED"
                  ? "bg-emerald-100 text-emerald-800"
                  : task.status === "CLAIMED"
                  ? "bg-indigo-100 text-indigo-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {task.status.replace("_", " ")}
            </span>
          </div>

          {/* Task Header Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                  {task.task_type}
                </span>
                <h1 className="text-xl font-extrabold text-slate-900 mt-1">{task.title}</h1>
                <p className="text-sm text-slate-600 mt-1">{task.description}</p>
              </div>

              <div className="text-right">
                <span className="text-xs font-bold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
                  Priority: {task.priority}
                </span>
                <div className="text-[11px] text-slate-400 mt-2">
                  Created {new Date(task.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            {task.status === "CREATED" && (
              <div className="pt-4 border-t border-slate-100 flex justify-end">
                <button
                  onClick={handleClaim}
                  disabled={submitting}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Claim This Task Now
                </button>
              </div>
            )}
          </div>

          {/* Fulfillment Manifest Items */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-600" />
              Manifest & Items to Pick
            </h2>

            {items.length === 0 ? (
              <p className="text-xs text-slate-500">No individual line items specified in payload.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {items.map((it: any, idx: number) => (
                  <div key={idx} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900 text-sm">
                        {it.product_name || it.title || "Product Item"}
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-3 mt-0.5">
                        <span>SKU: <strong className="font-mono">{it.sku || "UT-ITEM"}</strong></span>
                        {it.size && <span>Size: <strong>{it.size}</strong></span>}
                        {it.color && <span>Color: <strong>{it.color}</strong></span>}
                      </div>
                    </div>
                    <span className="px-3 py-1 bg-slate-100 text-slate-800 text-xs font-bold rounded-lg">
                      Qty: {it.quantity || 1}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interactive Checklist */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-emerald-600" />
              Fulfillment Verification Checklist
            </h2>

            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition">
                <input
                  type="checkbox"
                  checked={step1Done}
                  disabled={task.status === "COMPLETED"}
                  onChange={(e) => setStep1Done(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="text-xs font-bold text-slate-900 block">
                    1. Retrieve Items from Shelving Unit & Verify SKU
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Confirm SKU, size, color, and undamaged physical state against the packing list.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition">
                <input
                  type="checkbox"
                  checked={step2Done}
                  disabled={task.status === "COMPLETED"}
                  onChange={(e) => setStep2Done(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="text-xs font-bold text-slate-900 block">
                    2. Pack into UrbanThread Branded Parcel
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Insert protective tissue, catalog cards, and seal securely.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition">
                <input
                  type="checkbox"
                  checked={step3Done}
                  disabled={task.status === "COMPLETED"}
                  onChange={(e) => setStep3Done(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="text-xs font-bold text-slate-900 block">
                    3. Generate & Affix Shipping Label
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Scan tracking barcode and hand off parcel to carrier outbound sorting bin.
                  </span>
                </div>
              </label>
            </div>

            {task.status !== "COMPLETED" && (
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">
                    Employee Notes / Comments
                  </label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="e.g. Bin #4A, packaged in box size M"
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleComplete}
                    disabled={!allStepsComplete || submitting}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Complete & Sign-Off Task
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
