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
  RefreshCw,
  X,
  Sliders,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";

const defaultPolicies = [
  {
    id: "pol-01",
    name: "Commercial & Refund Safety Policy",
    code: "POL_REFUND_SAFETY",
    department: "Commercial Operations",
    description: "Enforces strict financial guardrails, automated thresholds, and fraud protection for customer refunds.",
    status: "ACTIVE",
    rules: [
      {
        id: "rule-01",
        name: "Autonomous Refund Cap",
        condition_field: "total_amount",
        operator: "LESS_THAN_OR_EQUAL",
        threshold_value: "₹5,000",
        action: "AUTO_APPROVE",
        is_active: true,
      },
      {
        id: "rule-02",
        name: "High Value Refund Approval",
        condition_field: "total_amount",
        operator: "GREATER_THAN",
        threshold_value: "₹5,000",
        action: "REQUIRE_APPROVAL",
        is_active: true,
      },
      {
        id: "rule-03",
        name: "Anti-Abuse Frequency Limit",
        condition_field: "refund_count_30d",
        operator: "GREATER_THAN",
        threshold_value: "2 Claims",
        action: "BLOCK_AND_FLAG",
        is_active: true,
      },
    ],
  },
  {
    id: "pol-02",
    name: "Procurement & Purchase Orders Policy",
    code: "POL_PROCURE_LIMIT",
    department: "Finance & Inventory",
    description: "Controls inventory replenishment budgets and vendor invoice authorizations.",
    status: "ACTIVE",
    rules: [
      {
        id: "rule-04",
        name: "Vendor Pre-Authorization",
        condition_field: "po_total",
        operator: "LESS_THAN_OR_EQUAL",
        threshold_value: "₹50,000",
        action: "AUTO_APPROVE",
        is_active: true,
      },
      {
        id: "rule-05",
        name: "Multi-Sig Signoff Required",
        condition_field: "po_total",
        operator: "GREATER_THAN",
        threshold_value: "₹50,000",
        action: "REQUIRE_MULTI_SIG",
        is_active: true,
      },
    ],
  },
  {
    id: "pol-03",
    name: "Customer SLA & Escalation Governance",
    code: "POL_SLA_GOVERNANCE",
    department: "Customer Experience",
    description: "Enforces maximum response delays before triggering supervisor handoff.",
    status: "ACTIVE",
    rules: [
      {
        id: "rule-06",
        name: "SLA Tier 1 Breach Escalation",
        condition_field: "wait_time_minutes",
        operator: "GREATER_THAN",
        threshold_value: "15 Mins",
        action: "ESCALATE_TIER_1",
        is_active: true,
      },
    ],
  },
];

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const [newRuleName, setNewRuleName] = useState("");
  const [conditionField, setConditionField] = useState("total_amount");
  const [operator, setOperator] = useState("GREATER_THAN");
  const [thresholdValue, setThresholdValue] = useState("10000");
  const [action, setAction] = useState("REQUIRE_APPROVAL");
  const [savingRule, setSavingRule] = useState(false);

  const loadPolicies = () => {
    setLoading(true);
    api.policies
      .list()
      .then((res) => {
        const pList = Array.isArray(res?.policies) && res.policies.length > 0 ? res.policies : (Array.isArray(res) && res.length > 0 ? res : defaultPolicies);
        setPolicies(pList);
        if (pList.length > 0 && !selectedPolicyId) {
          setSelectedPolicyId(pList[0].id);
        }
      })
      .catch((err) => {
        console.error("Error loading policies:", err);
        setPolicies(defaultPolicies);
        if (!selectedPolicyId) setSelectedPolicyId(defaultPolicies[0].id);
      })
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

  const handleCreateRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleName.trim()) return;
    setSavingRule(true);
    setTimeout(() => {
      setPolicies((prev) =>
        prev.map((p) => {
          if (p.id === selectedPolicyId || (!selectedPolicyId && prev[0]?.id === p.id)) {
            return {
              ...p,
              rules: [
                ...(p.rules || []),
                {
                  id: `rule-${Date.now()}`,
                  name: newRuleName,
                  condition_field: conditionField,
                  operator,
                  threshold_value: thresholdValue,
                  action,
                  is_active: true,
                },
              ],
            };
          }
          return p;
        })
      );
      setSavingRule(false);
      setShowAddModal(false);
      setNewRuleName("");
    }, 500);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Policy & Guardrail Governance"
          subtitle="Strict business rules, approval thresholds, risk containment, and automated compliance gates"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header Metric Bar */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-2xl">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Active Guardrail Policies: {policies.length} Policies Enforced
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Rules are evaluated synchronously by PolicyAgent before any financial, shipping, or refund action.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadPolicies}
                disabled={loading}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/30 transition flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Add Policy Rule</span>
              </button>
            </div>
          </div>

          {/* Policies List */}
          <div className="space-y-4">
            {policies.map((p) => (
              <div key={p.id} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm">{p.name}</span>
                      <span className="px-2.5 py-0.5 rounded-md font-mono text-[10px] bg-indigo-950/60 text-indigo-300 border border-indigo-800 font-bold">
                        {p.code}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">({p.department || "Operations"})</span>
                    </div>
                    {p.description && <p className="text-xs text-slate-400 mt-1">{p.description}</p>}
                  </div>
                </div>

                {/* Rules Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-950/80 text-slate-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Rule Name</th>
                        <th className="py-2.5 px-3">Condition Field</th>
                        <th className="py-2.5 px-3">Operator</th>
                        <th className="py-2.5 px-3">Threshold</th>
                        <th className="py-2.5 px-3">Triggered Action</th>
                        <th className="py-2.5 px-3 text-center">Active</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {p.rules?.map((r: any) => (
                        <tr key={r.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-3 font-semibold text-white">{r.name}</td>
                          <td className="py-3 px-3 font-mono text-[11px] text-indigo-300">{r.condition_field}</td>
                          <td className="py-3 px-3 font-mono font-bold text-slate-200">{r.operator}</td>
                          <td className="py-3 px-3 font-mono text-[11px] text-emerald-400 font-bold">{r.threshold_value}</td>
                          <td className="py-3 px-3">
                            <span className="px-2.5 py-0.5 rounded-md bg-amber-950/60 text-amber-400 border border-amber-800 font-bold text-[10px]">
                              {r.action}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <button
                              onClick={() => handleToggleRule(r.id)}
                              className="text-indigo-400 hover:text-white transition"
                              title={r.is_active ? "Disable Rule" : "Enable Rule"}
                            >
                              {r.is_active ? (
                                <ToggleRight className="w-7 h-7 text-emerald-400 inline" />
                              ) : (
                                <ToggleLeft className="w-7 h-7 text-slate-600 inline" />
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

      {/* Add Policy Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-sm text-white">Add Compliance Policy Rule</h3>
              </div>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Target Policy</label>
                <select
                  value={selectedPolicyId}
                  onChange={(e) => setSelectedPolicyId(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:border-emerald-500 outline-none"
                >
                  {policies.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  placeholder="e.g. VIP Customer Auto-Refund Waiver"
                  className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:border-emerald-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Condition Field</label>
                  <select
                    value={conditionField}
                    onChange={(e) => setConditionField(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:border-emerald-500 outline-none"
                  >
                    <option value="total_amount">Total Amount (₹)</option>
                    <option value="discount_pct">Discount Percentage (%)</option>
                    <option value="customer_risk_score">Customer Risk Score</option>
                    <option value="item_quantity">Item Quantity</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Operator</label>
                  <select
                    value={operator}
                    onChange={(e) => setOperator(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:border-emerald-500 outline-none"
                  >
                    <option value="GREATER_THAN">&gt; Greater Than</option>
                    <option value="LESS_THAN">&lt; Less Than</option>
                    <option value="EQUALS">== Equals</option>
                    <option value="NOT_EQUALS">!= Not Equals</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Threshold Value</label>
                  <input
                    type="text"
                    required
                    value={thresholdValue}
                    onChange={(e) => setThresholdValue(e.target.value)}
                    placeholder="e.g. 50000"
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:border-emerald-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Action</label>
                  <select
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:border-emerald-500 outline-none"
                  >
                    <option value="REQUIRE_APPROVAL">Require Manager Approval</option>
                    <option value="AUTO_APPROVE">Auto-Approve</option>
                    <option value="REJECT">Hard Reject</option>
                    <option value="FLAG_FRAUD">Flag Fraud Surveillance</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRule}
                  className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/30 flex items-center gap-1.5"
                >
                  {savingRule && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Policy Rule</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
