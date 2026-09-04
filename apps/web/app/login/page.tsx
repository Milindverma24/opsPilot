"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail, ArrowRight, Loader2, ShieldCheck, Building2, UserCheck } from "lucide-react";
import { api, setToken } from "@/lib/api";

const DEMO_PERSONAS = [
  { role: "UrbanThread E-Commerce Admin", email: "admin@urbanthread.local", desc: "UrbanThread Clothing Brand Operations & Catalog" },
  { role: "UrbanThread Operations Lead", email: "operations@urbanthread.local", desc: "Warehouses, Inventory, Orders & Fulfillment" },
  { role: "UrbanThread Customer Care", email: "support@urbanthread.local", desc: "Returns, Refunds, Support Cases & Messaging" },
  { role: "Acme Finance Manager", email: "finance@acme.test", desc: "Approval authority for invoices > ₹1L" },
  { role: "Acme Super Administrator", email: "admin@acme.test", desc: "Full permissions & system access" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("finance@acme.test");
  const [password, setPassword] = useState("DemoPassword123!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.auth.login(email, password);
      setToken(res.access_token);
      localStorage.setItem("opspilot_user", JSON.stringify(res.user));
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to authenticate. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPersona = (pEmail: string) => {
    setEmail(pEmail);
    setPassword("DemoPassword123!");
    // Auto submit with new credentials
    setLoading(true);
    api.auth.login(pEmail, "DemoPassword123!")
      .then((res) => {
        setToken(res.access_token);
        localStorage.setItem("opspilot_user", JSON.stringify(res.user));
        router.push("/");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-blue-600/10 blur-[120px] pointer-events-none rounded-full" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600 font-black text-white text-xl shadow-lg shadow-blue-500/30 mb-4">
          OP
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          OpsPilot
        </h1>
        <p className="mt-1 text-xs text-slate-400 font-medium">
          Your AI Employee for Business Operations
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10">
        <div className="bg-slate-900 border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 space-y-6">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs flex items-center gap-2">
              <span className="font-semibold">Error:</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Corporate Email
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-slate-500" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="block w-full pl-9 pr-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Password
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-slate-500" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="block w-full pl-9 pr-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-medium"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-lg shadow-md text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In to OpsPilot</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Personas */}
          <div className="pt-4 border-t border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
              <span>Quick Demo Sign-In</span>
              <span className="text-[9px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded font-bold">1-Click</span>
            </div>
            <div className="space-y-1.5">
              {DEMO_PERSONAS.map((p) => (
                <button
                  key={p.email}
                  type="button"
                  onClick={() => handleSelectPersona(p.email)}
                  disabled={loading}
                  className="w-full p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 text-left transition-colors flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                      {p.role}
                    </div>
                    <div className="text-[10px] text-slate-400">{p.desc}</div>
                  </div>
                  <UserCheck className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
