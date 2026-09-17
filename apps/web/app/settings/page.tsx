"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  Building2,
  Users,
  Shield,
  Cpu,
  Save,
  CheckCircle2,
  Lock,
  Radio,
  Sliders,
  AlertTriangle,
  Key,
  Webhook,
  RefreshCw,
  Plus,
  Trash2,
  Send,
  Zap,
  Check,
  Eye,
  EyeOff,
} from "lucide-react";

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "Active" | "Invited" | "Suspended";
  lastActive: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"general" | "autonomy" | "guardrails" | "rbac" | "webhooks">("general");

  // Organization state
  const [orgName, setOrgName] = useState("UrbanThread Global Ops");
  const [orgSlug, setOrgSlug] = useState("urbanthread-prod");
  const [timezone, setTimezone] = useState("Asia/Kolkata (IST +05:30)");
  const [currency, setCurrency] = useState("INR (₹)");
  const [contactEmail, setContactEmail] = useState("ops-lead@urbanthread.in");

  // AI & Autonomy state
  const [autonomyLevel, setAutonomyLevel] = useState("LEVEL_2");
  const [aiProvider, setAiProvider] = useState("deterministic");
  const [confidenceThreshold, setConfidenceThreshold] = useState(92);
  const [maxRetryBudget, setMaxRetryBudget] = useState(3);
  const [reasoningTemperature, setReasoningTemperature] = useState(0.2);

  // Safety & Guardrails state
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [maxAutoRefundCap, setMaxAutoRefundCap] = useState("5000");
  const [multiSigThreshold, setMultiSigThreshold] = useState("50000");
  const [piiMaskingEnabled, setPiiMaskingEnabled] = useState(true);
  const [strictRagGrounding, setStrictRagGrounding] = useState(true);
  const [circuitBreakerTripped, setCircuitBreakerTripped] = useState(false);

  // Webhooks state
  const [webhookUrl, setWebhookUrl] = useState("https://api.urbanthread.in/v1/ops/events");
  const [webhookSecret, setWebhookSecret] = useState("whsec_908f029c488349fa81bc772e04ad1769");
  const [showSecret, setShowSecret] = useState(false);
  const [testingWebhook, setTestingWebhook] = useState(false);
  const [webhookPingStatus, setWebhookPingStatus] = useState<string | null>(null);

  // Team members
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { id: "1", name: "Vikram Malhotra", email: "vikram@urbanthread.in", role: "SUPER_ADMIN", status: "Active", lastActive: "Just now" },
    { id: "2", name: "Ananya Iyer", email: "finance@urbanthread.in", role: "FINANCE_MANAGER", status: "Active", lastActive: "14m ago" },
    { id: "3", name: "Devendra Patel", email: "operations@urbanthread.in", role: "OPERATIONS_MANAGER", status: "Active", lastActive: "2h ago" },
    { id: "4", name: "Pooja Sharma", email: "support-lead@urbanthread.in", role: "SUPPORT_MANAGER", status: "Active", lastActive: "35m ago" },
    { id: "5", name: "Enterprise Auditor (KPMG)", email: "auditor@kpmg-assurance.com", role: "AUDITOR", status: "Active", lastActive: "1d ago" },
  ]);

  // Modals & Feedback
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newMemberName, setNewMemberName] = useState("");
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [newMemberRole, setNewMemberRole] = useState("OPERATIONS_MANAGER");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleTestWebhook = () => {
    setTestingWebhook(true);
    setWebhookPingStatus(null);
    setTimeout(() => {
      setTestingWebhook(false);
      setWebhookPingStatus("SUCCESS: 200 OK (Latency: 42ms - Signature Verified)");
      setTimeout(() => setWebhookPingStatus(null), 5000);
    }, 1200);
  };

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemberName || !newMemberEmail) return;
    const member: TeamMember = {
      id: Date.now().toString(),
      name: newMemberName,
      email: newMemberEmail,
      role: newMemberRole,
      status: "Invited",
      lastActive: "Invitation Pending",
    };
    setTeamMembers([...teamMembers, member]);
    setNewMemberName("");
    setNewMemberEmail("");
    setShowInviteModal(false);
  };

  const handleRemoveMember = (id: string) => {
    setTeamMembers(teamMembers.filter(m => m.id !== id));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Organization & Autonomous Operations Settings"
          subtitle="Multi-tenancy isolation boundaries, role-based access, safety kill-switches, and model gateways"
        />

        <main className="p-6 space-y-6 max-w-6xl mx-auto w-full">
          {saved && (
            <div className="p-4 bg-emerald-950/80 border border-emerald-500/40 rounded-2xl text-emerald-300 text-xs font-semibold flex items-center justify-between shadow-lg shadow-emerald-950/50 animate-in fade-in">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Enterprise configuration committed and broadcasted to worker fleet!</span>
              </div>
              <span className="text-[11px] font-mono bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-500/30">
                REV: 0x9AF41C
              </span>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3 overflow-x-auto">
            {[
              { id: "general", label: "Organization & Multi-Tenancy", icon: Building2 },
              { id: "autonomy", label: "AI Fleet & Autonomy", icon: Cpu },
              { id: "guardrails", label: "Safety & Kill Switches", icon: Shield },
              { id: "rbac", label: "Team & Role Directory", icon: Users },
              { id: "webhooks", label: "Webhooks & Gateways", icon: Webhook },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                      : "text-slate-400 hover:text-white hover:bg-slate-900"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <form onSubmit={handleSave} className="space-y-6">
            {/* GENERAL & TENANT TAB */}
            {activeTab === "general" && (
              <div className="space-y-6 animate-in fade-in">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                        <Building2 className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Organization Tenant Profile</h3>
                        <p className="text-xs text-slate-400">Manage identity, tenant slug, and regional settings</p>
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold">
                      TENANT_ISOLATION: ENFORCED
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Organization Legal Name</label>
                      <input
                        type="text"
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Tenant Slug (Immutable Identifier)</label>
                      <input
                        type="text"
                        disabled
                        value={orgSlug}
                        className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800/80 rounded-xl text-slate-400 font-mono text-[11px] cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Primary Operations Timezone</label>
                      <select
                        value={timezone}
                        onChange={(e) => setTimezone(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-blue-500"
                      >
                        <option value="Asia/Kolkata (IST +05:30)">Asia/Kolkata (IST +05:30)</option>
                        <option value="America/New_York (EST -05:00)">America/New_York (EST -05:00)</option>
                        <option value="Europe/London (GMT +00:00)">Europe/London (GMT +00:00)</option>
                        <option value="Asia/Singapore (SGT +08:00)">Asia/Singapore (SGT +08:00)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Default Operational Currency</label>
                      <select
                        value={currency}
                        onChange={(e) => setCurrency(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-blue-500"
                      >
                        <option value="INR (₹)">Indian Rupee (INR ₹)</option>
                        <option value="USD ($)">United States Dollar (USD $)</option>
                        <option value="EUR (€)">Euro (EUR €)</option>
                        <option value="GBP (£)">British Pound (GBP £)</option>
                      </select>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block font-semibold text-slate-300 mb-1.5">Primary Incident & SLA Contact Email</label>
                      <input
                        type="email"
                        value={contactEmail}
                        onChange={(e) => setContactEmail(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">Cryptographic Multi-Tenancy Boundary</h4>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-[11px] font-mono text-slate-400 space-y-1">
                    <div>SCHEMA_HASH: <span className="text-blue-400">0xfa892019b88237e199201a4bc882e389</span></div>
                    <div>ROW_LEVEL_SECURITY: <span className="text-emerald-400 font-semibold">ACTIVE (Enforced on Postgres Tenant Table)</span></div>
                    <div>ENCRYPTION_AT_REST: <span className="text-purple-400">AES-256-GCM / KMS Hardware Key</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* AI FLEET & AUTONOMY TAB */}
            {activeTab === "autonomy" && (
              <div className="space-y-6 animate-in fade-in">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                        <Cpu className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">AI Fleet Model & Autonomy Tier</h3>
                        <p className="text-xs text-slate-400">Configure engine provider, confidence bar, and human-in-the-loop limits</p>
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-mono bg-purple-500/10 border border-purple-500/20 text-purple-400 font-semibold">
                      ENGINE: ACTIVE
                    </span>
                  </div>

                  <div className="space-y-5 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">AI Engine Provider</label>
                      <select
                        value={aiProvider}
                        onChange={(e) => setAiProvider(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-purple-500"
                      >
                        <option value="deterministic">Deterministic Operations Provider (100% Offline, Zero-Latency, Safe)</option>
                        <option value="openai">OpenAI GPT-4o Enterprise Gateway (High Reasoning, Tool Calling)</option>
                        <option value="anthropic">Anthropic Claude 3.5 Sonnet (Extended SOP Context & Policy Adherence)</option>
                        <option value="llama3">Self-Hosted vLLM Llama-3-70B Cluster (On-Prem Sovereign Cloud)</option>
                      </select>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Currently routing commercial dispatch & workflow reconciliations through selected engine.
                      </p>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Autonomy Guardrail Tier</label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {[
                          {
                            id: "LEVEL_1",
                            name: "Level 1: Assistive",
                            desc: "All critical actions require human manager approval. Zero unsupervised tool executions.",
                            badge: "Human Gated",
                          },
                          {
                            id: "LEVEL_2",
                            name: "Level 2: Controlled Autonomy",
                            desc: "Routine refunds & POs < ₹5,000 auto-processed. High value items trigger Approval queue.",
                            badge: "Recommended",
                          },
                          {
                            id: "LEVEL_3",
                            name: "Level 3: Shadow Autonomy",
                            desc: "AI executes in shadow mode. Dispatches real actions only when confidence >= 95%.",
                            badge: "Experimental",
                          },
                          {
                            id: "LEVEL_4",
                            name: "Level 4: Lights-Out Autonomous",
                            desc: "Fully autonomous operations engine. Bypasses queues unless policy breach occurs.",
                            badge: "Autonomous",
                          },
                        ].map((tier) => (
                          <div
                            key={tier.id}
                            onClick={() => setAutonomyLevel(tier.id)}
                            className={`p-4 rounded-xl border cursor-pointer transition-all ${
                              autonomyLevel === tier.id
                                ? "bg-purple-950/40 border-purple-500 shadow-md shadow-purple-900/30"
                                : "bg-slate-950 border-slate-800 hover:border-slate-700"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-white text-xs">{tier.name}</span>
                              <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${
                                autonomyLevel === tier.id ? "bg-purple-500/20 text-purple-300" : "bg-slate-800 text-slate-400"
                              }`}>
                                {tier.badge}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed">{tier.desc}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300">Confidence Threshold</span>
                          <span className="font-mono text-purple-400 font-bold">{confidenceThreshold}%</span>
                        </div>
                        <input
                          type="range"
                          min="70"
                          max="99"
                          value={confidenceThreshold}
                          onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                          className="w-full accent-purple-500"
                        />
                        <p className="text-[10px] text-slate-500">Below this score, tasks route to human review.</p>
                      </div>

                      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300">Max Auto-Retry Budget</span>
                          <span className="font-mono text-blue-400 font-bold">{maxRetryBudget} Attempts</span>
                        </div>
                        <input
                          type="range"
                          min="1"
                          max="5"
                          value={maxRetryBudget}
                          onChange={(e) => setMaxRetryBudget(Number(e.target.value))}
                          className="w-full accent-blue-500"
                        />
                        <p className="text-[10px] text-slate-500">Transient step errors retried with backoff.</p>
                      </div>

                      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300">Reasoning Temperature</span>
                          <span className="font-mono text-emerald-400 font-bold">{reasoningTemperature}</span>
                        </div>
                        <input
                          type="range"
                          min="0.0"
                          max="0.8"
                          step="0.05"
                          value={reasoningTemperature}
                          onChange={(e) => setReasoningTemperature(Number(e.target.value))}
                          className="w-full accent-emerald-500"
                        />
                        <p className="text-[10px] text-slate-500">Low temperature guarantees deterministic outputs.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SAFETY & GUARDRAILS TAB */}
            {activeTab === "guardrails" && (
              <div className="space-y-6 animate-in fade-in">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                        <Lock className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Emergency Killswitch & Operational Guardrails</h3>
                        <p className="text-xs text-slate-400">Financial limits, automatic circuit breakers, and data privacy gates</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-mono font-semibold ${
                      killSwitchActive
                        ? "bg-rose-500/20 border border-rose-500 text-rose-400 animate-pulse"
                        : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                    }`}>
                      {killSwitchActive ? "CIRCUIT BREAKER ENGAGED" : "CIRCUITS NOMINAL"}
                    </span>
                  </div>

                  {/* Killswitch banner */}
                  <div className={`p-4 rounded-xl border flex items-center justify-between ${
                    killSwitchActive
                      ? "bg-rose-950/60 border-rose-500/80 text-rose-200"
                      : "bg-slate-950 border-slate-800 text-slate-300"
                  }`}>
                    <div className="flex items-center gap-3">
                      <AlertTriangle className={`w-5 h-5 ${killSwitchActive ? "text-rose-400 animate-bounce" : "text-amber-400"}`} />
                      <div>
                        <div className="text-xs font-bold text-white">Master AI Execution Killswitch</div>
                        <div className="text-[11px] text-slate-400">
                          Instantly halt all background agent tasks, webhooks, and tool dispatches across the entire tenant.
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setKillSwitchActive(!killSwitchActive)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                        killSwitchActive
                          ? "bg-rose-600 hover:bg-rose-700 text-white shadow-lg shadow-rose-600/40"
                          : "bg-slate-800 hover:bg-rose-600 text-slate-300 hover:text-white"
                      }`}
                    >
                      {killSwitchActive ? "Disengage Killswitch" : "Trip Killswitch"}
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
                    <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                      <label className="block font-semibold text-slate-300">
                        Max Auto-Approved Refund Cap (₹ INR)
                      </label>
                      <input
                        type="number"
                        value={maxAutoRefundCap}
                        onChange={(e) => setMaxAutoRefundCap(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-rose-500"
                      />
                      <p className="text-[10px] text-slate-500">
                        Refunds exceeding this threshold automatically pause and demand Human Approver signature.
                      </p>
                    </div>

                    <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                      <label className="block font-semibold text-slate-300">
                        Mandatory Multi-Sig Threshold (₹ INR)
                      </label>
                      <input
                        type="number"
                        value={multiSigThreshold}
                        onChange={(e) => setMultiSigThreshold(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-rose-500"
                      />
                      <p className="text-[10px] text-slate-500">
                        Requires dual signature (Finance Manager + Operations Director) to execute payout.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 rounded-xl">
                      <div>
                        <div className="text-xs font-semibold text-white">PII Masking & Anonymization Engine</div>
                        <div className="text-[11px] text-slate-400">
                          Strips credit cards, phone numbers, and addresses before sending payloads to LLM endpoints.
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={piiMaskingEnabled}
                        onChange={(e) => setPiiMaskingEnabled(e.target.checked)}
                        className="w-5 h-5 accent-blue-600 rounded cursor-pointer"
                      />
                    </div>

                    <div className="flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 rounded-xl">
                      <div>
                        <div className="text-xs font-semibold text-white">Strict RAG & Policy Grounding Verification</div>
                        <div className="text-[11px] text-slate-400">
                          Rejects responses if policy citations do not have matching vector similarity &gt; 0.85 in knowledge store.
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={strictRagGrounding}
                        onChange={(e) => setStrictRagGrounding(e.target.checked)}
                        className="w-5 h-5 accent-emerald-600 rounded cursor-pointer"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* RBAC DIRECTORY TAB */}
            {activeTab === "rbac" && (
              <div className="space-y-6 animate-in fade-in">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                        <Users className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Role-Based Access Control (RBAC)</h3>
                        <p className="text-xs text-slate-400">Manage authenticated operators, reviewers, and assurance auditors</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowInviteModal(true)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors shadow-sm shadow-blue-600/20"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Invite Operator</span>
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {teamMembers.map((u) => (
                      <div
                        key={u.id}
                        className="flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-200">
                            {u.name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-white">{u.name}</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                                {u.status}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono">{u.email}</div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-blue-950 text-blue-300 border border-blue-800/80 font-bold">
                            {u.role}
                          </span>
                          <span className="text-[11px] text-slate-500 hidden sm:inline">{u.lastActive}</span>
                          {u.role !== "SUPER_ADMIN" && (
                            <button
                              type="button"
                              onClick={() => handleRemoveMember(u.id)}
                              className="p-1 text-slate-500 hover:text-rose-400 hover:bg-slate-900 rounded transition-colors"
                              title="Revoke access"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* WEBHOOKS & GATEWAYS TAB */}
            {activeTab === "webhooks" && (
              <div className="space-y-6 animate-in fade-in">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                        <Webhook className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Inbound Webhooks & Integration Gateways</h3>
                        <p className="text-xs text-slate-400">Shopify, ERP endpoints, and incident dispatch webhooks</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleTestWebhook}
                      disabled={testingWebhook}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${testingWebhook ? "animate-spin text-blue-400" : ""}`} />
                      <span>{testingWebhook ? "Testing Ping..." : "Test Webhook Ping"}</span>
                    </button>
                  </div>

                  {webhookPingStatus && (
                    <div className="p-3 bg-emerald-950/80 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs font-mono flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-400" />
                      <span>{webhookPingStatus}</span>
                    </div>
                  )}

                  <div className="space-y-4 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">Shopify / E-Commerce Webhook URL</label>
                      <input
                        type="url"
                        value={webhookUrl}
                        onChange={(e) => setWebhookUrl(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white font-mono text-xs focus:outline-none focus:border-amber-500"
                      />
                      <p className="text-[10px] text-slate-500 mt-1">Listens to orders/create, refunds/create, and inventory/update payloads.</p>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-300 mb-1.5">HMAC Cryptographic Secret Key</label>
                      <div className="relative">
                        <input
                          type={showSecret ? "text" : "password"}
                          value={webhookSecret}
                          onChange={(e) => setWebhookSecret(e.target.value)}
                          className="w-full px-3.5 py-2.5 pr-10 bg-slate-950 border border-slate-800 rounded-xl text-white font-mono text-xs focus:outline-none focus:border-amber-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowSecret(!showSecret)}
                          className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                        >
                          {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1">Used to compute and verify SHA-256 signatures on every incoming event payload.</p>
                    </div>

                    <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                      <div className="text-xs font-bold text-white">Active Event Subscriptions</div>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {[
                          "orders/created",
                          "orders/updated",
                          "refunds/requested",
                          "inventory/level_low",
                          "shipments/delayed",
                          "customer/escalation_opened",
                        ].map((evt) => (
                          <span
                            key={evt}
                            className="px-2.5 py-1 rounded-lg text-[10px] font-mono bg-slate-900 border border-slate-800 text-amber-300 font-semibold"
                          >
                            {evt}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Save Action Bar */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <div className="text-xs text-slate-500 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Active configuration synchronized with opsPilot backend daemon</span>
              </div>

              <button
                type="submit"
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-600/30 transition-all flex items-center gap-2 active:scale-95"
              >
                <Save className="w-4 h-4" />
                <span>Save All System Configurations</span>
              </button>
            </div>
          </form>
        </main>
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-400" />
                <span>Invite Operator to Organization</span>
              </h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-slate-400 hover:text-white text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddMember} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rajesh Nair"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Work Email</label>
                <input
                  type="email"
                  required
                  placeholder="rajesh@urbanthread.in"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Role & Authority</label>
                <select
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="OPERATIONS_MANAGER">OPERATIONS_MANAGER (Workflows & Events)</option>
                  <option value="FINANCE_MANAGER">FINANCE_MANAGER (Refunds & Invoices)</option>
                  <option value="SUPPORT_MANAGER">SUPPORT_MANAGER (Customer SLA & Escalations)</option>
                  <option value="AUDITOR">AUDITOR (Read-Only Ledger & Hash Verification)</option>
                  <option value="SUPER_ADMIN">SUPER_ADMIN (Full Tenant Control)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-md shadow-blue-600/30"
                >
                  Send Invitation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
