"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  ShieldCheck,
  Plus,
  ToggleLeft,
  ToggleRight,
  Trash2,
  AlertTriangle,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { api } from "@/lib/api";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPolicies = () => {
    setLoading(true);
    api.policies
      .list()
      .then((res) => setPolicies(res.policies || []))
      .catch((err) => console.error("Error loading policies:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleToggleRule = async (ruleId: string) => {
    try {
      await api.policies.toggleRule(ruleId);
      loadPolicies();
    } catch (err: any) {
      alert("Error toggling rule: " + err.message);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Policy & Compliance Governance"
          subtitle="Strict business rules, approval thresholds, and automated guardrails"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Metric */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Active Guardrail Policies: {policies.length} Corporate Policies Enforced
                </h3>
                <p className="text-xs text-slate-500">
                  Rules are evaluated synchronously by PolicyAgent before any financial or refund action.
                </p>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
              100% Policy Enforced
            </span>
          </div>

          {/* Policies List */}
          <div className="space-y-4">
            {policies.map((p) => (
              <div key={p.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm">{p.name}</span>
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-blue-50 text-blue-700 font-bold">
                        {p.code}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">({p.department})</span>
                    </div>
                    {p.description && <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>}
                  </div>
                </div>

                {/* Rules Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider">
                      <tr>
                        <th className="py-2 px-3">Rule Name</th>
                        <th className="py-2 px-3">Condition Field</th>
                        <th className="py-2 px-3">Operator</th>
                        <th className="py-2 px-3">Threshold</th>
                        <th className="py-2 px-3">Triggered Action</th>
                        <th className="py-2 px-3 text-center">Active</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {p.rules?.map((r: any) => (
                        <tr key={r.id} className="hover:bg-slate-50/60">
                          <td className="py-2 px-3 font-semibold text-slate-900">{r.name}</td>
                          <td className="py-2 px-3 font-mono text-[11px] text-slate-600">{r.condition_field}</td>
                          <td className="py-2 px-3 font-mono font-bold text-slate-700">{r.operator}</td>
                          <td className="py-2 px-3 font-mono text-[11px] text-blue-600 font-bold">{r.threshold_value}</td>
                          <td className="py-2 px-3">
                            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 font-bold text-[10px]">
                              {r.action}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <button
                              onClick={() => handleToggleRule(r.id)}
                              className="text-blue-600 hover:text-blue-800"
                              title={r.is_active ? "Disable Rule" : "Enable Rule"}
                            >
                              {r.is_active ? (
                                <ToggleRight className="w-6 h-6 text-emerald-600" />
                              ) : (
                                <ToggleLeft className="w-6 h-6 text-slate-400" />
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
