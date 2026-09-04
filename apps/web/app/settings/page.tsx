"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Settings,
  Building2,
  Users,
  Shield,
  Cpu,
  Save,
  CheckCircle2,
} from "lucide-react";

export default function SettingsPage() {
  const [autonomyLevel, setAutonomyLevel] = useState("LEVEL_2");
  const [aiProvider, setAiProvider] = useState("deterministic");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Organization & AI Configuration"
          subtitle="Multi-tenancy boundaries, role-based access, and model provider settings"
        />

        <main className="p-6 space-y-6 max-w-4xl mx-auto w-full">
          {saved && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Settings updated successfully!</span>
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-6">
            {/* Organization Identity */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Building2 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Organization Tenant Profile</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Organization Name</label>
                  <input
                    type="text"
                    disabled
                    value="Acme Industries"
                    className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 font-medium cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Organization Slug</label>
                  <input
                    type="text"
                    disabled
                    value="acme-test"
                    className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 font-mono text-[11px] cursor-not-allowed"
                  />
                </div>
              </div>
            </div>

            {/* AI Fleet Configuration */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Cpu className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-bold text-slate-900">AI Model & Autonomy Level</h3>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">AI Provider Engine</label>
                  <select
                    value={aiProvider}
                    onChange={(e) => setAiProvider(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  >
                    <option value="deterministic">Deterministic Operations Provider (100% Reliable Offline & Fast)</option>
                    <option value="openai">OpenAI GPT-4o Production Gateway (Requires OPENAI_API_KEY)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Autonomy Guardrail Tier</label>
                  <select
                    value={autonomyLevel}
                    onChange={(e) => setAutonomyLevel(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  >
                    <option value="LEVEL_1">Level 1: Assistive (Every action requires human approval)</option>
                    <option value="LEVEL_2">Level 2: Controlled Autonomy (Invoices &lt; ₹50k auto-processed; High value requires approval)</option>
                    <option value="LEVEL_3">Level 3: Full Autonomy (Strict policy engine enforcement without manual checkpoints)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Active User Directory */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Users className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900">Seeded Role-Based Access Directory</h3>
              </div>

              <div className="space-y-2 text-xs">
                {[
                  { name: "Finance Manager", email: "finance@acme.test", role: "FINANCE_MANAGER" },
                  { name: "Super Administrator", email: "admin@acme.test", role: "SUPER_ADMIN" },
                  { name: "Operations Lead", email: "operations@acme.test", role: "OPERATIONS_MANAGER" },
                  { name: "Support Manager", email: "support@acme.test", role: "SUPPORT_MANAGER" },
                  { name: "Compliance Auditor", email: "auditor@acme.test", role: "AUDITOR" },
                ].map((u) => (
                  <div key={u.email} className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-100 rounded-lg">
                    <div>
                      <span className="font-bold text-slate-800">{u.name}</span>
                      <span className="text-[11px] text-slate-400 font-mono ml-2">({u.email})</span>
                    </div>
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-blue-50 text-blue-700 font-bold">
                      {u.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-sm transition-colors flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              <span>Save System Settings</span>
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}
